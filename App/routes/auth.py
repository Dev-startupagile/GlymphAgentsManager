from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from ..schemas import UserCreate, UserLogin, UserOut, Token, PasswordResetConfirm, PasswordResetRequest
from ..crud_user import create_user, authenticate_user, get_user_by_username, get_user_by_id, get_user_by_email, update_user_password
from ..token import create_access_token, create_refresh_token, decode_token, get_user_id_from_token, create_password_reset_token
from database.models.users import User


auth = APIRouter()

@auth.post("/register", response_model=UserOut)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Endpoint to register a new user.
    """
    try:
        user = create_user(db, user_in)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@auth.post("/login", response_model=Token)
def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Endpoint to login a user and get JWT tokens.
    """
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create access and refresh tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }

@auth.post("/refresh", response_model=Token)
def refresh_token_endpoint(refresh_token: str, db: Session = Depends(get_db)):
    """
    Endpoint to use a valid refresh token to get a new access token.
    """
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # Get the user by ID
    user = get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Create new access and refresh tokens
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token,
    }

@auth.post("/activate")
def activate_user(token: str, db: Session = Depends(get_db)):
    """
    Activate the user's account.
    The user receives `token` via email.
    """
    payload = decode_token(token)
    if not payload or payload.get("type") != "activation":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired activation token."
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token payload."
        )

    user = get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    user.is_active = True
    db.commit()
    db.refresh(user)

    return {"status": "User activated successfully. You can now log in."}

@auth.post("/request-password-reset")
def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Endpoint to request a password reset.
    Generates a password reset token and sends it to the user's email.
    """
    user = get_user_by_email(db, request.email)
    if not user:
        return {"status": "If the email exists, a password reset link has been sent."}

    # Generate password reset token
    password_reset_token = create_password_reset_token({"sub": str(user.id)})

    # In a real scenario, send this `password_reset_token` via email.
    # Example: send_password_reset_email(user.email, password_reset_token)

    # For demonstration, return the token.
    return {
        "status": "If the email exists, a password reset link has been sent.",
    }

@auth.post("/reset-password")
def reset_password(confirm: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Endpoint to reset the user's password.
    Requires a valid password reset token and the new password.
    """
    payload = decode_token(confirm.token)
    if not payload or payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token."
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token payload."
        )

    user = get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Update the user's password
    updated_user = update_user_password(db, user, confirm.new_password)

    return {"status": "Password has been reset successfully. You can now log in with your new password."}

@auth.post("/logout")
def logout_user():
    """
    Endpoint to logout a user.
    In a stateless JWT world, "logout" means the client should discard the token.
    If you need to invalidate a token, you must implement a blacklist or token store.
    """
    return {"status": "Logged out successfully"}
