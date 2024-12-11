from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from database.models.organization import Organization, OrganizationMember
from database.models.users import User

organizations = APIRouter()

@organizations.get("/organizations")
def list_organizations(current_user_id: int, db: Session = Depends(get_db)):
    organizations = (
        db.query(Organization)
        .join(OrganizationMember, Organization.id == OrganizationMember.org_id)
        .filter(OrganizationMember.user_id == current_user_id)
        .all()
    )
    return organizations


@organizations.get("/organizations/{org_id}")
def get_organization_details(org_id: int, db: Session = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization


@organizations.put("/organizations/{org_id}")
def update_organization(org_id: int, updated_data: dict, db: Session = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    for key, value in updated_data.items():
        setattr(organization, key, value)

    db.commit()
    return {"message": "Organization updated successfully"}

@organizations.post("/organizations/{org_id}/members")
def invite_user_to_organization(org_id: int, user_id: int, db: Session = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing_member = db.query(OrganizationMember).filter_by(org_id=org_id, user_id=user_id).first()
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member of the organization")

    new_member = OrganizationMember(org_id=org_id, user_id=user_id)
    db.add(new_member)
    db.commit()
    return {"message": f"User {user.username} invited to organization {organization.name}"}

@organizations.delete("/organizations/{org_id}/members/{user_id}")
def remove_user_from_organization(org_id: int, user_id: int, db: Session = Depends(get_db)):
    membership = db.query(OrganizationMember).filter_by(org_id=org_id, user_id=user_id).first()
    if not membership:
        raise HTTPException(status_code=404, detail="User is not a member of the organization")

    db.delete(membership)
    db.commit()
    return {"message": "User removed from organization successfully"}

@organizations.patch("/organizations/{org_id}/transfer-ownership")
def transfer_ownership(org_id: int, new_owner_id: int, db: Session = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    new_owner = db.query(User).filter(User.id == new_owner_id).first()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    if not new_owner:
        raise HTTPException(status_code=404, detail="New owner not found")

    organization.owner_id = new_owner_id
    db.commit()
    return {"message": f"Ownership transferred to {new_owner.username}"}
