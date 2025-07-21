from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_id, verify_user_owns_data
from app.models.monitor import Monitor
from app.models.user import User
from app.schemas.monitor import (
    MonitorCreateRequest,
    MonitorUpdateRequest,
    MonitorResponse,
    MonitorListResponse,
    MonitorStatusResponse
)
from app.services.scheduler import scheduler
from app.services.scraper_service import scraper_service
from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/monitors", response_model=MonitorResponse)
async def create_monitor(
    request: MonitorCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new monitor - requires authentication
    """
    try:
        logger.info(f"📝 Creating monitor for user: {current_user.id}")
        logger.info(f"   Name: {request.name}, Type: {request.monitor_type}")
        
        # Check if we've reached the maximum number of monitors for this user
        monitor_count = db.query(Monitor).filter(Monitor.user_id == current_user.id).count()
        if monitor_count >= settings.MAX_MONITORS_PER_USER:
            logger.warning(f"❌ User {current_user.id} reached monitor limit: {settings.MAX_MONITORS_PER_USER}")
            raise HTTPException(
                status_code=400, 
                detail=f"Maximum number of monitors ({settings.MAX_MONITORS_PER_USER}) reached"
            )
        
        # Create monitor with user association
        monitor = Monitor(
            user_id=current_user.id,  # Associate with current user
            name=request.name,
            url=request.url,
            monitor_type=request.monitor_type,
            css_selector=request.css_selector,
            xpath_selector=request.xpath_selector,
            item_name=request.item_name,
            item_type=request.item_type,
            check_interval=request.check_interval,
            notification_enabled=request.notification_enabled,
            monitor_metadata=request.metadata
        )
        
        db.add(monitor)
        db.commit()
        db.refresh(monitor)
        
        # Add to scheduler if active
        if monitor.is_active:
            scheduler.add_monitor_job(monitor)
        
        logger.info(f"✅ Monitor created successfully: {monitor.id} for user: {current_user.id}")
        
        return MonitorResponse(**monitor.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating monitor for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating monitor: {str(e)}")

@router.get("/monitors", response_model=MonitorListResponse)
async def get_monitors(
    page: int = 1,
    per_page: int = 20,
    active_only: bool = False,
    monitor_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of monitors with pagination and filtering - user-specific
    """
    try:
        logger.info(f"📋 Getting monitors for user: {current_user.id}")
        logger.info(f"   Page: {page}, Per page: {per_page}, Active only: {active_only}")
        
        # Filter by current user only
        query = db.query(Monitor).filter(Monitor.user_id == current_user.id)
        
        if active_only:
            query = query.filter(Monitor.is_active == True)
            logger.info("   Filtering active monitors only")
        
        if monitor_type:
            query = query.filter(Monitor.monitor_type == monitor_type)
            logger.info(f"   Filtering by type: {monitor_type}")
        
        # Get total count for current user
        total = query.count()
        logger.info(f"   Total monitors for user: {total}")
        
        # Apply pagination
        offset = (page - 1) * per_page
        monitors = query.order_by(Monitor.created_at.desc()).offset(offset).limit(per_page).all()
        
        monitor_list = [MonitorResponse(**monitor.to_dict()) for monitor in monitors]
        
        logger.info(f"✅ Retrieved {len(monitor_list)} monitors for user: {current_user.id}")
        
        return MonitorListResponse(
            monitors=monitor_list,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"❌ Error retrieving monitors for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving monitors: {str(e)}")

@router.get("/monitors/types")
async def get_monitor_types():
    """
    Get available monitor types
    """
    return {
        "types": [
            {"value": "content", "label": "Content Changes", "description": "Monitor for any content changes"},
            {"value": "price", "label": "Price Changes", "description": "Monitor for price changes on product pages"},
            {"value": "selector", "label": "Specific Element", "description": "Monitor a specific element using CSS selector"},
            {"value": "item_search", "label": "Item Search", "description": "Search for specific items (stocks, crypto, products) using Perplexity-style techniques"}
        ],
        "item_types": [
            {"value": "crypto", "label": "Cryptocurrency", "description": "Bitcoin, Ethereum, Cardano, etc."},
            {"value": "stock", "label": "Stock", "description": "AAPL, GOOGL, TSLA, etc."},
            {"value": "product", "label": "Product", "description": "iPhone, Samsung, Laptop, etc."},
            {"value": "news", "label": "News", "description": "Headlines, articles, updates"},
            {"value": "auto", "label": "Auto-detect", "description": "Automatically detect item type"}
        ]
    }

@router.get("/monitors/stats")
async def get_monitor_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get monitor statistics for current user
    """
    try:
        logger.info(f"📊 Getting monitor stats for user: {current_user.id}")
        
        # Get stats for current user only
        total_monitors = db.query(Monitor).filter(Monitor.user_id == current_user.id).count()
        active_monitors = db.query(Monitor).filter(
            Monitor.user_id == current_user.id,
            Monitor.is_active == True
        ).count()
        inactive_monitors = total_monitors - active_monitors
        
        # Get monitors by type for current user
        monitor_types = {}
        for monitor_type in ["content", "price", "selector", "item_search"]:
            count = db.query(Monitor).filter(
                Monitor.user_id == current_user.id,
                Monitor.monitor_type == monitor_type
            ).count()
            monitor_types[monitor_type] = count
        
        # Get recent changes (monitors that have changed in last 24 hours) for current user
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_changes = db.query(Monitor).filter(
            Monitor.user_id == current_user.id,
            Monitor.last_changed >= yesterday
        ).count()
        
        # Get monitors that haven't been checked recently (more than 1 hour ago) for current user
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        stale_monitors = db.query(Monitor).filter(
            Monitor.user_id == current_user.id,
            Monitor.last_checked < one_hour_ago
        ).count()
        
        logger.info(f"✅ Monitor stats for user {current_user.id}: {total_monitors} total, {active_monitors} active")
        
        return {
            "total_monitors": total_monitors,
            "active_monitors": active_monitors,
            "inactive_monitors": inactive_monitors,
            "monitor_types": monitor_types,
            "recent_changes": recent_changes,
            "stale_monitors": stale_monitors,
            "scheduler_running": scheduler.is_running()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting monitor stats for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting monitor stats: {str(e)}")

@router.get("/monitors/{monitor_id}", response_model=MonitorResponse)
async def get_monitor(
    monitor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific monitor by ID - user-specific
    """
    try:
        monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
        
        if not monitor:
            raise HTTPException(status_code=404, detail="Monitor not found")
        
        # Verify user owns the monitor
        if not verify_user_owns_data(db, current_user.id, monitor.id):
            raise HTTPException(status_code=403, detail="You do not have permission to access this monitor")
        
        return MonitorResponse(**monitor.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving monitor {monitor_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving monitor: {str(e)}")

@router.put("/monitors/{monitor_id}", response_model=MonitorResponse)
async def update_monitor(
    monitor_id: str,
    request: MonitorUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a monitor - user-specific
    """
    try:
        monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
        
        if not monitor:
            raise HTTPException(status_code=404, detail="Monitor not found")
        
        # Verify user owns the monitor
        if not verify_user_owns_data(db, current_user.id, monitor.id):
            raise HTTPException(status_code=403, detail="You do not have permission to update this monitor")
        
        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            # Map metadata field to monitor_metadata to avoid SQLAlchemy conflict
            if field == 'metadata':
                setattr(monitor, 'monitor_metadata', value)
            else:
                setattr(monitor, field, value)
        
        db.commit()
        db.refresh(monitor)
        
        # Update scheduler if interval or active status changed
        if 'check_interval' in update_data or 'is_active' in update_data:
            scheduler.update_monitor_job(monitor)
        
        logger.info(f"✅ Monitor {monitor_id} updated successfully for user: {current_user.id}")
        
        return MonitorResponse(**monitor.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating monitor {monitor_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating monitor: {str(e)}")

@router.delete("/monitors/{monitor_id}")
async def delete_monitor(
    monitor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a monitor - user-specific
    """
    try:
        monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
        
        if not monitor:
            raise HTTPException(status_code=404, detail="Monitor not found")
        
        # Verify user owns the monitor
        if not verify_user_owns_data(db, current_user.id, monitor.id):
            raise HTTPException(status_code=403, detail="You do not have permission to delete this monitor")
        
        # Remove from scheduler
        scheduler.remove_monitor_job(monitor_id)
        
        db.delete(monitor)
        db.commit()
        
        logger.info(f"✅ Monitor {monitor_id} deleted successfully for user: {current_user.id}")
        
        return {"message": "Monitor deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting monitor {monitor_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting monitor: {str(e)}")

@router.post("/monitors/{monitor_id}/check")
async def check_monitor_now(
    monitor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check a monitor immediately - user-specific
    """
    try:
        monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
        
        if not monitor:
            raise HTTPException(status_code=404, detail="Monitor not found")
        
        # Verify user owns the monitor
        if not verify_user_owns_data(db, current_user.id, monitor.id):
            raise HTTPException(status_code=403, detail="You do not have permission to check this monitor")
        
        # Perform the check based on monitor type
        if monitor.monitor_type == "item_search" and monitor.item_name:
            # Use Perplexity-style search
            result = await scraper_service.search_for_specific_item(
                monitor.url, 
                monitor.item_name, 
                monitor.item_type or 'auto'
            )
            
            if result['success']:
                # Extract relevant data from search results
                found_data = result['found_data']
                current_value = _format_item_search_results(found_data)
                
                # Update monitor
                monitor.previous_value = monitor.current_value
                monitor.current_value = current_value
                monitor.last_checked = datetime.utcnow()
                
                # Check if value changed
                if monitor.previous_value != monitor.current_value:
                    monitor.last_changed = datetime.utcnow()
                
                db.commit()
                
                logger.info(f"✅ Monitor {monitor_id} checked successfully for user: {current_user.id}")
                
                return {
                    "success": True,
                    "message": f"Found {len(found_data.get('exact_matches', []))} matches for {monitor.item_name}",
                    "current_value": current_value,
                    "search_results": result
                }
            else:
                logger.warning(f"❌ Could not find {monitor.item_name} on {monitor.url} for monitor {monitor_id} for user {current_user.id}")
                return {
                    "success": False,
                    "message": f"Could not find {monitor.item_name} on {monitor.url}",
                    "error": result.get('error', 'Unknown error')
                }
        
        else:
            # Use traditional scraping methods
            if monitor.css_selector:
                current_value = await scraper_service.extract_element_content(
                    monitor.url, monitor.css_selector
                )
            else:
                title, content, _ = await scraper_service.fetch_page_content(monitor.url)
                current_value = content[:1000]  # Limit content length
            
            # Update monitor
            monitor.previous_value = monitor.current_value
            monitor.current_value = current_value
            monitor.last_checked = datetime.utcnow()
            
            # Check if value changed
            if monitor.previous_value != monitor.current_value:
                monitor.last_changed = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"✅ Monitor {monitor_id} checked successfully for user: {current_user.id}")
            
            return {
                "success": True,
                "message": "Monitor checked successfully",
                "current_value": current_value
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error checking monitor {monitor_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking monitor: {str(e)}")

def _format_item_search_results(found_data: dict) -> str:
    """Format item search results for storage with enhanced market data"""
    parts = []
    
    # Add exact matches
    if found_data.get('exact_matches'):
        parts.append(f"Exact matches: {len(found_data['exact_matches'])}")
        for match in found_data['exact_matches'][:3]:  # Limit to first 3
            context = match.get('context', '')[:100] if isinstance(match, dict) else str(match)[:100]
            parts.append(f"- {context}...")
    
    # Add extracted prices
    if found_data.get('extracted_prices'):
        prices = found_data['extracted_prices'][:3]  # Limit to first 3
        parts.append(f"Prices found: {', '.join(prices)}")
    
    # Add market data for crypto/stocks
    if found_data.get('market_data'):
        market_data = found_data['market_data']
        market_parts = []
        
        if market_data.get('price'):
            market_parts.append(f"Price: {market_data['price']}")
        
        if market_data.get('change_24h'):
            market_parts.append(f"24h: {market_data['change_24h']}")
        
        if market_data.get('market_cap'):
            market_parts.append(f"Market Cap: {market_data['market_cap']}")
        
        if market_parts:
            parts.append(f"Market Data: {' | '.join(market_parts)}")
    
    # Add change percentages
    if found_data.get('change_percentages'):
        changes = found_data['change_percentages'][:3]  # Limit to first 3
        parts.append(f"Changes: {', '.join(changes)}")
    
    # Add price data
    if found_data.get('price_data'):
        prices = found_data['price_data'][:3]  # Limit to first 3
        parts.append(f"Price data: {', '.join(prices)}")
    
    # Add related info
    if found_data.get('related_info'):
        parts.append(f"Related info: {len(found_data['related_info'])} items")
    
    return " | ".join(parts) if parts else "No data found"

@router.get("/monitors/{monitor_id}/status", response_model=MonitorStatusResponse)
async def get_monitor_status(
    monitor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get monitor status - user-specific
    """
    try:
        monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
        
        if not monitor:
            raise HTTPException(status_code=404, detail="Monitor not found")
        
        # Verify user owns the monitor
        if not verify_user_owns_data(db, current_user.id, monitor.id):
            raise HTTPException(status_code=403, detail="You do not have permission to access this monitor")
        
        # Determine if monitor has changed recently
        has_changed = False
        if monitor.last_changed:
            from datetime import timedelta
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            has_changed = monitor.last_changed >= one_hour_ago
        
        logger.info(f"✅ Retrieved status for monitor {monitor_id} for user: {current_user.id}")
        
        return MonitorStatusResponse(
            id=monitor.id,
            name=monitor.name,
            url=monitor.url,
            current_value=monitor.current_value,
            previous_value=monitor.previous_value,
            last_checked=monitor.last_checked,
            last_changed=monitor.last_changed,
            is_active=monitor.is_active,
            has_changed=has_changed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting status for monitor {monitor_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting monitor status: {str(e)}")

@router.post("/monitors/{monitor_id}/toggle")
async def toggle_monitor(
    monitor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Toggle monitor active status - user-specific
    """
    try:
        monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
        
        if not monitor:
            raise HTTPException(status_code=404, detail="Monitor not found")
        
        # Verify user owns the monitor
        if not verify_user_owns_data(db, current_user.id, monitor.id):
            raise HTTPException(status_code=403, detail="You do not have permission to toggle this monitor")
        
        monitor.is_active = not monitor.is_active
        
        # Update scheduler
        if monitor.is_active:
            scheduler.add_monitor_job(monitor)
        else:
            scheduler.remove_monitor_job(monitor.id)
        
        db.commit()
        db.refresh(monitor)
        
        logger.info(f"✅ Monitor {monitor_id} toggled active status for user: {current_user.id}")
        
        return {
            "message": f"Monitor {'activated' if monitor.is_active else 'deactivated'} successfully",
            "is_active": monitor.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error toggling monitor {monitor_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error toggling monitor: {str(e)}")

@router.post("/monitors/check-all")
async def check_all_monitors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check all active monitors - user-specific
    """
    try:
        active_monitors = db.query(Monitor).filter(Monitor.is_active == True).all()
        
        results = []
        for monitor in active_monitors:
            try:
                # Verify user owns the monitor
                if not verify_user_owns_data(db, current_user.id, monitor.id):
                    results.append({
                        "monitor_id": monitor.id,
                        "name": monitor.name,
                        "success": False,
                        "message": "Permission denied"
                    })
                    continue

                # Use the same logic as check_monitor_now
                if monitor.monitor_type == "item_search" and monitor.item_name:
                    result = await scraper_service.search_for_specific_item(
                        monitor.url, 
                        monitor.item_name, 
                        monitor.item_type or 'auto'
                    )
                    
                    if result['success']:
                        found_data = result['found_data']
                        current_value = _format_item_search_results(found_data)
                        
                        monitor.previous_value = monitor.current_value
                        monitor.current_value = current_value
                        monitor.last_checked = datetime.utcnow()
                        
                        if monitor.previous_value != monitor.current_value:
                            monitor.last_changed = datetime.utcnow()
                        
                        results.append({
                            "monitor_id": monitor.id,
                            "name": monitor.name,
                            "success": True,
                            "message": f"Found {len(found_data.get('exact_matches', []))} matches"
                        })
                    else:
                        results.append({
                            "monitor_id": monitor.id,
                            "name": monitor.name,
                            "success": False,
                            "message": result.get('error', 'Unknown error')
                        })
                
                else:
                    if monitor.css_selector:
                        current_value = await scraper_service.extract_element_content(
                            monitor.url, monitor.css_selector
                        )
                    else:
                        title, content, _ = await scraper_service.fetch_page_content(monitor.url)
                        current_value = content[:1000]
                    
                    monitor.previous_value = monitor.current_value
                    monitor.current_value = current_value
                    monitor.last_checked = datetime.utcnow()
                    
                    if monitor.previous_value != monitor.current_value:
                        monitor.last_changed = datetime.utcnow()
                    
                    results.append({
                        "monitor_id": monitor.id,
                        "name": monitor.name,
                        "success": True,
                        "message": "Checked successfully"
                    })
                    
            except Exception as e:
                results.append({
                    "monitor_id": monitor.id,
                    "name": monitor.name,
                    "success": False,
                    "message": str(e)
                })
        
        db.commit()
        
        logger.info(f"✅ Checked {len(active_monitors)} monitors for user: {current_user.id}")
        
        return {
            "message": f"Checked {len(active_monitors)} monitors",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking all monitors for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking all monitors: {str(e)}")

@router.get("/scheduler/status")
async def get_scheduler_status():
    """
    Get scheduler status
    """
    try:
        return {
            "is_running": scheduler.is_running(),
            "job_count": len(scheduler.monitor_jobs),
            "active_monitors": len(scheduler.monitor_jobs),
            "scheduler_running": scheduler.running,
            "jobs": scheduler.get_job_info()
        }
    except Exception as e:
        return {
            "is_running": False,
            "job_count": 0,
            "active_monitors": 0,
            "scheduler_running": False,
            "error": str(e)
        } 