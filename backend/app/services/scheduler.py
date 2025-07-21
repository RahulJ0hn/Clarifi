from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import asyncio
import logging
import re
from typing import List, Optional, Dict, Any

from app.core.database import SessionLocal
from app.models.monitor import Monitor
from app.models.notification import Notification
from app.services.scraper_service import scraper_service
from app.services.ai_service import ai_service
from app.services.websocket_manager import websocket_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.running = False
        self.monitor_jobs = {}  # Track individual monitor jobs
    
    def start(self):
        """Start the scheduler"""
        if not self.running:
            self.scheduler.start()
            self.running = True
            
            # Schedule cleanup job (daily)
            self.scheduler.add_job(
                self.cleanup_old_data,
                IntervalTrigger(hours=24),
                id="cleanup_data",
                replace_existing=True
            )
            
            # Load existing monitors and schedule them
            self._schedule_existing_monitors()
            
            logger.info("Scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.running:
            self.scheduler.shutdown()
            self.running = False
            logger.info("Scheduler stopped")
    
    async def check_all_monitors(self):
        """Check all active monitors"""
        db = SessionLocal()
        try:
            # Get all active monitors
            monitors = db.query(Monitor).filter(Monitor.is_active == True).all()
            
            if not monitors:
                logger.debug("No active monitors to check")
                return
            
            logger.info(f"Checking {len(monitors)} active monitors")
            
            # Check each monitor
            for monitor in monitors:
                try:
                    await self.check_monitor(monitor, db)
                except Exception as e:
                    logger.error(f"Error checking monitor {monitor.id}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error in check_all_monitors: {str(e)}")
        finally:
            db.close()
    
    async def check_monitor(self, monitor: Monitor, db: Session):
        """Check a specific monitor for changes"""
        try:
            logger.debug(f"Checking monitor: {monitor.name} ({monitor.url})")
            
            # Extract current content based on monitor type
            if monitor.monitor_type == "item_search" and monitor.item_name:
                # Use Perplexity-style search for specific items
                result = await scraper_service.search_for_specific_item(
                    monitor.url, 
                    monitor.item_name, 
                    monitor.item_type or 'auto'
                )
                
                if result['success']:
                    found_data = result['found_data']
                    current_value = self._format_item_search_results(found_data)
                else:
                    current_value = f"Error: {result.get('error', 'Unknown error')}"
            elif monitor.css_selector:
                current_value = await scraper_service.extract_element_content(
                    monitor.url, 
                    css_selector=monitor.css_selector
                )
            else:
                # Full page content
                title, content, _ = await scraper_service.fetch_page_content(monitor.url)
                current_value = scraper_service.normalize_content(content)
            
            if not current_value:
                logger.warning(f"No content extracted for monitor {monitor.id}")
                return
            
            # Process the value based on monitor type
            processed_value = self._process_monitor_value(monitor, current_value)
            
            # Check if content has changed
            has_changed = False
            if monitor.current_value and monitor.current_value != processed_value:
                has_changed = True
                logger.info(f"Change detected for monitor {monitor.name}")
            else:
                logger.debug(f"No change detected for monitor {monitor.name}")
            
            # Update monitor record
            monitor.previous_value = monitor.current_value
            monitor.current_value = processed_value
            monitor.last_checked = datetime.utcnow()
            
            if has_changed:
                monitor.last_changed = datetime.utcnow()
                logger.info(f"Monitor {monitor.name} detected changes")
                
                # Analyze changes with AI if enabled
                if monitor.previous_value and monitor.notification_enabled:
                    logger.info(f"Processing notification for monitor {monitor.name}")
                    await self.process_monitor_change(monitor, db)
                else:
                    logger.debug(f"Skipping notification for monitor {monitor.name} (disabled or no previous value)")
            
            db.commit()
            
            # Send WebSocket update
            await websocket_manager.send_monitor_update({
                "monitor_id": monitor.id,
                "name": monitor.name,
                "url": monitor.url,
                "has_changed": has_changed,
                "last_checked": monitor.last_checked.isoformat(),
                "current_value": processed_value[:200] + "..." if len(processed_value) > 200 else processed_value
            })
            
        except Exception as e:
            logger.error(f"Error checking monitor {monitor.id}: {str(e)}")
    
    def _process_monitor_value(self, monitor: Monitor, raw_value: str) -> str:
        """Process monitor value based on monitor type"""
        if not raw_value:
            return ""
        
        if monitor.monitor_type == "price":
            # Extract price information
            price_text = self._extract_price_from_value(raw_value, monitor.item_type)
            
            if price_text:
                return price_text
            
            # If no price found, return the raw value with item name
            return f"{monitor.item_name}: {raw_value[:100]}{'...' if len(raw_value) > 100 else ''}"
        
        elif monitor.monitor_type == "item_search" and monitor.item_name:
            # Enhanced item-specific processing using improved price extraction
            price_text = self._extract_price_from_value(raw_value, monitor.item_type)
            
            if price_text:
                return f"{monitor.item_name}: {price_text}"
            
            # If no price found, return the raw value with item name
            return f"{monitor.item_name}: {raw_value[:100]}{'...' if len(raw_value) > 100 else ''}"
        
        elif monitor.monitor_type == "content":
            # For content monitors, clean up the text and get meaningful content
            import re
            # Remove HTML tags
            clean_text = re.sub(r'<[^>]*>', '', raw_value)
            # Remove extra whitespace
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            # Get first meaningful sentence or first 200 characters
            if len(clean_text) > 200:
                # Try to break at sentence boundary
                sentence_match = re.search(r'^.{1,200}[.!?]', clean_text)
                if sentence_match:
                    return sentence_match.group(0)
                else:
                    return clean_text[:200] + "..."
            return clean_text
        
        elif monitor.monitor_type == "selector":
            # For selector monitors, return the extracted value as-is
            return raw_value[:200] + "..." if len(raw_value) > 200 else raw_value
        
        # Default case
        return raw_value[:200] + "..." if len(raw_value) > 200 else raw_value
    
    def _format_item_search_results(self, found_data: dict) -> str:
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
    
    async def process_monitor_change(self, monitor: Monitor, db: Session):
        """Process monitor changes and create notifications"""
        try:
            logger.info(f"Processing change for monitor: {monitor.name}")
            
            # Analyze the change with AI
            change_analysis = await self._analyze_monitor_change(monitor)
            
            # Create notification
            notification = Notification(
                user_id=monitor.user_id,
                title=f"Change Detected: {monitor.name}",
                message=change_analysis['message'],
                notification_type=change_analysis['type'],
                source=monitor.id,
                source_type='monitor',
                data={
                    'monitor_id': monitor.id,
                    'monitor_name': monitor.name,
                    'url': monitor.url,
                    'previous_value': monitor.previous_value,
                    'current_value': monitor.current_value,
                    'change_type': change_analysis['change_type'],
                    'confidence': change_analysis['confidence']
                }
            )
            
            db.add(notification)
            db.commit()
            
            logger.info(f"Created notification for monitor {monitor.name}")
            
        except Exception as e:
            logger.error(f"Error processing monitor change for {monitor.name}: {str(e)}")
    
    async def _analyze_monitor_change(self, monitor: Monitor) -> Dict[str, Any]:
        """Analyze monitor changes with AI"""
        try:
            # For item-specific monitoring, provide detailed analysis
            if monitor.monitor_type == "item_search" and monitor.item_name:
                return await self._analyze_item_change(monitor)
            
            # For price monitoring, analyze price changes
            elif monitor.monitor_type == "price":
                return await self._analyze_price_change(monitor)
            
            # For content monitoring, analyze content changes
            else:
                return await self._analyze_content_change(monitor)
                
        except Exception as e:
            logger.error(f"Error analyzing monitor change: {str(e)}")
            return {
                'message': f"Change detected in {monitor.name}. Previous: {monitor.previous_value[:50]}... Current: {monitor.current_value[:50]}...",
                'type': 'info',
                'change_type': 'general',
                'confidence': 0.5
            }
    
    async def _analyze_item_change(self, monitor: Monitor) -> Dict[str, Any]:
        """Analyze changes for item-specific monitoring"""
        try:
            import re
            
            # Use improved price extraction
            prev_price = self._extract_price_from_value(monitor.previous_value, monitor.item_type)
            curr_price = self._extract_price_from_value(monitor.current_value, monitor.item_type)
            
            if prev_price and curr_price:
                # Calculate price change
                try:
                    # Clean price strings
                    prev_clean = re.sub(r'[^\d.]', '', prev_price)
                    curr_clean = re.sub(r'[^\d.]', '', curr_price)
                    
                    prev_num = float(prev_clean)
                    curr_num = float(curr_clean)
                    
                    change_amount = curr_num - prev_num
                    change_percent = (change_amount / prev_num) * 100
                    
                    if change_amount > 0:
                        change_type = 'increase'
                        emoji = '📈'
                        notification_type = 'success'
                    elif change_amount < 0:
                        change_type = 'decrease'
                        emoji = '📉'
                        notification_type = 'warning'
                    else:
                        change_type = 'no_change'
                        emoji = '➡️'
                        notification_type = 'info'
                    
                    message = f"{emoji} {monitor.item_name} price changed: {prev_price} → {curr_price}"
                    if change_type != 'no_change':
                        message += f" ({change_percent:+.2f}%)"
                    
                    return {
                        'message': message,
                        'type': notification_type,
                        'change_type': change_type,
                        'confidence': 0.9,
                        'price_change': {
                            'previous': prev_price,
                            'current': curr_price,
                            'amount': change_amount,
                            'percent': change_percent
                        }
                    }
                    
                except (ValueError, ZeroDivisionError):
                    pass
            
            # Fallback for non-price changes
            return {
                'message': f"🔍 {monitor.item_name} information updated: {monitor.current_value[:100]}...",
                'type': 'info',
                'change_type': 'update',
                'confidence': 0.7
            }
            
        except Exception as e:
            logger.error(f"Error analyzing item change: {str(e)}")
            return {
                'message': f"Change detected in {monitor.item_name}: {monitor.current_value[:100]}...",
                'type': 'info',
                'change_type': 'general',
                'confidence': 0.5
            }
    
    async def _analyze_price_change(self, monitor: Monitor) -> Dict[str, Any]:
        """Analyze price changes"""
        try:
            # Use improved price extraction
            prev_price = self._extract_price_from_value(monitor.previous_value, monitor.item_type)
            curr_price = self._extract_price_from_value(monitor.current_value, monitor.item_type)
            
            if prev_price and curr_price:
                try:
                    import re
                    # Clean price strings
                    prev_clean = re.sub(r'[^\d.]', '', prev_price)
                    curr_clean = re.sub(r'[^\d.]', '', curr_price)
                    
                    prev_num = float(prev_clean)
                    curr_num = float(curr_clean)
                    
                    change_amount = curr_num - prev_num
                    change_percent = (change_amount / prev_num) * 100
                    
                    if change_amount > 0:
                        emoji = '📈'
                        notification_type = 'success'
                    elif change_amount < 0:
                        emoji = '📉'
                        notification_type = 'warning'
                    else:
                        emoji = '➡️'
                        notification_type = 'info'
                    
                    message = f"{emoji} Price changed: {prev_price} → {curr_price} ({change_percent:+.2f}%)"
                    
                    return {
                        'message': message,
                        'type': notification_type,
                        'change_type': 'price_change',
                        'confidence': 0.9
                    }
                    
                except (ValueError, ZeroDivisionError):
                    pass
            
            return {
                'message': f"Price information updated: {monitor.current_value[:100]}...",
                'type': 'info',
                'change_type': 'price_update',
                'confidence': 0.7
            }
            
        except Exception as e:
            logger.error(f"Error analyzing price change: {str(e)}")
            return {
                'message': f"Price change detected: {monitor.current_value[:100]}...",
                'type': 'info',
                'change_type': 'general',
                'confidence': 0.5
            }
    
    async def _analyze_content_change(self, monitor: Monitor) -> Dict[str, Any]:
        """Analyze content changes"""
        try:
            # Use AI to analyze content changes
            prompt = f"""
            Analyze the change in content for monitor "{monitor.name}":
            
            Previous content: {monitor.previous_value[:500]}
            Current content: {monitor.current_value[:500]}
            
            Provide a brief summary of what changed and its significance.
            """
            
            response = await ai_service.analyze_content(prompt)
            
            return {
                'message': f"Content changed: {response[:200]}...",
                'type': 'info',
                'change_type': 'content_change',
                'confidence': 0.8
            }
            
        except Exception as e:
            logger.error(f"Error analyzing content change: {str(e)}")
            return {
                'message': f"Content updated in {monitor.name}: {monitor.current_value[:100]}...",
                'type': 'info',
                'change_type': 'content_update',
                'confidence': 0.6
            }
    
    async def cleanup_old_data(self):
        """Clean up old data to prevent database bloat"""
        db = SessionLocal()
        try:
            # Delete old notifications (older than 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            old_notifications = db.query(Notification).filter(
                Notification.created_at < cutoff_date
            ).delete()
            
            logger.info(f"Cleaned up {old_notifications} old notifications")
            
            # You could also clean up old summary data here
            # For now, we'll keep all summaries
            
            db.commit()
        
        except Exception as e:
            logger.error(f"Error in cleanup_old_data: {str(e)}")
        finally:
            db.close()
    
    def _schedule_existing_monitors(self):
        """Schedule all existing active monitors"""
        db = SessionLocal()
        try:
            monitors = db.query(Monitor).filter(Monitor.is_active == True).all()
            logger.info(f"Found {len(monitors)} active monitors to schedule")
            
            for monitor in monitors:
                logger.info(f"Scheduling monitor: {monitor.name} with interval {monitor.check_interval} minutes")
                self.add_monitor_job(monitor)
            
            logger.info(f"Successfully scheduled {len(monitors)} monitors")
        except Exception as e:
            logger.error(f"Error scheduling existing monitors: {str(e)}")
        finally:
            db.close()
    
    def add_monitor_job(self, monitor: Monitor):
        """Add a monitor to the scheduler"""
        if not self.running:
            logger.warning(f"Scheduler not running, cannot add monitor {monitor.name}")
            return
        
        job_id = f"monitor_{monitor.id}"
        
        # Remove existing job if it exists
        if job_id in self.monitor_jobs:
            logger.info(f"Removing existing job for monitor {monitor.name}")
            self.scheduler.remove_job(job_id)
        
        # Calculate interval in seconds (check_interval is already in seconds)
        interval_seconds = monitor.check_interval  # Already in seconds
        logger.info(f"Adding job for monitor {monitor.name} with {interval_seconds} second interval")
        
        # Add new job
        job = self.scheduler.add_job(
            self.check_single_monitor,
            IntervalTrigger(seconds=interval_seconds),
            args=[monitor.id],
            id=job_id,
            replace_existing=True
        )
        
        self.monitor_jobs[monitor.id] = job
        logger.info(f"Successfully scheduled monitor {monitor.name} with {monitor.check_interval} minute interval")
    
    def remove_monitor_job(self, monitor_id: str):
        """Remove a monitor from the scheduler"""
        job_id = f"monitor_{monitor_id}"
        
        if job_id in self.monitor_jobs:
            self.scheduler.remove_job(job_id)
            del self.monitor_jobs[monitor_id]
            logger.info(f"Removed monitor job {job_id}")
    
    def update_monitor_job(self, monitor: Monitor):
        """Update a monitor job in the scheduler"""
        if monitor.is_active:
            self.add_monitor_job(monitor)
        else:
            self.remove_monitor_job(monitor.id)
    
    async def check_single_monitor(self, monitor_id: str):
        """Check a single monitor by ID"""
        logger.info(f"Starting scheduled check for monitor {monitor_id}")
        db = SessionLocal()
        try:
            monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
            if monitor and monitor.is_active:
                logger.info(f"Checking monitor: {monitor.name} ({monitor.url})")
                await self.check_monitor(monitor, db)
                logger.info(f"Completed scheduled check for monitor {monitor.name}")
            else:
                logger.warning(f"Monitor {monitor_id} not found or not active, removing job")
                # Remove job if monitor is no longer active
                self.remove_monitor_job(monitor_id)
        except Exception as e:
            logger.error(f"Error checking single monitor {monitor_id}: {str(e)}")
        finally:
            db.close()
    
    def get_job_info(self) -> List[dict]:
        """Get information about all scheduled jobs"""
        jobs = []
        for monitor_id, job in self.monitor_jobs.items():
            jobs.append({
                "monitor_id": monitor_id,
                "job_id": job.id,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs
    
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self.running

    def _extract_price_from_value(self, value: str, item_type: str = None) -> Optional[str]:
        """Extract price from monitor value with improved logic"""
        if not value:
            return None
        
        # Special handling for Bitcoin
        if item_type == 'crypto' and ('bitcoin' in value.lower() or 'btc' in value.lower()):
            # Look for Bitcoin price specifically
            bitcoin_price = self._extract_bitcoin_price(value)
            if bitcoin_price:
                return bitcoin_price
        
        # Enhanced price patterns
        price_patterns = [
            # Item-specific patterns (highest priority) - handle multi-line
            r'Bitcoin.*?[\$€£¥₹]?\s*[\d,]+\.?\d*',
            r'BTC.*?[\$€£¥₹]?\s*[\d,]+\.?\d*',
            r'ETH.*?[\$€£¥₹]?\s*[\d,]+\.?\d*',
            r'Ethereum.*?[\$€£¥₹]?\s*[\d,]+\.?\d*',
            # Price labels (high priority)
            r'Price:\s*[\$€£¥₹]?\s*[\d,]+\.?\d*',
            r'Current Price:\s*[\$€£¥₹]?\s*[\d,]+\.?\d*',
            r'Value:\s*[\$€£¥₹]?\s*[\d,]+\.?\d*',
            # Major currency symbols with numbers (medium priority)
            r'[\$€£¥₹]\s*[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*(?:USD|EUR|GBP|JPY|INR|BTC|ETH)',
            # Large numbers that could be prices (for crypto)
            r'[\$€£¥₹]?\s*[\d,]{1,3}(?:,\d{3})*\.?\d*',
            # Numbers with currency codes
            r'[\d,]+\.?\d*\s*(?:USD|EUR|GBP|JPY|INR)',
            # Simple price patterns (lowest priority)
            r'[\$€£¥₹]\s*[\d,]+\.?\d*',
            r'[\d,]+\.?\d*'
        ]
        
        found_prices = []
        
        for pattern_index, pattern in enumerate(price_patterns):
            matches = re.finditer(pattern, value, re.IGNORECASE)
            for match in matches:
                price_text = match.group(0).strip()
                
                # Clean and validate the price
                cleaned_price = self._clean_price_text(price_text)
                if cleaned_price and self._is_valid_price(cleaned_price, item_type):
                    # Extract numeric value for sorting
                    numeric_value = self._extract_numeric_value(cleaned_price)
                    found_prices.append({
                        'price': cleaned_price,
                        'position': match.start(),
                        'raw_text': price_text,
                        'numeric_value': numeric_value,
                        'pattern_priority': len(price_patterns) - pattern_index  # Higher priority for earlier patterns
                    })
        
        if found_prices:
            # For crypto, prioritize larger numbers and higher priority patterns
            if item_type == 'crypto':
                # Filter out very small numbers that are likely not prices
                valid_prices = [p for p in found_prices if self._is_likely_crypto_price(p['price'])]
                if valid_prices:
                    # Sort by pattern priority first, then by numeric value (largest first), then by position
                    valid_prices.sort(key=lambda x: (x['pattern_priority'], x['numeric_value'], -x['position']), reverse=True)
                    return valid_prices[0]['price']
            
            # For other types, sort by pattern priority first, then by position
            found_prices.sort(key=lambda x: (x['pattern_priority'], x['position']), reverse=True)
            return found_prices[0]['price']
        
        return None
    
    def _extract_bitcoin_price(self, value: str) -> Optional[str]:
        """Extract Bitcoin price specifically, handling multi-line content"""
        try:
            lines = value.split('\n')
            
            for i, line in enumerate(lines):
                # Look for Bitcoin/BTC in the line
                if re.search(r'bitcoin|btc', line, re.IGNORECASE):
                    # Check the next line for a price
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        price_match = re.search(r'[\$€£¥₹]\s*[\d,]+\.?\d*', next_line)
                        if price_match:
                            price_text = price_match.group(0).strip()
                            cleaned_price = self._clean_price_text(price_text)
                            if cleaned_price and self._is_valid_price(cleaned_price, 'crypto'):
                                return cleaned_price
                    
                    # Also check the current line for price
                    price_match = re.search(r'[\$€£¥₹]\s*[\d,]+\.?\d*', line)
                    if price_match:
                        price_text = price_match.group(0).strip()
                        cleaned_price = self._clean_price_text(price_text)
                        if cleaned_price and self._is_valid_price(cleaned_price, 'crypto'):
                            return cleaned_price
            
            return None
            
        except Exception as e:
            print(f"Error extracting Bitcoin price: {e}")
            return None
    
    def _extract_numeric_value(self, price_text: str) -> float:
        """Extract numeric value from price text for comparison"""
        try:
            # Remove currency symbols and commas
            numeric_part = re.sub(r'[^\d.]', '', price_text)
            return float(numeric_part)
        except ValueError:
            return 0.0
    
    def _clean_price_text(self, price_text: str) -> str:
        """Clean and normalize price text"""
        if not price_text:
            return ""
        
        # Remove extra whitespace
        cleaned = price_text.strip()
        
        # Ensure proper formatting
        if cleaned.startswith('$') and not cleaned[1:].replace(',', '').replace('.', '').isdigit():
            # Remove $ if it's not followed by a number
            cleaned = cleaned[1:].strip()
        
        return cleaned
    
    def _is_valid_price(self, price_text: str, item_type: str = None) -> bool:
        """Check if a price text is valid"""
        if not price_text:
            return False
        
        # Remove currency symbols and commas
        numeric_part = re.sub(r'[^\d.]', '', price_text)
        
        try:
            price_value = float(numeric_part)
            
            # For crypto, expect larger numbers
            if item_type == 'crypto':
                return price_value > 1  # Most crypto prices are > $1
            
            # For stocks, expect reasonable ranges
            elif item_type == 'stock':
                return 0.01 <= price_value <= 10000  # Reasonable stock price range
            
            # For products, expect reasonable ranges
            elif item_type == 'product':
                return 0.01 <= price_value <= 100000  # Reasonable product price range
            
            return True
            
        except ValueError:
            return False
    
    def _is_likely_crypto_price(self, price_text: str) -> bool:
        """Check if a price is likely to be a crypto price (not a small number)"""
        try:
            numeric_part = re.sub(r'[^\d.]', '', price_text)
            price_value = float(numeric_part)
            
            # Crypto prices are typically > $10 for major cryptocurrencies
            # Bitcoin and Ethereum are usually > $1000
            return price_value > 10
            
        except ValueError:
            return False

# Create global instance
scheduler = SchedulerService() 