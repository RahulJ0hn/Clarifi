from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_id, verify_user_owns_data
from app.models.user import User
from app.models.summary import Summary
from app.schemas.summary import (
    SummarizeRequest, 
    SummarizeResponse, 
    SummaryHistory,
    SummaryListResponse
)
from app.services.ai_service import ai_service
from app.services.scraper_service import scraper_service

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_webpage(
    request: SummarizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Summarize a webpage with optional question answering - requires authentication
    """
    try:
        logger.info(f"📝 Creating summary for user: {current_user.id}")
        logger.info(f"   URL: {request.url}")
        logger.info(f"   Question: {request.question}")
        
        # Fetch webpage content
        title, content, raw_html = await scraper_service.fetch_page_content(request.url)
        
        if not content:
            raise HTTPException(status_code=400, detail="Unable to extract content from the webpage")
        
        # Generate summary using AI
        summary_text, answer, processing_time = await ai_service.summarize_content(
            content=content,
            title=title,
            question=request.question,
            provider=request.ai_provider
        )
        
        # Save to database with user association
        summary = Summary(
            user_id=current_user.id,  # Associate with current user
            url=request.url,
            title=title,
            content=content if request.include_content else None,
            summary_text=summary_text,
            question=request.question,
            response=answer,
            ai_provider=request.ai_provider or ai_service.get_available_providers()[0],
            processing_time=processing_time
        )
        
        db.add(summary)
        db.commit()
        db.refresh(summary)
        
        logger.info(f"✅ Summary created successfully: {summary.id} for user: {current_user.id}")
        
        return SummarizeResponse(
            id=summary.id,
            url=summary.url,
            title=summary.title,
            summary_text=summary.summary_text,
            question=summary.question,
            response=summary.response,
            ai_provider=summary.ai_provider,
            processing_time=summary.processing_time,
            created_at=summary.created_at
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating summary for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error summarizing webpage: {str(e)}")

@router.get("/summaries", response_model=SummaryListResponse)
async def get_summaries(
    page: int = 1,
    per_page: int = 20,
    url_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of summaries with pagination and optional URL filtering - user-specific
    """
    try:
        logger.info(f"📋 Getting summaries for user: {current_user.id}")
        logger.info(f"   Page: {page}, Per page: {per_page}")
        
        # Filter by current user only
        query = db.query(Summary).filter(Summary.user_id == current_user.id)
        
        if url_filter:
            query = query.filter(Summary.url.contains(url_filter))
            logger.info(f"   URL filter: {url_filter}")
        
        # Get total count for current user
        total = query.count()
        logger.info(f"   Total summaries for user: {total}")
        
        # Apply pagination
        offset = (page - 1) * per_page
        summaries = query.order_by(Summary.created_at.desc()).offset(offset).limit(per_page).all()
        
        summary_list = [
            SummaryHistory(
                id=summary.id,
                url=summary.url,
                title=summary.title,
                summary_text=summary.summary_text,
                question=summary.question,
                response=summary.response,
                created_at=summary.created_at
            )
            for summary in summaries
        ]
        
        logger.info(f"✅ Retrieved {len(summary_list)} summaries for user: {current_user.id}")
        
        return SummaryListResponse(
            summaries=summary_list,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"❌ Error retrieving summaries for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving summaries: {str(e)}")

@router.get("/summaries/{summary_id}", response_model=SummarizeResponse)
async def get_summary(
    summary_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific summary by ID - user-specific access
    """
    try:
        logger.info(f"🔍 Getting summary {summary_id} for user: {current_user.id}")
        
        # Get summary and verify ownership
        summary = db.query(Summary).filter(
            Summary.id == summary_id,
            Summary.user_id == current_user.id  # Only allow access to own summaries
        ).first()
        
        if not summary:
            logger.warning(f"❌ Summary {summary_id} not found or access denied for user: {current_user.id}")
            raise HTTPException(status_code=404, detail="Summary not found")
        
        logger.info(f"✅ Summary {summary_id} retrieved for user: {current_user.id}")
        
        return SummarizeResponse(
            id=summary.id,
            url=summary.url,
            title=summary.title,
            summary_text=summary.summary_text,
            question=summary.question,
            response=summary.response,
            ai_provider=summary.ai_provider,
            processing_time=summary.processing_time,
            created_at=summary.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving summary {summary_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving summary: {str(e)}")

@router.delete("/summaries/{summary_id}")
async def delete_summary(
    summary_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a summary by ID - user-specific access
    """
    try:
        logger.info(f"🗑️ Deleting summary {summary_id} for user: {current_user.id}")
        
        # Get summary and verify ownership
        summary = db.query(Summary).filter(
            Summary.id == summary_id,
            Summary.user_id == current_user.id  # Only allow deletion of own summaries
        ).first()
        
        if not summary:
            logger.warning(f"❌ Summary {summary_id} not found or access denied for user: {current_user.id}")
            raise HTTPException(status_code=404, detail="Summary not found")
        
        db.delete(summary)
        db.commit()
        
        logger.info(f"✅ Summary {summary_id} deleted for user: {current_user.id}")
        
        return {"message": "Summary deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting summary {summary_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting summary: {str(e)}")

@router.get("/me/data-check")
async def data_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check user's data - returns summary count for current user
    """
    try:
        logger.info(f"📊 Data check for user: {current_user.id}")
        
        # Count summaries for current user
        summary_count = db.query(Summary).filter(Summary.user_id == current_user.id).count()
        
        logger.info(f"✅ User {current_user.id} has {summary_count} summaries")
        
        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "summary_count": summary_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error in data check for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking user data: {str(e)}")

@router.post("/analyze-url")
async def analyze_url(
    url: str,
    db: Session = Depends(get_db)
):
    """
    Analyze a URL to detect content type and suggest monitoring options
    """
    try:
        # Detect product information and suggest monitoring
        product_info = await scraper_service.detect_product_info(url)
        
        return {
            "url": url,
            "analysis": product_info,
            "recommendations": {
                "can_monitor": True,
                "suggested_monitor_type": product_info.get("suggested_monitor_type", "content"),
                "price_selectors": product_info.get("price_selectors", []),
                "is_product_page": product_info.get("is_product_page", False)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing URL: {str(e)}")

@router.get("/ai-providers")
async def get_ai_providers():
    """
    Get available AI providers
    """
    try:
        providers = ai_service.get_available_providers()
        return {
            "providers": providers,
            "default": ai_service.get_available_providers()[0] if providers else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting AI providers: {str(e)}")

@router.get("/stats")
async def get_summary_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get summary statistics for current user
    """
    try:
        logger.info(f"📊 Getting stats for user: {current_user.id}")
        
        # Get total summaries for current user
        total_summaries = db.query(Summary).filter(Summary.user_id == current_user.id).count()
        
        # Get recent summaries (last 7 days) for current user
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_summaries = db.query(Summary).filter(
            Summary.user_id == current_user.id,
            Summary.created_at >= seven_days_ago
        ).count()
        
        # Get top domains for current user
        summaries = db.query(Summary).filter(Summary.user_id == current_user.id).all()
        domains = {}
        for summary in summaries:
            try:
                from urllib.parse import urlparse
                domain = urlparse(summary.url).netloc
                domains[domain] = domains.get(domain, 0) + 1
            except:
                continue
        
        top_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]
        
        logger.info(f"✅ Stats for user {current_user.id}: {total_summaries} total, {recent_summaries} recent")
        
        return {
            "total_summaries": total_summaries,
            "recent_summaries": recent_summaries,
            "top_domains": [{"domain": domain, "count": count} for domain, count in top_domains],
            "available_ai_providers": ai_service.get_available_providers()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting stats for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

from datetime import timedelta 