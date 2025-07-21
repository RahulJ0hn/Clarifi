from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_id, verify_user_owns_data
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationMarkReadRequest,
    NotificationCreateRequest,
    NotificationStatsResponse
)
from app.services.websocket_manager import websocket_manager

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/notifications/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get notification statistics for current user
    """
    try:
        logger.info(f"📊 Getting notification stats for user: {current_user.id}")
        
        # Get stats for current user only
        total_notifications = db.query(Notification).filter(Notification.user_id == current_user.id).count()
        unread_notifications = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).count()
        
        # Get recent notifications (last 7 days) for current user
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_notifications = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.created_at >= seven_days_ago
        ).count()
        
        # Get notifications by type for current user
        notification_types = {}
        for notification_type in ["info", "warning", "error", "success"]:
            count = db.query(Notification).filter(
                Notification.user_id == current_user.id,
                Notification.notification_type == notification_type
            ).count()
            notification_types[notification_type] = count
        
        # Get notifications by priority for current user
        notification_priorities = {}
        for priority in ["low", "normal", "high", "urgent"]:
            count = db.query(Notification).filter(
                Notification.user_id == current_user.id,
                Notification.priority == priority
            ).count()
            notification_priorities[priority] = count
        
        logger.info(f"✅ Notification stats for user {current_user.id}: {total_notifications} total, {unread_notifications} unread")
        
        return NotificationStatsResponse(
            total_notifications=total_notifications,
            unread_notifications=unread_notifications,
            recent_notifications=recent_notifications,
            notifications_by_type=notification_types,
            notifications_by_priority=notification_priorities
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting notification stats for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting notification stats: {str(e)}")

@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    page: int = 1,
    per_page: int = 20,
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    source_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get notifications with pagination and filtering - user-specific
    """
    try:
        logger.info(f"📋 Getting notifications for user: {current_user.id}")
        logger.info(f"   Page: {page}, Per page: {per_page}, Unread only: {unread_only}")
        
        # Filter by current user only
        query = db.query(Notification).filter(Notification.user_id == current_user.id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
            logger.info("   Filtering unread notifications only")
        
        if notification_type:
            query = query.filter(Notification.notification_type == notification_type)
            logger.info(f"   Filtering by type: {notification_type}")
        
        if source_type:
            query = query.filter(Notification.source_type == source_type)
            logger.info(f"   Filtering by source type: {source_type}")
        
        # Get total count for current user
        total = query.count()
        logger.info(f"   Total notifications for user: {total}")
        
        # Get unread count for current user
        unread_count = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        notifications = query.order_by(Notification.created_at.desc()).offset(offset).limit(per_page).all()
        
        notification_list = [NotificationResponse(**notification.to_dict()) for notification in notifications]
        
        logger.info(f"✅ Retrieved {len(notification_list)} notifications for user: {current_user.id}")
        
        return NotificationListResponse(
            notifications=notification_list,
            total=total,
            unread_count=unread_count,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"❌ Error retrieving notifications for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving notifications: {str(e)}")

@router.get("/notifications/recent")
async def get_recent_notifications(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recent notifications for current user
    """
    try:
        logger.info(f"📋 Getting recent notifications for user: {current_user.id}, limit: {limit}")
        
        # Filter by current user only
        notifications = db.query(Notification).filter(
            Notification.user_id == current_user.id
        ).order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
        
        notification_list = [NotificationResponse(**notification.to_dict()) for notification in notifications]
        
        logger.info(f"✅ Retrieved {len(notification_list)} recent notifications for user: {current_user.id}")
        
        return {
            "notifications": notification_list,
            "count": len(notification_list)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting recent notifications for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting recent notifications: {str(e)}")

@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific notification by ID - user-specific access
    """
    try:
        logger.info(f"🔍 Getting notification {notification_id} for user: {current_user.id}")
        
        # Get notification and verify ownership
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id  # Only allow access to own notifications
        ).first()
        
        if not notification:
            logger.warning(f"❌ Notification {notification_id} not found or access denied for user: {current_user.id}")
            raise HTTPException(status_code=404, detail="Notification not found")
        
        logger.info(f"✅ Notification {notification_id} retrieved for user: {current_user.id}")
        
        return NotificationResponse(**notification.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving notification {notification_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving notification: {str(e)}")

@router.post("/notifications/mark-read")
async def mark_notifications_read(
    request: NotificationMarkReadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark notifications as read - user-specific
    """
    try:
        logger.info(f"📝 Marking notifications as read for user: {current_user.id}")
        logger.info(f"   Notification IDs: {request.notification_ids}")
        
        # Update notifications owned by current user only
        updated_count = db.query(Notification).filter(
            Notification.id.in_(request.notification_ids),
            Notification.user_id == current_user.id,  # Only allow marking own notifications
            Notification.is_read == False
        ).update({
            Notification.is_read: True,
            Notification.read_at: datetime.utcnow()
        }, synchronize_session=False)
        
        db.commit()
        
        logger.info(f"✅ Marked {updated_count} notifications as read for user: {current_user.id}")
        
        return {
            "message": f"Marked {updated_count} notifications as read",
            "updated_count": updated_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error marking notifications as read for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error marking notifications as read: {str(e)}")

@router.post("/notifications/mark-all-read")
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark all notifications as read for current user
    """
    try:
        logger.info(f"📝 Marking all notifications as read for user: {current_user.id}")
        
        updated_count = db.query(Notification).filter(
            Notification.user_id == current_user.id,  # Only allow marking own notifications
            Notification.is_read == False
        ).update({
            Notification.is_read: True,
            Notification.read_at: datetime.utcnow()
        }, synchronize_session=False)
        
        db.commit()
        
        logger.info(f"✅ Marked all {updated_count} notifications as read for user: {current_user.id}")
        
        return {
            "message": f"Marked all {updated_count} notifications as read",
            "updated_count": updated_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error marking all notifications as read for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error marking all notifications as read: {str(e)}")

@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a notification - user-specific access
    """
    try:
        logger.info(f"🗑️ Deleting notification {notification_id} for user: {current_user.id}")
        
        # Get notification and verify ownership
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id  # Only allow deletion of own notifications
        ).first()
        
        if not notification:
            logger.warning(f"❌ Notification {notification_id} not found or access denied for user: {current_user.id}")
            raise HTTPException(status_code=404, detail="Notification not found")
        
        db.delete(notification)
        db.commit()
        
        logger.info(f"✅ Notification {notification_id} deleted for user: {current_user.id}")
        
        return {"message": "Notification deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting notification {notification_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting notification: {str(e)}")

@router.delete("/notifications")
async def delete_all_notifications(
    read_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete all notifications or only read ones for current user
    """
    try:
        logger.info(f"🗑️ Deleting notifications for user: {current_user.id}, read_only: {read_only}")
        
        query = db.query(Notification).filter(Notification.user_id == current_user.id)  # Only allow deletion of own notifications
        
        if read_only:
            query = query.filter(Notification.is_read == True)
        
        deleted_count = query.delete(synchronize_session=False)
        db.commit()
        
        message = f"Deleted {deleted_count} {'read' if read_only else 'all'} notifications"
        logger.info(f"✅ {message} for user: {current_user.id}")
        
        return {
            "message": message,
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error deleting notifications for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting notifications: {str(e)}")

@router.post("/notifications", response_model=NotificationResponse)
async def create_notification(
    request: NotificationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new notification for current user
    """
    try:
        logger.info(f"📝 Creating notification for user: {current_user.id}")
        logger.info(f"   Title: {request.title}, Type: {request.notification_type}")
        
        notification = Notification(
            user_id=current_user.id,  # Associate with current user
            title=request.title,
            message=request.message,
            notification_type=request.notification_type,
            source=request.source,
            source_type=request.source_type,
            priority=request.priority,
            data=request.data
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        # Send real-time notification
        await websocket_manager.send_notification(notification.to_dict())
        
        logger.info(f"✅ Notification created successfully: {notification.id} for user: {current_user.id}")
        
        return NotificationResponse(**notification.to_dict())
        
    except Exception as e:
        logger.error(f"❌ Error creating notification for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating notification: {str(e)}")

@router.get("/notifications/unread/count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get count of unread notifications for current user
    """
    try:
        logger.info(f"📊 Getting unread count for user: {current_user.id}")
        
        unread_count = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).count()
        
        logger.info(f"✅ User {current_user.id} has {unread_count} unread notifications")
        
        return {"unread_count": unread_count}
        
    except Exception as e:
        logger.error(f"❌ Error getting unread count for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting unread count: {str(e)}")

@router.get("/notifications/types")
async def get_notification_types():
    """
    Get available notification types and priorities
    """
    return {
        "types": [
            {"value": "info", "label": "Information", "color": "blue"},
            {"value": "warning", "label": "Warning", "color": "yellow"},
            {"value": "error", "label": "Error", "color": "red"},
            {"value": "success", "label": "Success", "color": "green"}
        ],
        "priorities": [
            {"value": "low", "label": "Low"},
            {"value": "normal", "label": "Normal"},
            {"value": "high", "label": "High"},
            {"value": "urgent", "label": "Urgent"}
        ]
    } 