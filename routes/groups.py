# routes/groups.py - Device Grouping/Tags
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
from datetime import datetime

from database import get_database
from routes.auth import get_current_user
from models import DeviceGroupCreate, DeviceGroupUpdate, DeviceGroupResponse

router = APIRouter()


@router.get("/", response_model=List[DeviceGroupResponse])
async def get_groups(current_user: dict = Depends(get_current_user)):
    """Get all device groups for current user"""
    db = await get_database()
    user_id = current_user["_id"]
    
    groups = await db.device_groups.find({"user_id": user_id}).to_list(100)
    
    result = []
    for group in groups:
        # Count devices in this group
        device_count = await db.devices.count_documents({
            "user_id": user_id,
            "groups": group["_id"]
        })
        
        result.append(DeviceGroupResponse(
            id=str(group["_id"]),
            user_id=str(group["user_id"]),
            name=group["name"],
            description=group.get("description"),
            color=group.get("color", "#3b82f6"),
            device_count=device_count,
            created_at=group["created_at"],
            updated_at=group["updated_at"]
        ))
    
    return result


@router.post("/", response_model=DeviceGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: DeviceGroupCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new device group"""
    db = await get_database()
    user_id = current_user["_id"]
    
    group_doc = {
        "user_id": user_id,
        "name": group_data.name,
        "description": group_data.description,
        "color": group_data.color,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.device_groups.insert_one(group_doc)
    group_doc["_id"] = result.inserted_id
    
    return DeviceGroupResponse(
        id=str(group_doc["_id"]),
        user_id=str(user_id),
        name=group_doc["name"],
        description=group_doc["description"],
        color=group_doc["color"],
        device_count=0,
        created_at=group_doc["created_at"],
        updated_at=group_doc["updated_at"]
    )


@router.put("/{group_id}", response_model=DeviceGroupResponse)
async def update_group(
    group_id: str,
    group_update: DeviceGroupUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update device group"""
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        group_obj_id = ObjectId(group_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group ID"
        )
    
    # Check ownership
    group = await db.device_groups.find_one({"_id": group_obj_id, "user_id": user_id})
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Update
    update_data = {k: v for k, v in group_update.dict().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await db.device_groups.update_one(
            {"_id": group_obj_id},
            {"$set": update_data}
        )
    
    # Get updated group
    updated_group = await db.device_groups.find_one({"_id": group_obj_id})
    device_count = await db.devices.count_documents({
        "user_id": user_id,
        "groups": group_obj_id
    })
    
    return DeviceGroupResponse(
        id=str(updated_group["_id"]),
        user_id=str(user_id),
        name=updated_group["name"],
        description=updated_group.get("description"),
        color=updated_group.get("color", "#3b82f6"),
        device_count=device_count,
        created_at=updated_group["created_at"],
        updated_at=updated_group["updated_at"]
    )


@router.delete("/{group_id}")
async def delete_group(
    group_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete device group"""
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        group_obj_id = ObjectId(group_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group ID"
        )
    
    # Check ownership
    group = await db.device_groups.find_one({"_id": group_obj_id, "user_id": user_id})
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Remove group from all devices
    await db.devices.update_many(
        {"user_id": user_id},
        {"$pull": {"groups": group_obj_id}}
    )
    
    # Delete group
    await db.device_groups.delete_one({"_id": group_obj_id})
    
    return {"message": "Group deleted successfully"}


@router.post("/{group_id}/devices/{device_id}")
async def add_device_to_group(
    group_id: str,
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Add a device to a group"""
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        group_obj_id = ObjectId(group_id)
        device_obj_id = ObjectId(device_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID"
        )
    
    # Verify ownership
    group = await db.device_groups.find_one({"_id": group_obj_id, "user_id": user_id})
    device = await db.devices.find_one({"_id": device_obj_id, "user_id": user_id})
    
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    
    # Add to group
    await db.devices.update_one(
        {"_id": device_obj_id},
        {"$addToSet": {"groups": group_obj_id}}
    )
    
    return {"message": "Device added to group"}


@router.delete("/{group_id}/devices/{device_id}")
async def remove_device_from_group(
    group_id: str,
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a device from a group"""
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        group_obj_id = ObjectId(group_id)
        device_obj_id = ObjectId(device_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID"
        )
    
    # Remove from group
    await db.devices.update_one(
        {"_id": device_obj_id, "user_id": user_id},
        {"$pull": {"groups": group_obj_id}}
    )
    
    return {"message": "Device removed from group"}
