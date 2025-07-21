import asyncio
from typing import Optional, Dict, Any, Tuple
import time
import json
from anthropic import Anthropic
from openai import OpenAI
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.ai_client = None
        self.executor = ThreadPoolExecutor(max_workers=4)  # Limit concurrent AI calls
            
        # Initialize AI client
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            self.ai_client = boto3.client(
                'bedrock-runtime',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
    
    def _get_summarization_prompt(self, content: str, title: str = None, question: str = None) -> str:
        """Generate a comprehensive prompt for content summarization"""
        
        if question:
            # Prioritize answering the user's question first
            base_prompt = f"""
You are an AI assistant helping users understand web content. A user has asked a specific question about this webpage.

{"Title: " + title if title else ""}

Content:
{content}

User Question: {question}

IMPORTANT: You MUST provide your response in this EXACT format with these EXACT section headers:

## Answer to User Question:
[Provide a direct answer to the user's question based on the content above. If the answer cannot be found in the content, clearly state that.]

## Summary of {title if title else "the webpage"}:
[Provide a comprehensive summary of the webpage content, including key insights and notable details]

CRITICAL: Do NOT embed the answer within the summary. The answer must be in its own separate section.
"""
        else:
            # Standard summary without question
            base_prompt = f"""
You are an AI assistant helping users understand web content. Please analyze the following webpage content and provide a helpful summary.

{"Title: " + title if title else ""}

Content:
{content}

Please provide:
1. A concise summary of the main points (2-3 sentences)
2. Key insights or important information
3. Any notable details that stand out
"""
        
        return base_prompt
    
    def _get_content_analysis_prompt(self, current_content: str, previous_content: str) -> str:
        """Generate prompt for analyzing content changes"""
        return f"""
You are monitoring web content for changes. Please analyze the differences between the current and previous content.

Previous Content:
{previous_content}

Current Content:
{current_content}

Please provide:
1. A summary of what changed
2. The significance of these changes
3. Whether this change is worth notifying the user about

Be concise and focus on meaningful changes, not minor formatting differences.
"""
    
    def _ai_completion_sync(self, prompt: str) -> str:
        """Synchronous AI completion for background processing"""
        try:
            # Prepare the request body
            body = json.dumps({
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7,
                "anthropic_version": "bedrock-2023-05-31"
            })
            
            # Make the API call
            response = self.ai_client.invoke_model(
                modelId=settings.get_model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            return content
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS Bedrock error: {error_code} - {error_message}")
            raise Exception(f"AWS Bedrock error: {error_message}")
        except Exception as e:
            logger.error(f"Error in AI completion: {str(e)}")
            raise
    
    async def _ai_completion(self, prompt: str) -> str:
        """Asynchronous AI completion with background processing"""
        try:
            # Run the blocking AI call in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                self._ai_completion_sync, 
                prompt
            )
            return result
        except Exception as e:
            logger.error(f"Error in async AI completion: {str(e)}")
            raise
    
    async def summarize_content(
        self, 
        content: str, 
        title: str = None, 
        question: str = None, 
        provider: str = None
    ) -> Tuple[str, str, float]:
        """
        Summarize webpage content and optionally answer a question
        Returns: (summary, answer, processing_time)
        """
        start_time = time.time()
        
        prompt = self._get_summarization_prompt(content, title, question)
        
        try:
            if self.ai_client:
                response = await self._ai_completion(prompt)
            else:
                raise ValueError("AI client not configured")
            
            processing_time = time.time() - start_time
            
            # Split response into summary and answer if question was asked
            if question:
                # Parse the new format with clear sections
                if "## Answer to User Question:" in response and "## Summary of" in response:
                    # Extract answer and summary from the structured response
                    answer_start = response.find("## Answer to User Question:") + len("## Answer to User Question:")
                    summary_start = response.find("## Summary of")
                    
                    answer = response[answer_start:summary_start].strip()
                    summary = response[summary_start:].strip()
                elif "Answer to User Question:" in response:
                    # Try alternative format without ##
                    answer_start = response.find("Answer to User Question:") + len("Answer to User Question:")
                    # Look for next section or end of response
                    next_section = response.find("##", answer_start)
                    if next_section != -1:
                        answer = response[answer_start:next_section].strip()
                        summary = response[next_section:].strip()
                    else:
                        answer = response[answer_start:].strip()
                        summary = ""
                else:
                    # Try to extract answer from within the summary text
                    # Look for patterns that might indicate the answer
                    answer_indicators = [
                        f"XRP ($",
                        f"Ethereum ($",
                        f"Bitcoin ($",
                        f"price is $",
                        f"costs $",
                        f"priced at $",
                        f"worth $"
                    ]
                    
                    answer = ""
                    summary = response.strip()
                    
                    # Try to find a direct answer in the text
                    for indicator in answer_indicators:
                        if indicator in response:
                            # Extract the sentence containing the price
                            start_idx = response.find(indicator)
                            end_idx = response.find(".", start_idx)
                            if end_idx == -1:
                                end_idx = response.find("\n", start_idx)
                            if end_idx == -1:
                                end_idx = len(response)
                            
                            answer = response[start_idx:end_idx].strip()
                            # Remove the answer from the summary
                            summary = response.replace(answer, "").strip()
                            break
            else:
                summary = response.strip()
                answer = ""
            
            return summary, answer, processing_time
            
        except Exception as e:
            logger.error(f"Error in AI summarization: {str(e)}")
            processing_time = time.time() - start_time
            return f"Error generating summary: {str(e)}", "", processing_time
    
    async def analyze_content_changes(self, previous_content: str, current_content: str, monitor_info: dict = None) -> str:
        """
        Analyze content changes and provide intelligent insights
        """
        try:
            # Prepare the prompt based on monitor type
            if monitor_info and monitor_info.get('monitor_type') == 'item_search':
                item_name = monitor_info.get('item_name', 'item')
                item_type = monitor_info.get('item_type', 'general')
                
                prompt = f"""
                Analyze the changes in content for a {item_type} monitor tracking "{item_name}".
                
                Previous content: {previous_content[:2000]}
                
                Current content: {current_content[:2000]}
                
                Please provide:
                1. **Summary of Changes**: What specifically changed about {item_name}?
                2. **Price/Market Data**: Extract any price, market cap, volume, or percentage changes
                3. **Significance**: How significant are these changes? (Low/Medium/High)
                4. **Action Required**: Should the user be notified? (Yes/No)
                5. **Key Metrics**: List any important numbers or percentages found
                
                Format your response as a structured analysis with clear sections.
                """
            else:
                prompt = f"""
                Analyze the changes between these two content versions:
                
                Previous content: {previous_content[:2000]}
                
                Current content: {current_content[:2000]}
                
                Please provide:
                1. **Summary of Changes**: What has changed?
                2. **Significance**: How significant are these changes? (Low/Medium/High)
                3. **Action Required**: Should the user be notified? (Yes/No)
                4. **Key Points**: List the most important changes
                
                Format your response as a structured analysis with clear sections.
                """
            
            if self.ai_client:
                response = await self._ai_completion(prompt)
                return response
            else:
                logger.warning("AI service not available for content analysis")
                return "Content analysis not available - AI service not configured"
            
        except Exception as e:
            logger.error(f"Error analyzing content changes: {str(e)}")
            return f"Error analyzing changes: {str(e)}"
    
    def get_available_providers(self) -> list[str]:
        """Get list of available AI providers"""
        providers = []
        if self.ai_client:
            providers.append("aws_bedrock")
        return providers
    
    def is_provider_available(self, provider: str) -> bool:
        """Check if a specific AI provider is available"""
        return provider in self.get_available_providers()
    
    def __del__(self):
        """Cleanup thread pool executor"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

# Create global instance
ai_service = AIService() 