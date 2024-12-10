from sqlalchemy.orm import Session
from database.models.revokedtoken import RevokedToken

def add_token_to_blacklist(db: Session, jti: str):
    revoked = RevokedToken(jti=jti)
    db.add(revoked)
    db.commit()
    db.refresh(revoked)
    return revoked

def is_token_revoked(db: Session, jti: str) -> bool:
    token = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
    return token is not None
