import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import random
import time
from typing import Optional, Dict, Any, Tuple, List
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class PerplexityStyleScraper:
    """Advanced scraper with Perplexity-like capabilities"""
    
    def __init__(self):
        self.session = None
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # Advanced headers that mimic real browsers
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        }
        
        # Known search patterns for different types of content
        self.search_patterns = {
            'crypto': {
                'patterns': [
                    r'bitcoin|btc|ethereum|eth|cardano|ada|solana|sol|polkadot|dot|binance|bnb|ripple|xrp',
                    r'[\$€£¥₹]\s*[\d,]+\.?\d*',
                    r'[\d,]+\.?\d*\s*(?:USD|EUR|GBP|JPY|INR|BTC|ETH)',
                    r'Price:\s*[\$€£¥₹]?\s*[\d,]+\.?\d*',
                    r'Current Price:\s*[\$€£¥₹]?\s*[\d,]+\.?\d*',
                    r'Bitcoin.*?[\$€£¥₹]?\s*[\d,]+\.?\d*',
                    r'BTC.*?[\$€£¥₹]?\s*[\d,]+\.?\d*',
                    r'ETH.*?[\$€£¥₹]?\s*[\d,]+\.?\d*'
                ],
                'sites': ['coingecko.com', 'cryptonews.com', 'coinmarketcap.com', 'binance.com', 'crypto.com'],
                'selectors': ['.price', '.value', '[data-price]', '.crypto-price', '.coin-price', '.current-price', '.price-value']
            },
            'stock': {
                'patterns': [
                    r'[\$€£¥₹]\s*[\d,]+\.?\d*',
                    r'[\d,]+\.?\d*\s*(?:USD|EUR|GBP|JPY|INR)',
                    r'stock|share|trading|market cap',
                    r'Price:\s*[\$€£¥₹]?\s*[\d,]+\.?\d*',
                    r'Current Price:\s*[\$€£¥₹]?\s*[\d,]+\.?\d*'
                ],
                'sites': ['finance.yahoo.com', 'marketwatch.com', 'investing.com', 'bloomberg.com'],
                'selectors': ['.price', '.value', '[data-price]', '.stock-price', '.current-price', '.price-value']
            },
            'product': {
                'patterns': [
                    r'[\$€£¥₹]\s*[\d,]+\.?\d*',
                    r'[\d,]+\.?\d*\s*(?:USD|EUR|GBP|JPY|INR)',
                    r'product|item|buy|purchase|price',
                    r'Price:\s*[\$€£¥₹]?\s*[\d,]+\.?\d*',
                    r'Cost:\s*[\$€£¥₹]?\s*[\d,]+\.?\d*'
                ],
                'sites': ['amazon.com', 'ebay.com', 'walmart.com', 'target.com'],
                'selectors': ['.price', '.product-price', '[data-price]', '.sale-price', '.current-price']
            },
            'news': {
                'patterns': [r'headline|title|article|news'],
                'sites': ['news.ycombinator.com', 'reddit.com', 'techcrunch.com', 'theverge.com'],
                'selectors': ['.title', '.headline', '.article-title', 'h1', 'h2']
            }
        }
    
    async def _get_session(self):
        """Get or create aiohttp session with rotating user agents"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)
            headers = self.base_headers.copy()
            headers['User-Agent'] = random.choice(self.user_agents)
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def search_for_item(self, url: str, item_name: str, item_type: str = 'auto') -> Dict[str, Any]:
        """
        Search for a specific item on a webpage using Perplexity-like techniques
        
        Args:
            url: Website URL to search
            item_name: Name of the item to search for (e.g., "Bitcoin", "AAPL", "iPhone 15")
            item_type: Type of item ('crypto', 'stock', 'product', 'news', 'auto')
        
        Returns:
            Dict with found information
        """
        try:
            # Determine item type if auto
            if item_type == 'auto':
                item_type = self._detect_item_type(item_name)
            
            # Get content with advanced techniques
            content, html = await self._fetch_with_advanced_techniques(url)
            
            # Search for the specific item
            results = await self._search_content_for_item(content, html, item_name, item_type)
            
            return {
                'success': True,
                'item_name': item_name,
                'item_type': item_type,
                'url': url,
                'found_data': results,
                'search_strategy': 'perplexity_style'
            }
            
        except Exception as e:
            logger.error(f"Error searching for {item_name} on {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'item_name': item_name,
                'url': url
            }
    
    async def _fetch_with_advanced_techniques(self, url: str) -> Tuple[str, str]:
        """Fetch content using advanced techniques to bypass blocking"""
        
        # Strategy 1: Try with rotating user agents
        for attempt in range(3):
            try:
                session = await self._get_session()
                
                # Add random delay to avoid rate limiting
                await asyncio.sleep(random.uniform(1, 3))
                
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        content = self._extract_clean_content(soup)
                        return content, html
                    
                    elif response.status == 403:
                        # Try with different headers
                        headers = self.base_headers.copy()
                        headers['User-Agent'] = random.choice(self.user_agents)
                        headers['Referer'] = 'https://www.google.com/'
                        
                        async with session.get(url, headers=headers) as retry_response:
                            if retry_response.status == 200:
                                html = await retry_response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                content = self._extract_clean_content(soup)
                                return content, html
                    
                    elif response.status == 429:
                        # Rate limited - wait longer
                        await asyncio.sleep(random.uniform(5, 10))
                        continue
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < 2:
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
        
        # Strategy 2: Try alternative URLs for the same site
        alternative_urls = self._get_alternative_urls(url)
        for alt_url in alternative_urls:
            try:
                session = await self._get_session()
                async with session.get(alt_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        content = self._extract_clean_content(soup)
                        return content, html
            except Exception:
                continue
        
        raise Exception(f"Unable to fetch content from {url} after multiple attempts")
    
    def _get_alternative_urls(self, url: str) -> List[str]:
        """Get alternative URLs for the same site"""
        parsed = urlparse(url)
        domain = parsed.netloc
        
        alternatives = []
        
        # Common alternative paths
        if 'coinmarketcap.com' in domain:
            alternatives = [
                f"https://{domain}/trending-cryptocurrencies",
                f"https://{domain}/cryptocurrencies",
                f"https://{domain}/markets"
            ]
        elif 'finance.yahoo.com' in domain:
            alternatives = [
                f"https://{domain}/quote",
                f"https://{domain}/markets",
                f"https://{domain}/screener"
            ]
        elif 'github.com' in domain:
            alternatives = [
                f"https://{domain}/trending",
                f"https://{domain}/explore",
                f"https://{domain}/topics"
            ]
        
        return alternatives
    
    async def _search_content_for_item(self, content: str, html: str, item_name: str, item_type: str) -> Dict[str, Any]:
        """
        Search for a specific item in the content using advanced techniques
        """
        try:
            # Normalize item name for better matching
            item_name_lower = item_name.lower().strip()
            item_variations = self._get_item_variations(item_name, item_type)
            
            # Get search patterns for this item type
            patterns = self.search_patterns.get(item_type, {}).get('patterns', [])
            selectors = self.search_patterns.get(item_type, {}).get('selectors', [])
        
            results = {
                'item_name': item_name,
                'item_type': item_type,
                'found_matches': [],
                'price_info': None,
                'context': [],
                'confidence': 0
            }
        
            # Strategy 1: Direct text search for item name
            for variation in item_variations:
                if variation.lower() in content.lower():
                    matches = self._find_all_matches(content, variation)
                    for match in matches:
                        results['found_matches'].append({
                            'type': 'direct_match',
                            'text': match['text'],
                            'context': match['context'],
                            'confidence': 0.9
                        })
        
            # Strategy 2: Price extraction for financial items
            if item_type in ['crypto', 'stock', 'product']:
                price_info = self._extract_price_information(content, item_name, item_type)
                if price_info:
                    results['price_info'] = price_info
                    results['confidence'] = max(results['confidence'], 0.8)
        
            # Strategy 3: CSS selector search
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                for selector in selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        element_text = element.get_text().strip()
                        if element_text and any(var.lower() in element_text.lower() for var in item_variations):
                            results['found_matches'].append({
                                'type': 'css_selector',
                                'text': element_text,
                                'selector': selector,
                                'confidence': 0.7
                            })
            
            # Strategy 4: Pattern-based search
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    match_text = match.group(0)
                    # Check if this match is near our item name
                    if self._is_match_near_item(content, match.start(), item_variations):
                        results['found_matches'].append({
                            'type': 'pattern_match',
                            'text': match_text,
                            'pattern': pattern,
                            'confidence': 0.6
                        })
        
            # Strategy 5: Market data extraction for crypto/stocks
            if item_type in ['crypto', 'stock']:
                market_data = self._extract_market_data(content, item_name)
                if market_data:
                    results['market_data'] = market_data
                    results['confidence'] = max(results['confidence'], 0.7)
            
            # Remove duplicates and sort by confidence
            unique_matches = []
            seen_texts = set()
            for match in results['found_matches']:
                if match['text'] not in seen_texts:
                    unique_matches.append(match)
                    seen_texts.add(match['text'])
            
            results['found_matches'] = sorted(unique_matches, key=lambda x: x['confidence'], reverse=True)
            
            # Calculate overall confidence
            if results['found_matches']:
                results['confidence'] = max(results['confidence'], max(match['confidence'] for match in results['found_matches']))
        
            return results
            
        except Exception as e:
            logger.error(f"Error searching for item {item_name}: {str(e)}")
            return {
                'item_name': item_name,
                'item_type': item_type,
                'error': str(e),
                'confidence': 0
            }
    
    def _get_item_variations(self, item_name: str, item_type: str) -> List[str]:
        """Get variations of an item name for better matching"""
        variations = [item_name]
        
        # Common abbreviations and variations
        if item_type == 'crypto':
            crypto_variations = {
                'bitcoin': ['btc', 'bitcoin', 'bit coin'],
                'ethereum': ['eth', 'ethereum'],
                'cardano': ['ada', 'cardano'],
                'solana': ['sol', 'solana'],
                'polkadot': ['dot', 'polkadot'],
                'binance coin': ['bnb', 'binance', 'binance coin'],
                'ripple': ['xrp', 'ripple']
            }
            
            item_lower = item_name.lower()
            for crypto, vars in crypto_variations.items():
                if crypto in item_lower or any(var in item_lower for var in vars):
                    variations.extend(vars)
                    break
        
        elif item_type == 'stock':
            # Stock ticker variations
            if len(item_name) <= 5:  # Likely a ticker
                variations.append(item_name.upper())
                variations.append(item_name.lower())
        
        return list(set(variations))  # Remove duplicates
    
    def _is_match_near_item(self, content: str, match_pos: int, item_variations: List[str], context_chars: int = 200) -> bool:
        """Check if a match is near any item variation"""
        start = max(0, match_pos - context_chars)
        end = min(len(content), match_pos + context_chars)
        context = content[start:end].lower()
        
        return any(var.lower() in context for var in item_variations)
    
    def _extract_price_information(self, content: str, item_name: str, item_type: str) -> Optional[Dict[str, Any]]:
        """Extract price information for financial items"""
        try:
            # Enhanced price patterns for better extraction
            price_patterns = [
                # Major currency symbols with numbers
                r'[\$€£¥₹]\s*[\d,]+\.?\d*',
                r'[\d,]+\.?\d*\s*(?:USD|EUR|GBP|JPY|INR|BTC|ETH)',
                # Price labels
                r'Price:\s*[\$€£¥₹]?\s*[\d,]+\.?\d*',
                r'Current Price:\s*[\$€£¥₹]?\s*[\d,]+\.?\d*',
                r'Value:\s*[\$€£¥₹]?\s*[\d,]+\.?\d*',
                # Item-specific patterns
                r'Bitcoin.*?[\$€£¥₹]?\s*[\d,]+\.?\d*',
                r'BTC.*?[\$€£¥₹]?\s*[\d,]+\.?\d*',
                r'ETH.*?[\$€£¥₹]?\s*[\d,]+\.?\d*',
                # Large numbers that could be prices (for crypto)
                r'[\$€£¥₹]?\s*[\d,]{1,3}(?:,\d{3})*\.?\d*',
                # Numbers with currency codes
                r'[\d,]+\.?\d*\s*(?:USD|EUR|GBP|JPY|INR)',
                # Simple price patterns
                r'[\$€£¥₹]\s*[\d,]+\.?\d*',
                r'[\d,]+\.?\d*'
            ]
            
            item_variations = self._get_item_variations(item_name, item_type)
            found_prices = []
            
            for pattern in price_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    price_text = match.group(0)
                    
                    # Clean and validate the price
                    cleaned_price = self._clean_price_text(price_text)
                    if cleaned_price and self._is_valid_price(cleaned_price, item_type):
                        # Check if this price is near our item
                        if self._is_match_near_item(content, match.start(), item_variations):
                            found_prices.append({
                                'price': cleaned_price,
                                'position': match.start(),
                                'pattern': pattern,
                                'raw_text': price_text
                            })
            
            if found_prices:
                # Sort by position and get the most relevant one
                found_prices.sort(key=lambda x: x['position'])
                
                # For crypto, prefer larger numbers (likely to be the actual price)
                if item_type == 'crypto':
                    # Filter out very small numbers that are likely not prices
                    valid_prices = [p for p in found_prices if self._is_likely_crypto_price(p['price'])]
                    if valid_prices:
                        return {
                            'price': valid_prices[0]['price'],
                            'all_prices': [p['price'] for p in valid_prices],
                            'confidence': 0.9
                        }
                
                return {
                    'price': found_prices[0]['price'],
                    'all_prices': [p['price'] for p in found_prices],
                    'confidence': 0.8
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting price for {item_name}: {str(e)}")
            return None
    
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
    
    def _is_valid_price(self, price_text: str, item_type: str) -> bool:
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
            
            # Crypto prices are typically > $1, and major ones are much higher
            return price_value > 1
            
        except ValueError:
            return False
    
    def _extract_context_around_matches(self, content: str, search_term: str, context_chars: int = 100) -> List[Dict[str, str]]:
        """Extract context around matches"""
        matches = []
        content_lower = content.lower()
        search_lower = search_term.lower()
        
        start = 0
        while True:
            pos = content_lower.find(search_lower, start)
            if pos == -1:
                break
            
            # Extract context
            context_start = max(0, pos - context_chars)
            context_end = min(len(content), pos + len(search_term) + context_chars)
            context = content[context_start:context_end]
            
            matches.append({
                'match': search_term,
                'context': context,
                'position': pos
            })
            
            start = pos + 1
        
        return matches
    
    def _get_related_terms(self, item_name: str, item_type: str) -> List[str]:
        """Get related terms for semantic search"""
        related_terms = []
        
        if item_type == 'crypto':
            # Common cryptocurrency terms
            crypto_terms = {
                'bitcoin': ['btc', 'bitcoin', 'crypto', 'digital currency'],
                'ethereum': ['eth', 'ethereum', 'smart contract', 'defi'],
                'cardano': ['ada', 'cardano', 'blockchain'],
                'solana': ['sol', 'solana', 'blockchain']
            }
            
            for crypto, terms in crypto_terms.items():
                if crypto.lower() in item_name.lower():
                    related_terms.extend(terms)
        
        elif item_type == 'stock':
            # Common stock market terms
            stock_terms = ['stock', 'share', 'trading', 'market', 'price', 'volume']
            related_terms.extend(stock_terms)
        
        return related_terms
    
    def _detect_item_type(self, item_name: str) -> str:
        """Auto-detect item type based on name"""
        item_lower = item_name.lower()
        
        # Cryptocurrency detection
        crypto_keywords = ['bitcoin', 'btc', 'ethereum', 'eth', 'cardano', 'ada', 'solana', 'sol', 'crypto']
        if any(keyword in item_lower for keyword in crypto_keywords):
            return 'crypto'
        
        # Stock detection (common stock symbols)
        stock_patterns = [r'^[A-Z]{1,5}$', r'stock', r'share']
        if any(re.search(pattern, item_lower) for pattern in stock_patterns):
            return 'stock'
        
        # Product detection
        product_keywords = ['iphone', 'samsung', 'laptop', 'phone', 'product']
        if any(keyword in item_lower for keyword in product_keywords):
            return 'product'
        
        return 'news'  # Default to news
    
    def _extract_clean_content(self, soup: BeautifulSoup) -> str:
        """Extract clean content from BeautifulSoup object"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'advertisement']):
            element.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _extract_price_from_element(self, element) -> Optional[str]:
        """Extract price information from an HTML element"""
        # Look for price patterns in the element text
        text = element.get_text()
        price_match = re.search(r'\$[\d,]+\.?\d*', text)
        if price_match:
            return price_match.group()
        
        # Look for price in data attributes
        price_attrs = ['data-price', 'data-value', 'data-cost']
        for attr in price_attrs:
            price = element.get(attr)
            if price:
                return price
        
        return None
    
    def _extract_market_data(self, content: str, item_name: str) -> Dict[str, Any]:
        """Extract market data for crypto/stocks"""
        market_data = {
            'price': None,
            'market_cap': None,
            'volume': None,
            'change_24h': None,
            'change_7d': None
        }
        
        # Price extraction
        price_patterns = [
            r'\$([\d,]+\.?\d*)',
            r'Price[:\s]*\$([\d,]+\.?\d*)',
            r'Value[:\s]*\$([\d,]+\.?\d*)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                market_data['price'] = f"${match.group(1)}"
                break
        
        # Market cap extraction
        cap_patterns = [
            r'Market Cap[:\s]*\$([\d,]+\.?\d*[KMB]?)',
            r'Cap[:\s]*\$([\d,]+\.?\d*[KMB]?)',
            r'\$([\d,]+\.?\d*[KMB]?)\s*Market Cap'
        ]
        
        for pattern in cap_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                market_data['market_cap'] = f"${match.group(1)}"
                break
        
        # Volume extraction
        volume_patterns = [
            r'Volume[:\s]*\$([\d,]+\.?\d*[KMB]?)',
            r'24h Vol[:\s]*\$([\d,]+\.?\d*[KMB]?)',
            r'\$([\d,]+\.?\d*[KMB]?)\s*Volume'
        ]
        
        for pattern in volume_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                market_data['volume'] = f"${match.group(1)}"
                break
        
        # Change percentage extraction
        change_patterns = [
            r'(\+|-)?(\d+\.?\d*)%',
            r'Change[:\s]*(\+|-)?(\d+\.?\d*)%',
            r'24h[:\s]*(\+|-)?(\d+\.?\d*)%'
        ]
        
        for pattern in change_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                sign = match.group(1) or ''
                value = match.group(2)
                market_data['change_24h'] = f"{sign}{value}%"
                break
        
        return market_data

    def _find_all_matches(self, content: str, search_term: str, context_chars: int = 100) -> List[Dict[str, str]]:
        """Find all matches of a search term with context"""
        matches = []
        search_term_lower = search_term.lower()
        content_lower = content.lower()
        
        start = 0
        while True:
            pos = content_lower.find(search_term_lower, start)
            if pos == -1:
                break
            
            # Extract context around the match
            context_start = max(0, pos - context_chars)
            context_end = min(len(content), pos + len(search_term) + context_chars)
            context = content[context_start:context_end]
            
            # Extract the actual match text
            match_text = content[pos:pos + len(search_term)]
            
            matches.append({
                'text': match_text,
                'context': context,
                'position': pos
            })
            
            start = pos + 1
        
        return matches

class ScraperService:
    def __init__(self):
        self.perplexity_scraper = PerplexityStyleScraper()
        self.session = None
        self.headers = {
            'User-Agent': settings.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        }
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self.headers
            )
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
        await self.perplexity_scraper.close_session()
    
    async def search_for_specific_item(self, url: str, item_name: str, item_type: str = 'auto') -> Dict[str, Any]:
        """
        Search for a specific item using Perplexity-like techniques
        
        Args:
            url: Website URL
            item_name: Name of item to search for (e.g., "Bitcoin", "AAPL", "iPhone 15")
            item_type: Type of item ('crypto', 'stock', 'product', 'news', 'auto')
        
        Returns:
            Dict with search results
        """
        return await self.perplexity_scraper.search_for_item(url, item_name, item_type)
    
    async def fetch_page_content(self, url: str) -> Tuple[str, str, str]:
        """
        Fetch webpage content and extract title, content, and raw HTML
        Returns: (title, cleaned_content, raw_html)
        """
        try:
            session = await self._get_session()
            
            async with session.get(url) as response:
                if response.status != 200:
                    if response.status == 403:
                        raise Exception(
                            f"Access forbidden (HTTP 403). This website blocks automated requests.\n\n"
                            f"Try these websites instead:\n"
                            f"• https://en.wikipedia.org/wiki/Artificial_intelligence\n"
                            f"• https://github.com/trending\n"
                            f"• https://stackoverflow.com/questions\n"
                            f"• https://dev.to\n"
                            f"• https://httpbin.org/html\n"
                            f"• https://example.com"
                        )
                    elif response.status == 404:
                        raise Exception(f"Page not found (HTTP 404). Please check the URL is correct.")
                    elif response.status == 429:
                        raise Exception(f"Rate limited (HTTP 429). This website is blocking too many requests. Please try again later.")
                    elif response.status == 503:
                        raise Exception(f"Service unavailable (HTTP 503). The website is temporarily down. Please try again later.")
                    else:
                        raise Exception(f"HTTP {response.status}: {response.reason}")
                
                # Check content length
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > settings.MAX_CONTENT_LENGTH:
                    raise Exception(f"Content too large: {content_length} bytes")
                
                html = await response.text()
                
                # Parse HTML
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract title
                title = self._extract_title(soup)
                
                # Extract main content
                content = self._extract_content(soup)
                
                return title, content, html
                
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Try meta title
        meta_title = soup.find('meta', property='og:title')
        if meta_title:
            return meta_title.get('content', '').strip()
        
        # Try h1 as fallback
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "Untitled Page"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from page"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # Try to find main content area
        content_selectors = [
            'article',
            'main',
            '.content',
            '.main-content',
            '.post-content',
            '.entry-content',
            '.article-content',
            'div[role="main"]'
        ]
        
        content_text = ""
        for selector in content_selectors:
            content_area = soup.select_one(selector)
            if content_area:
                content_text = content_area.get_text()
                break
        
        # Fallback to body content
        if not content_text:
            body = soup.find('body')
            if body:
                content_text = body.get_text()
        
        # Clean up the text
        content_text = re.sub(r'\s+', ' ', content_text).strip()
        
        return content_text
    
    async def extract_element_content(self, url: str, css_selector: str = None, xpath_selector: str = None) -> str:
        """
        Extract content from a specific element using CSS selector or XPath
        Returns: element content as string
        """
        try:
            _, _, html = await self.fetch_page_content(url)
            soup = BeautifulSoup(html, 'html.parser')
            
            if css_selector:
                element = soup.select_one(css_selector)
                if element:
                    return element.get_text().strip()
            
            # XPath support would require lxml or selenium
            # For now, focus on CSS selectors
            if xpath_selector:
                logger.warning("XPath selectors not yet supported, falling back to CSS")
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting element from {url}: {str(e)}")
            return ""
    
    def detect_price_selectors(self, soup: BeautifulSoup) -> list[str]:
        """
        Detect common price selectors on a page
        Returns: list of potential CSS selectors for prices
        """
        price_patterns = [
            r'\$[\d,]+\.?\d*',
            r'€[\d,]+\.?\d*',
            r'£[\d,]+\.?\d*',
            r'¥[\d,]+\.?\d*',
            r'₹[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*(?:USD|EUR|GBP|JPY|INR)',
        ]
        
        potential_selectors = []
        
        # Common price class/id patterns
        price_attributes = [
            'price', 'cost', 'amount', 'value', 'money',
            'sale-price', 'regular-price', 'current-price',
            'product-price', 'item-price', 'total-price'
        ]
        
        for attr in price_attributes:
            # Check for classes
            elements = soup.find_all(class_=re.compile(attr, re.I))
            for element in elements:
                if element.get('class'):
                    potential_selectors.append(f".{'.'.join(element.get('class'))}")
            
            # Check for IDs
            elements = soup.find_all(id=re.compile(attr, re.I))
            for element in elements:
                if element.get('id'):
                    potential_selectors.append(f"#{element.get('id')}")
        
        return list(set(potential_selectors))
    
    async def detect_product_info(self, url: str) -> Dict[str, Any]:
        """
        Detect product information from a webpage
        Returns: Dict with product details
        """
        try:
            title, content, html = await self.fetch_page_content(url)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract product information
            product_info = {
                'title': title,
                'prices': [],
                'images': [],
                'description': '',
                'availability': '',
                'rating': ''
            }
            
            # Find prices
            price_selectors = self.detect_price_selectors(soup)
            for selector in price_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text().strip()
                        price = self.extract_price_from_text(text)
                        if price:
                            product_info['prices'].append({
                                'value': price,
                                'text': text,
                                'selector': selector
                            })
                except Exception:
                    continue
            
            # Find images
            img_elements = soup.find_all('img')
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if src:
                    product_info['images'].append({
                        'src': src,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', '')
                    })
            
            # Find description
            desc_selectors = [
                '.description', '.product-description', '.item-description',
                '.summary', '.product-summary', '.details'
            ]
            for selector in desc_selectors:
                element = soup.select_one(selector)
                if element:
                    product_info['description'] = element.get_text().strip()
                    break
            
            return product_info
            
        except Exception as e:
            logger.error(f"Error detecting product info from {url}: {str(e)}")
            return {}
    
    def extract_price_from_text(self, text: str) -> Optional[float]:
        """
        Extract price from text
        Returns: price as float or None
        """
        # Common price patterns
        price_patterns = [
            r'\$([\d,]+\.?\d*)',
            r'€([\d,]+\.?\d*)',
            r'£([\d,]+\.?\d*)',
            r'¥([\d,]+\.?\d*)',
            r'₹([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:USD|EUR|GBP|JPY|INR)',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    return float(price_str)
                except ValueError:
                    continue
        
        return None
    
    def normalize_content(self, content: str) -> str:
        """
        Normalize content for comparison
        Returns: normalized content string
        """
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common noise
        noise_patterns = [
            r'cookie|privacy|terms|conditions',
            r'newsletter|subscribe|sign up',
            r'advertisement|ad|sponsored',
            r'©|copyright|all rights reserved'
        ]
        
        for pattern in noise_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        return content.strip()

# Create global instance
scraper_service = ScraperService() 