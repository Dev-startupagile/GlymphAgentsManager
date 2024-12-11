from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models.users import User
from app.deps import admin_required
from database.models.RoleAssignment import RoleAssignment
from database.models.roles import Role
from database.models.permissions import Permission
from database.models.rolePermission import RolePermission
from database.models.userRoles import UserRole

router = APIRouter()

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}")
def update_user(user_id: int, user_data: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user_data.items():
        setattr(user, key, value)
    db.commit()
    return user

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(admin_required)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

@router.post("/users/{user_id}/roles")
def assign_role_to_user(user_id: int, role_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    role = db.query(Role).filter(Role.id == role_id).first()
    if not user or not role:
        raise HTTPException(status_code=404, detail="User or Role not found")

    # Check if the role is already assigned
    existing_assignment = db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.role_id == role_id).first()
    if existing_assignment:
        raise HTTPException(status_code=400, detail="Role already assigned to the user")

    user_role = UserRole(user_id=user_id, role_id=role_id)
    db.add(user_role)
    db.commit()
    return {"message": f"Role '{role.name}' assigned to user '{user.username}' successfully"}


@router.delete("/users/{user_id}/roles/{role_id}")
def remove_role_from_user(user_id: int, role_id: int, db: Session = Depends(get_db)):
    user_role = db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.role_id == role_id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail="Role not assigned to user")

    db.delete(user_role)
    db.commit()
    return {"message": "Role removed from user successfully"}



@router.get("/users/{user_id}/permissions")
def get_user_permissions(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    role_ids = [user_role.role_id for user_role in user_roles]

    permissions = (
        db.query(Permission)
        .join(RolePermission, Permission.id == RolePermission.permission_id)
        .filter(RolePermission.role_id.in_(role_ids))
        .all()
    )
    return {"permissions": [permission.name for permission in permissions]}

@router.post("/roles/{role_id}/permissions")
def assign_permission_to_role(role_id: int, permission_id: int, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not role or not permission:
        raise HTTPException(status_code=404, detail="Role or Permission not found")

    # Check if the permission is already assigned
    existing_assignment = db.query(RolePermission).filter(RolePermission.role_id == role_id, RolePermission.permission_id == permission_id).first()
    if existing_assignment:
        raise HTTPException(status_code=400, detail="Permission already assigned to the role")

    role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
    db.add(role_permission)
    db.commit()
    return {"message": f"Permission '{permission.name}' assigned to role '{role.name}' successfully"}

@router.get("/roles")
def get_all_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    return roles

@router.get("/permissions")
def get_all_permissions(db: Session = Depends(get_db)):
    permissions = db.query(Permission).all()
    return permissions



