# routes/family.py - Family/Household Sharing
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId
import secrets
import bcrypt

from database import get_database
from routes.auth import get_current_user
from models import (
    FamilyCreate, FamilyUpdate, FamilyResponse, FamilyMember,
    FamilyInvitationCreate, FamilyInvitationResponse, AcceptInvitationRequest
)
from services.notification_service import send_email

router = APIRouter()


def _family_doc_to_response(family_doc: dict, members: List[dict]) -> FamilyResponse:
    """Convert family document to response model"""
    family_members = []
    for member in members:
        family_members.append(FamilyMember(
            user_id=str(member["user_id"]),
            email=member["email"],
            name=member["name"],
            role=member["role"],
            joined_at=member["joined_at"],
            can_manage_devices=member.get("can_manage_devices", True),
            can_resolve_alerts=member.get("can_resolve_alerts", True),
            can_invite_members=member.get("can_invite_members", False)
        ))
    
    return FamilyResponse(
        id=str(family_doc["_id"]),
        name=family_doc["name"],
        description=family_doc.get("description"),
        owner_id=str(family_doc["owner_id"]),
        owner_name=family_doc["owner_name"],
        owner_email=family_doc["owner_email"],
        members=family_members,
        total_devices=family_doc.get("device_count", 0),
        created_at=family_doc["created_at"],
        updated_at=family_doc["updated_at"]
    )


@router.post("/", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
async def create_family(
    family_data: FamilyCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new family/household"""
    db = await get_database()
    user_id = current_user["_id"]
    
    # Check if user already owns a family
    existing = await db.families.find_one({"owner_id": user_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already own a family. You can only own one family."
        )
    
    # Create family
    family_doc = {
        "name": family_data.name,
        "description": family_data.description,
        "owner_id": user_id,
        "owner_name": current_user["name"],
        "owner_email": current_user["email"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.families.insert_one(family_doc)
    family_id = result.inserted_id
    
    # Add owner as admin member
    member_doc = {
        "family_id": family_id,
        "user_id": user_id,
        "email": current_user["email"],
        "name": current_user["name"],
        "role": "admin",
        "can_manage_devices": True,
        "can_resolve_alerts": True,
        "can_invite_members": True,
        "joined_at": datetime.utcnow()
    }
    
    await db.family_members.insert_one(member_doc)
    
    # Get updated family with members
    family_doc["_id"] = family_id
    members = await db.family_members.find({"family_id": family_id}).to_list(100)
    
    return _family_doc_to_response(family_doc, members)


@router.get("/my-family", response_model=FamilyResponse)
async def get_my_family(current_user: dict = Depends(get_current_user)):
    """Get the family I'm part of"""
    db = await get_database()
    user_id = current_user["_id"]
    
    # Find family membership
    membership = await db.family_members.find_one({"user_id": user_id})
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not part of any family. Create or join one!"
        )
    
    # Get family details
    family_id = membership["family_id"]
    family_doc = await db.families.find_one({"_id": family_id})
    if not family_doc:
        # Family document missing but membership exists - repair by recreating family
        # Get owner info from membership
        owner_member = await db.family_members.find_one({"family_id": family_id, "role": "admin"})
        if not owner_member:
            owner_member = await db.family_members.find_one({"family_id": family_id})
        
        if owner_member:
            owner_user = await db.users.find_one({"_id": owner_member["user_id"]})
            if owner_user:
                # Recreate family document
                family_doc = {
                    "_id": family_id,  # Use existing family_id
                    "name": "My Family",  # Default name
                    "description": "Family recreated automatically",
                    "owner_id": owner_member["user_id"],
                    "owner_name": owner_user.get("name", "Unknown"),
                    "owner_email": owner_user.get("email", ""),
                    "created_at": owner_member.get("joined_at", datetime.utcnow()),
                    "updated_at": datetime.utcnow()
                }
                await db.families.insert_one(family_doc)
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Family not found - owner account missing"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family not found - no members found"
            )
    
    # Get all members
    members = await db.family_members.find({"family_id": family_id}).to_list(100)
    
    # Get device count (exclude soft-deleted)
    device_count = await db.devices.count_documents({
        "family_id": family_id,
        "isDeleted": {"$ne": True}
    })
    family_doc["device_count"] = device_count
    
    return _family_doc_to_response(family_doc, members)


