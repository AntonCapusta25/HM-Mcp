#!/usr/bin/env python3
"""
Ultra-Robust Form Submitter
Handles form submission with maximum reliability and barrier bypass
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import json
import re

logger = logging.getLogger(__name__)

class UltraFormSubmitter:
    def __init__(self):
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with persistent cookies"""
        if self.session is None or self.session.closed:
            # Create session with cookie jar for maintaining state
            jar = aiohttp.CookieJar(unsafe=True)
            connector = aiohttp.TCPConnector(
                limit=100,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Cache-Control': 'max-age=0'
            }
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                headers=headers,
                cookie_jar=jar,
                timeout=aiohttp.ClientTimeout(total=30, connect=10)
            )
            
        return self.session
    
    async def validate_submission(self, url: str, field_data: Dict[str, str], form_index: int = 0) -> Dict[str, Any]:
        """Validate form data before submission"""
        try:
            from form_scraper import UltraFormScraper
            scraper = UltraFormScraper()
            
            # Get form structure
            form_result = await scraper.extract_form_fields_ultra(url, form_index)
            
            if not form_result.get('success'):
                return {
                    'valid': False,
                    'issues': [f"Cannot validate: {form_result.get('error')}"]
                }
            
            fields = form_result.get('fields', [])
            issues = []
            warnings = []
            
            # Check required fields
            for field in fields:
                field_id = field.get('identifier')
                field_name = field.get('name')
                field_label = field.get('label', field_id)
                
                # Check if required field is provided
                if field.get('required', False):
                    if field_id not in field_data and field_name not in field_data:
                        issues.append(f"Required field missing: {field_label}")
                    elif not (field_data.get(field_id, '').strip() or field_data.get(field_name, '').strip()):
                        issues.append(f"Required field empty: {field_label}")
                
                # Validate field format
                field_value = field_data.get(field_id) or field_data.get(field_name, '')
                if field_value:
                    field_issues = self._validate_field_value(field, field_value)
                    issues.extend(field_issues)
            
            # Check for unknown fields
            known_fields = set()
            for field in fields:
                if field.get('identifier'):
                    known_fields.add(field.get('identifier'))
                if field.get('name'):
                    known_fields.add(field.get('name'))
            
            for provided_field in field_data.keys():
                if provided_field not in known_fields:
                    warnings.append(f"Unknown field provided: {provided_field}")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'warnings': warnings,
                'fields_checked': len(fields),
                'data_provided': len(field_data)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'issues': [f"Validation error: {str(e)}"]
            }
    
    def _validate_field_value(self, field: Dict[str, Any], value: str) -> List[str]:
        """Validate a single field value against its constraints"""
        issues = []
        field_type = field.get('type', '').lower()
        field_label = field.get('label', field.get('identifier', 'field'))
        
        # Email validation
        if field_type == 'email':
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                issues.append(f"{field_label}: Invalid email format")
        
        # URL validation
        elif field_type == 'url':
            url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if not re.match(url_pattern, value):
                issues.append(f"{field_label}: Invalid URL format")
        
        # Phone validation
        elif field_type == 'tel' or 'phone' in field.get('name', '').lower():
            # Basic phone validation (very permissive)
            phone_pattern = r'[\d\s\(\)\-\+\.]+'
            if not re.match(phone_pattern, value):
                issues.append(f"{field_label}: Invalid phone format")
        
        # Length validation
        max_length = field.get('max_length')
        if max_length and len(value) > int(max_length):
            issues.append(f"{field_label}: Too long (max {max_length} characters)")
        
        min_length = field.get('min_length')
        if min_length and len(value) < int(min_length):
            issues.append(f"{field_label}: Too short (min {min_length} characters)")
        
        # Pattern validation
        pattern = field.get('pattern')
        if pattern:
            try:
                if not re.match(pattern, value):
                    issues.append(f"{field_label}: Does not match required pattern")
            except re.error:
                pass  # Invalid regex pattern, skip validation
        
        # Select field validation
        if field.get('tag') == 'select':
            valid_options = [opt.get('value', '') for opt in field.get('options', [])]
            if value not in valid_options:
                issues.append(f"{field_label}: Invalid option selected")
        
        return issues
    
    async def submit_form_ultra(self, url: str, field_data: Dict[str, str], form_index: int = 0) -> Dict[str, Any]:
        """Submit form with ultra-robust error handling and retry logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                result = await self._attempt_form_submission(url, field_data, form_index)
                
                if result.get('success'):
                    return result
                elif attempt < max_retries - 1:
                    # Wait before retry
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    logger.info(f"Retrying submission (attempt {attempt + 2}/{max_retries})")
                else:
                    return result
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Submission attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return {
                        'success': False,
                        'error': f"All submission attempts failed. Final error: {str(e)}",
                        'attempts': max_retries
                    }
        
        return {
            'success': False,
            'error': 'Maximum retry attempts exceeded',
            'attempts': max_retries
        }
    
    async def _attempt_form_submission(self, url: str, field_data: Dict[str, str], form_index: int = 0) -> Dict[str, Any]:
        """Single attempt at form submission"""
        try:
            session = await self._get_session()
            
            # First, get the form page to extract form details and CSRF tokens
            async with session.get(url, allow_redirects=True) as response:
                if response.status not in [200, 201]:
                    return {
                        'success': False,
                        'error': f"Cannot access form page: HTTP {response.status}",
                        'status_code': response.status
                    }
                
                form_html = await response.text()
                actual_url = str(response.url)
            
            # Parse the form
            soup = BeautifulSoup(form_html, 'html.parser')
            forms = soup.find_all('form')
            
            if not forms:
                return {
                    'success': False,
                    'error': 'No forms found on page'
                }
            
            if form_index >= len(forms):
                return {
                    'success': False,
                    'error': f'Form index {form_index} not found. Page has {len(forms)} forms.'
                }
            
            form = forms[form_index]
            
            # Extract form action and method
            form_action = form.get('action', '')
            if not form_action:
                form_action = actual_url
            elif not form_action.startswith('http'):
                form_action = urljoin(actual_url, form_action)
            
            form_method = form.get('method', 'POST').upper()
            form_enctype = form.get('enctype', 'application/x-www-form-urlencoded')
            
            # Build form data
            submission_data = {}
            
            # Include hidden fields (important for CSRF tokens, etc.)
            hidden_fields = form.find_all('input', {'type': 'hidden'})
            for hidden in hidden_fields:
                name = hidden.get('name')
                value = hidden.get('value', '')
                if name:
                    submission_data[name] = value
            
            # Add provided field data
            submission_data.update(field_data)
            
            # Set additional headers for form submission
            submit_headers = {
                'Referer': actual_url,
                'Origin': f"{urlparse(actual_url).scheme}://{urlparse(actual_url).netloc}",
                'X-Requested-With': 'XMLHttpRequest',  # Some forms expect this
            }
            
            if form_enctype == 'multipart/form-data':
                submit_headers['Content-Type'] = 'multipart/form-data'
            else:
                submit_headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
            # Submit the form
            if form_method == 'GET':
                async with session.get(form_action, params=submission_data, headers=submit_headers) as submit_response:
                    return await self._process_submission_response(submit_response, actual_url)
            else:
                if form_enctype == 'multipart/form-data':
                    # Use FormData for multipart
                    data = aiohttp.FormData()
                    for key, value in submission_data.items():
                        data.add_field(key, str(value))
                    async with session.post(form_action, data=data, headers=submit_headers) as submit_response:
                        return await self._process_submission_response(submit_response, actual_url)
                else:
                    # Regular form submission
                    async with session.post(form_action, data=submission_data, headers=submit_headers) as submit_response:
                        return await self._process_submission_response(submit_response, actual_url)
            
        except Exception as e:
            logger.error(f"Form submission error: {str(e)}")
            return {
                'success': False,
                'error': f"Submission failed: {str(e)}"
            }
    
    async def _process_submission_response(self, response, original_url: str) -> Dict[str, Any]:
        """Process the response from form submission"""
        try:
            response_text = await response.text()
            response_url = str(response.url)
            
            # Build redirect chain
            redirect_chain = []
            if hasattr(response, 'history'):
                for redirect in response.history:
                    redirect_chain.append({
                        'url': str(redirect.url),
                        'status': redirect.status
                    })
            
            # Analyze response for success indicators
            success_indicators = self._detect_success_indicators(response_text, response.status)
            error_indicators = self._detect_error_indicators(response_text, response.status)
            
            # Determine if submission was successful
            submission_success = (
                response.status in [200, 201, 302, 303] and
                len(error_indicators) == 0 and
                len(success_indicators) > 0
            )
            
            # Extract confirmation message
            confirmation = self._extract_confirmation_message(response_text, success_indicators)
            
            # Gather evidence of submission
            evidence = {
                'success_indicators': success_indicators,
                'error_indicators': error_indicators,
                'response_contains_form': 'form' in response_text.lower(),
                'response_length': len(response_text),
                'redirected': response_url != original_url,
                'new_page_detected': any(word in response_text.lower() for word in ['thank you', 'received', 'submitted', 'confirmation'])
            }
            
            result = {
                'success': submission_success,
                'status_code': response.status,
                'response_url': response_url,
                'redirect_chain': redirect_chain,
                'confirmation': confirmation,
                'evidence': evidence
            }
            
            if not submission_success:
                error_message = "Form submission may have failed"
                if error_indicators:
                    error_message = f"Errors detected: {', '.join(error_indicators)}"
                elif response.status >= 400:
                    error_message = f"HTTP error {response.status}"
                elif not success_indicators:
                    error_message = "No success confirmation detected"
                
                result['error'] = error_message
                result['message'] = error_message
            else:
                result['message'] = confirmation or "Form submitted successfully"
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Response processing failed: {str(e)}",
                'status_code': getattr(response, 'status', 0)
            }
    
    def _detect_success_indicators(self, response_text: str, status_code: int) -> List[str]:
        """Detect indicators that the form was submitted successfully"""
        indicators = []
        text_lower = response_text.lower()
        
        # Status code indicators
        if status_code in [200, 201]:
            indicators.append('http_success_status')
        elif status_code in [302, 303]:
            indicators.append('redirect_after_submit')
        
        # Text-based indicators
        success_phrases = [
            'thank you', 'submitted successfully', 'application received',
            'form submitted', 'your application', 'confirmation',
            'we have received', 'successfully sent', 'message sent',
            'registration complete', 'account created', 'saved successfully',
            'submission successful', 'application submitted'
        ]
        
        for phrase in success_phrases:
            if phrase in text_lower:
                indicators.append(f'success_text:{phrase.replace(" ", "_")}')
        
        # Look for confirmation numbers or IDs
        confirmation_patterns = [
            r'confirmation\s*#?\s*:?\s*([a-zA-Z0-9]+)',
            r'reference\s*#?\s*:?\s*([a-zA-Z0-9]+)',
            r'application\s*#?\s*:?\s*([a-zA-Z0-9]+)',
            r'ticket\s*#?\s*:?\s*([a-zA-Z0-9]+)'
        ]
        
        for pattern in confirmation_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            if matches:
                indicators.append(f'confirmation_number_found')
        
        return indicators
    
    def _detect_error_indicators(self, response_text: str, status_code: int) -> List[str]:
        """Detect indicators that the form submission failed"""
        indicators = []
        text_lower = response_text.lower()
        
        # Status code indicators
        if status_code >= 400:
            indicators.append(f'http_error_{status_code}')
        
        # Text-based error indicators
        error_phrases = [
            'error', 'failed', 'invalid', 'required field',
            'missing information', 'please correct', 'try again',
            'submission failed', 'could not submit', 'problem occurred',
            'validation error', 'form error', 'please fix'
        ]
        
        for phrase in error_phrases:
            if phrase in text_lower:
                indicators.append(f'error_text:{phrase.replace(" ", "_")}')
        
        # Look for form validation errors
        if 'class="error"' in response_text or 'class="invalid"' in response_text:
            indicators.append('validation_error_detected')
        
        # Check if the same form is still present (might indicate failed submission)
        if '<form' in response_text:
            indicators.append('form_still_present')
        
        return indicators
    
    def _extract_confirmation_message(self, response_text: str, success_indicators: List[str]) -> str:
        """Extract confirmation message from response"""
        soup = BeautifulSoup(response_text, 'html.parser')
        
        # Look for elements that might contain confirmation
        confirmation_selectors = [
            '.success', '.confirmation', '.thank-you', '.message',
            '#success', '#confirmation', '#thank-you', '#message',
            '[class*="success"]', '[class*="confirm"]', '[class*="thank"]'
        ]
        
        for selector in confirmation_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if text and len(text) < 500:  # Reasonable message length
                        return text
            except:
                continue
        
        # Look for thank you or confirmation text in the page
        text_lower = response_text.lower()
        if 'thank you' in text_lower:
            # Try to extract the thank you message
            soup_text = soup.get_text()
            lines = [line.strip() for line in soup_text.split('\n') if line.strip()]
            for line in lines:
                if 'thank you' in line.lower() and len(line) < 200:
                    return line
        
        # Default message based on indicators
        if success_indicators:
            return "Form appears to have been submitted successfully"
        
        return ""
    
    async def close(self):
        """Clean up resources"""
        if self.session and not self.session.closed:
            await self.session.close()