@router.put("/my-family", response_model=FamilyResponse)
async def update_family(
    family_update: FamilyUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update family details (admin only)"""
    db = await get_database()
    user_id = current_user["_id"]
    
    # Check if user is admin of a family
    membership = await db.family_members.find_one({"user_id": user_id})
    if not membership or membership["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only family admins can update family details"
        )
    
    family_id = membership["family_id"]
    
    # Update family
    update_data = {k: v for k, v in family_update.dict().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await db.families.update_one(
            {"_id": family_id},
            {"$set": update_data}
        )
    
    # Return updated family
    family_doc = await db.families.find_one({"_id": family_id})
    members = await db.family_members.find({"family_id": family_id}).to_list(100)
    device_count = await db.devices.count_documents({
        "family_id": family_id,
        "isDeleted": {"$ne": True}
    })
    family_doc["device_count"] = device_count

    return _family_doc_to_response(family_doc, members)


@router.post("/invite", response_model=FamilyInvitationResponse, status_code=status.HTTP_201_CREATED)
async def invite_family_member(
    invitation_data: FamilyInvitationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Invite someone to join your family"""
    db = await get_database()
    user_id = current_user["_id"]
    
    # Check if user can invite (admin or has permission)
    membership = await db.family_members.find_one({"user_id": user_id})
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not part of any family"
        )
    
    if membership["role"] != "admin" and not membership.get("can_invite_members"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to invite members"
        )
    
    family_id = membership["family_id"]
    
    # Get family details
    family_doc = await db.families.find_one({"_id": family_id})
    if not family_doc:
        # Family document missing but membership exists - repair by recreating family
        # Get owner info from membership
        owner_member = await db.family_members.find_one({"family_id": family_id, "role": "admin"})
        if not owner_member:
            owner_member = await db.family_members.find_one({"family_id": family_id})
        
        if owner_member:
            owner_user = await db.users.find_one({"_id": owner_member["user_id"]})
            if owner_user:
                # Recreate family document
                family_doc = {
                    "name": "My Family",  # Default name
                    "description": "Family recreated automatically",
                    "owner_id": owner_member["user_id"],
                    "owner_name": owner_user.get("name", "Unknown"),
                    "owner_email": owner_user.get("email", ""),
                    "created_at": owner_member.get("joined_at", datetime.utcnow()),
                    "updated_at": datetime.utcnow()
                }
                await db.families.insert_one(family_doc)
                family_doc["_id"] = family_id
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Family not found - owner account missing"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family not found - no members found"
            )
    
    # Check if email is already a member
    existing_member = await db.family_members.find_one({
        "family_id": family_id,
        "email": invitation_data.email
    })
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This person is already a family member"
        )
    
    # Check for pending invitation
    pending = await db.family_invitations.find_one({
        "family_id": family_id,
        "invitee_email": invitation_data.email,
        "status": "pending",
        "expires_at": {"$gt": datetime.utcnow()}
    })
    if pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An invitation is already pending for this email"
        )
    
    # Create invitation token
    token = secrets.token_urlsafe(32)
    
    # Create invitation
    invitation_doc = {
        "family_id": family_id,
        "family_name": family_doc["name"],
        "invited_by_id": user_id,
        "invited_by_name": current_user["name"],
        "invited_by_email": current_user["email"],
        "invitee_email": invitation_data.email,
        "invitee_name": invitation_data.name,
        "role": invitation_data.role,
        "can_manage_devices": invitation_data.can_manage_devices,
        "can_resolve_alerts": invitation_data.can_resolve_alerts,
        "can_invite_members": invitation_data.can_invite_members,
        "token": token,
        "status": "pending",
        "expires_at": datetime.utcnow() + timedelta(days=7),  # 7 days to accept
        "created_at": datetime.utcnow()
    }
    
    result = await db.family_invitations.insert_one(invitation_doc)
    invitation_doc["_id"] = result.inserted_id
    
    # Send invitation email
    invitation_url = f"http://localhost:8000/family/accept-invitation?token={token}"
    
    try:
        await send_email(
            to_email=invitation_data.email,
            subject=f"You're invited to join {family_doc['name']}!",
            body=f"""
            <h2>Family Invitation</h2>
            <p>Hi {invitation_data.name}!</p>
            <p><strong>{current_user['name']}</strong> has invited you to join their family on Alert-Pro:</p>
            <h3>{family_doc['name']}</h3>
            <p>{family_doc.get('description', '')}</p>
            <p><strong>Your role:</strong> {invitation_data.role.title()}</p>
            <p><strong>Permissions:</strong></p>
            <ul>
                <li>View all family devices: ✅</li>
                <li>Receive alert notifications: ✅</li>
                <li>Manage devices: {'✅' if invitation_data.can_manage_devices else '❌'}</li>
                <li>Resolve alerts: {'✅' if invitation_data.can_resolve_alerts else '❌'}</li>
                <li>Invite others: {'✅' if invitation_data.can_invite_members else '❌'}</li>
            </ul>
            <p><a href="{invitation_url}" style="display: inline-block; padding: 12px 24px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px; margin-top: 16px;">Accept Invitation</a></p>
            <p style="color: #666; font-size: 12px; margin-top: 24px;">This invitation expires in 7 days.</p>
            <p style="color: #666; font-size: 12px;">If you can't click the button, copy this link: {invitation_url}</p>
            """
        )
    except Exception as e:
        print(f"Failed to send invitation email: {e}")
        # Don't fail the invitation creation if email fails
    
    return FamilyInvitationResponse(
        id=str(invitation_doc["_id"]),
        family_id=str(family_id),
        family_name=family_doc["name"],
        invited_by_name=current_user["name"],
        invited_by_email=current_user["email"],
        invitee_email=invitation_data.email,
        invitee_name=invitation_data.name,
        role=invitation_data.role,
        status="pending",
        token=token,
        expires_at=invitation_doc["expires_at"],
        created_at=invitation_doc["created_at"]
    )


@router.get("/invitations", response_model=List[FamilyInvitationResponse])
async def get_family_invitations(current_user: dict = Depends(get_current_user)):
    """Get all pending invitations for my family"""
    db = await get_database()
    user_id = current_user["_id"]
    
    # Get user's family
    membership = await db.family_members.find_one({"user_id": user_id})
    if not membership:
        return []
    
    family_id = membership["family_id"]
    
    # Get invitations
    invitations = await db.family_invitations.find({
        "family_id": family_id,
        "status": "pending"
    }).to_list(100)
    
    return [
        FamilyInvitationResponse(
            id=str(inv["_id"]),
            family_id=str(inv["family_id"]),
            family_name=inv["family_name"],
            invited_by_name=inv["invited_by_name"],
            invited_by_email=inv["invited_by_email"],
            invitee_email=inv["invitee_email"],
            invitee_name=inv["invitee_name"],
            role=inv["role"],
            status=inv["status"],
            token=inv["token"],
            expires_at=inv["expires_at"],
            created_at=inv["created_at"]
        )
        for inv in invitations
    ]


@router.post("/accept-invitation")
async def accept_invitation(request: AcceptInvitationRequest):
    """Accept a family invitation (can create account if needed)"""
    db = await get_database()
    
    # Find invitation
    invitation = await db.family_invitations.find_one({
        "token": request.token,
        "status": "pending"
    })
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or already used"
        )
    
    # Check expiration
    if invitation["expires_at"] < datetime.utcnow():
        await db.family_invitations.update_one(
            {"_id": invitation["_id"]},
            {"$set": {"status": "expired"}}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has expired"
        )
    
    # Check if user exists
    user = await db.users.find_one({"email": invitation["invitee_email"]})
    
    # If user doesn't exist, create account
    if not user:
        if not request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password required to create new account"
            )
        
        # Create new user
        hashed_password = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt()).decode()
        user_doc = {
            "name": invitation["invitee_name"],
            "email": invitation["invitee_email"],
            "password": hashed_password,
            "role": "consumer",
            "plan": "free",
            "created_at": datetime.utcnow()
        }
        result = await db.users.insert_one(user_doc)
        user_id = result.inserted_id
    else:
        user_id = user["_id"]
    
    # Check if already a member of this family
    existing = await db.family_members.find_one({
        "family_id": invitation["family_id"],
        "user_id": user_id
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of this family"
        )
    
    # Add as family member
    member_doc = {
        "family_id": invitation["family_id"],
        "user_id": user_id,
        "email": invitation["invitee_email"],
        "name": invitation["invitee_name"],
        "role": invitation["role"],
        "can_manage_devices": invitation.get("can_manage_devices", True),
        "can_resolve_alerts": invitation.get("can_resolve_alerts", True),
        "can_invite_members": invitation.get("can_invite_members", False),
        "joined_at": datetime.utcnow()
    }
    
    await db.family_members.insert_one(member_doc)
    
    # Mark invitation as accepted
    await db.family_invitations.update_one(
        {"_id": invitation["_id"]},
        {"$set": {"status": "accepted", "accepted_at": datetime.utcnow()}}
    )
    
    return {
        "message": "Successfully joined the family!",
        "family_name": invitation["family_name"],
        "role": invitation["role"]
    }


@router.delete("/members/{member_user_id}")
async def remove_family_member(
    member_user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a member from the family (admin only)"""
    db = await get_database()
    user_id = current_user["_id"]
    
    # Check if user is admin
    membership = await db.family_members.find_one({"user_id": user_id})
    if not membership or membership["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only family admins can remove members"
        )
    
    family_id = membership["family_id"]
    
    # Can't remove yourself if you're the owner
    family_doc = await db.families.find_one({"_id": family_id})
    if str(family_doc["owner_id"]) == member_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the family owner"
        )
    
    # Remove member
    try:
        member_obj_id = ObjectId(member_user_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    result = await db.family_members.delete_one({
        "family_id": family_id,
        "user_id": member_obj_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    return {"message": "Member removed successfully"}


@router.delete("/my-family")
async def leave_family(current_user: dict = Depends(get_current_user)):
    """Leave your current family"""
    db = await get_database()
    user_id = current_user["_id"]
    
    # Find membership
    membership = await db.family_members.find_one({"user_id": user_id})
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not part of any family"
        )
    
    family_id = membership["family_id"]
    
    # Check if owner
    family_doc = await db.families.find_one({"_id": family_id})
    if not family_doc:
        # Family missing - can't check ownership, allow leaving
        pass
    elif family_doc["owner_id"] == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Family owner cannot leave. Transfer ownership or delete the family first."
        )
    
    # Remove membership
    await db.family_members.delete_one({"_id": membership["_id"]})
    
    return {"message": "Successfully left the family"}


@router.delete("/invitations/{invitation_id}")
async def cancel_invitation(
    invitation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a pending invitation (admin only)"""
    db = await get_database()
    user_id = current_user["_id"]
    
    # Check if user is admin
    membership = await db.family_members.find_one({"user_id": user_id})
    if not membership or membership["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only family admins can cancel invitations"
        )
    
    family_id = membership["family_id"]
    
    # Find invitation
    try:
        invitation_obj_id = ObjectId(invitation_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invitation ID"
        )
    
    invitation = await db.family_invitations.find_one({
        "_id": invitation_obj_id,
        "family_id": family_id
    })
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    if invitation["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending invitations"
        )
    
    # Cancel invitation
    await db.family_invitations.update_one(
        {"_id": invitation_obj_id},
        {"$set": {"status": "cancelled", "cancelled_at": datetime.utcnow()}}
    )
    
    return {"message": "Invitation cancelled successfully"}
