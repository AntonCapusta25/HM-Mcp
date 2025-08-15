#!/usr/bin/env python3
"""
Ultra-Enhanced Form Submitter with DrissionPage
Handles form submission with superior Cloudflare bypass and reliability
"""

import asyncio
import time
import logging
import random
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import re

# DrissionPage imports
from DrissionPage import ChromiumPage, SessionPage
from DrissionPage.common import Actions
from DrissionPage.errors import ElementNotFoundError, PageDisconnectedError

from enhanced_form_scraper import EnhancedFormScraper

logger = logging.getLogger(__name__)

class EnhancedFormSubmitter:
    def __init__(self, use_stealth: bool = True, headless: bool = True):
        self.scraper = EnhancedFormScraper(use_stealth=use_stealth, headless=headless)
        self.browser_page = None
        self.session_page = None
        self.submission_history = []
        
    async def validate_submission_enhanced(self, url: str, field_data: Dict[str, str], 
                                         form_index: int = 0) -> Dict[str, Any]:
        """Enhanced validation with intelligent field matching"""
        try:
            # Get form structure using enhanced scraper
            form_result = await self.scraper.extract_form_fields_enhanced(url, form_index)
            
            if not form_result.get('success'):
                return {
                    'valid': False,
                    'issues': [f"Cannot validate: {form_result.get('error')}"],
                    'method_used': form_result.get('method_used', 'unknown')
                }
            
            fields = form_result.get('fields', [])
            issues = []
            warnings = []
            suggestions = []
            
            # Create field lookup maps
            fields_by_name = {f.get('name'): f for f in fields if f.get('name')}
            fields_by_id = {f.get('id'): f for f in fields if f.get('id')}
            fields_by_identifier = {f.get('identifier'): f for f in fields if f.get('identifier')}
            
            # Check each form field
            for field in fields:
                field_id = field.get('identifier') or field.get('id') or field.get('name')
                field_name = field.get('name')
                field_label = field.get('label', field_id)
                field_type = field.get('type', '')
                
                # Find provided value using multiple strategies
                provided_value = self._find_field_value(field, field_data)
                
                # Validate required fields
                if field.get('required', False):
                    if not provided_value or not provided_value.strip():
                        issues.append(f"Required field missing or empty: {field_label}")
                        suggestions.append(f"Provide value for field: {field_id or field_name}")
                
                # Validate field values if provided
                if provided_value:
                    field_issues = self._validate_field_value_enhanced(field, provided_value)
                    issues.extend(field_issues)
            
            # Check for unknown provided fields
            known_field_keys = set()
            for field in fields:
                if field.get('name'):
                    known_field_keys.add(field.get('name'))
                if field.get('id'):
                    known_field_keys.add(field.get('id'))
                if field.get('identifier'):
                    known_field_keys.add(field.get('identifier'))
            
            for provided_key in field_data.keys():
                if provided_key not in known_field_keys:
                    # Try fuzzy matching
                    best_match = self._find_fuzzy_field_match(provided_key, known_field_keys)
                    if best_match:
                        suggestions.append(f"Unknown field '{provided_key}' - did you mean '{best_match}'?")
                    else:
                        warnings.append(f"Unknown field provided: {provided_key}")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'warnings': warnings,
                'suggestions': suggestions,
                'fields_checked': len(fields),
                'data_provided': len(field_data),
                'method_used': form_result.get('method_used', 'unknown')
            }
            
        except Exception as e:
            return {
                'valid': False,
                'issues': [f"Validation error: {str(e)}"]
            }
    
    def _find_field_value(self, field: Dict[str, Any], field_data: Dict[str, str]) -> str:
        """Find field value using multiple matching strategies"""
        # Try exact matches first
        for key in [field.get('id'), field.get('name'), field.get('identifier')]:
            if key and key in field_data:
                return field_data[key]
        
        # Try fuzzy matching
        field_keys = [k for k in [field.get('id'), field.get('name'), field.get('identifier')] if k]
        for field_key in field_keys:
            if field_key:
                fuzzy_match = self._find_fuzzy_field_match(field_key, field_data.keys())
                if fuzzy_match:
                    return field_data[fuzzy_match]
        
        return ""
    
    def _find_fuzzy_field_match(self, target: str, candidates: List[str]) -> Optional[str]:
        """Find fuzzy match for field names"""
        target_lower = target.lower()
        
        # Exact match (case insensitive)
        for candidate in candidates:
            if candidate.lower() == target_lower:
                return candidate
        
        # Partial match
        for candidate in candidates:
            if target_lower in candidate.lower() or candidate.lower() in target_lower:
                return candidate
        
        # Word-based matching
        target_words = set(re.findall(r'\w+', target_lower))
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            candidate_words = set(re.findall(r'\w+', candidate.lower()))
            common_words = target_words.intersection(candidate_words)
            if common_words:
                score = len(common_words) / max(len(target_words), len(candidate_words))
                if score > best_score and score > 0.5:  # At least 50% match
                    best_score = score
                    best_match = candidate
        
        return best_match
    
    def _validate_field_value_enhanced(self, field: Dict[str, Any], value: str) -> List[str]:
        """Enhanced field value validation"""
        issues = []
        field_type = field.get('type', '').lower()
        field_label = field.get('label', field.get('identifier', 'field'))
        
        # Email validation
        if field_type == 'email' or 'email' in field.get('name', '').lower():
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                issues.append(f"{field_label}: Invalid email format")
        
        # URL validation
        elif field_type == 'url':
            url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if not re.match(url_pattern, value):
                issues.append(f"{field_label}: Invalid URL format")
        
        # Phone validation
        elif field_type == 'tel' or any(word in field.get('name', '').lower() for word in ['phone', 'tel', 'mobile']):
            # More flexible phone validation
            phone_clean = re.sub(r'[^\d+]', '', value)
            if len(phone_clean) < 7 or len(phone_clean) > 15:
                issues.append(f"{field_label}: Invalid phone number length")
        
        # Number validation
        elif field_type in ['number', 'range']:
            try:
                float(value)
            except ValueError:
                issues.append(f"{field_label}: Must be a valid number")
        
        # Length validation
        validation_rules = field.get('validation_rules', [])
        for rule in validation_rules:
            if rule.startswith('max_length:'):
                max_length = int(rule.split(':')[1])
                if len(value) > max_length:
                    issues.append(f"{field_label}: Too long (max {max_length} characters)")
            elif rule.startswith('min_length:'):
                min_length = int(rule.split(':')[1])
                if len(value) < min_length:
                    issues.append(f"{field_label}: Too short (min {min_length} characters)")
            elif rule.startswith('pattern:'):
                pattern = rule.split(':', 1)[1]
                try:
                    if not re.match(pattern, value):
                        issues.append(f"{field_label}: Does not match required pattern")
                except re.error:
                    pass  # Skip invalid patterns
        
        # Select field validation
        if field.get('tag') == 'select':
            valid_options = [opt.get('value', '') for opt in field.get('options', [])]
            if value not in valid_options and valid_options:
                issues.append(f"{field_label}: Invalid option '{value}'. Valid options: {', '.join(valid_options[:5])}")
        
        return issues
    
    async def submit_form_enhanced(self, url: str, field_data: Dict[str, str], 
                                 form_index: int = 0, max_retries: int = 3) -> Dict[str, Any]:
        """Enhanced form submission with intelligent method selection"""
        
        # Validate first
        validation = await self.validate_submission_enhanced(url, field_data, form_index)
        if not validation.get('valid'):
            return {
                'success': False,
                'error': 'Form validation failed',
                'validation': validation
            }
        
        # Determine best submission method
        submission_method = await self._determine_submission_method(url, validation)
        
        # Attempt submission with retries
        for attempt in range(max_retries):
            try:
                if submission_method == 'http_session':
                    result = await self._submit_with_session(url, field_data, form_index, attempt)
                else:
                    result = await self._submit_with_browser(url, field_data, form_index, attempt)
                
                # Record submission attempt
                self._record_submission_attempt(url, field_data, result, attempt + 1)
                
                if result.get('success'):
                    result['validation'] = validation
                    result['attempts'] = attempt + 1
                    result['method_used'] = submission_method
                    return result
                elif attempt < max_retries - 1:
                    # Wait before retry with exponential backoff
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Submission attempt {attempt + 1} failed, retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                    
                    # Switch methods on failure
                    if submission_method == 'http_session':
                        submission_method = 'browser_automation'
                        logger.info("Switching to browser automation for retry")
                
            except Exception as e:
                logger.warning(f"Submission attempt {attempt + 1} failed with error: {str(e)}")
                if attempt == max_retries - 1:
                    return {
                        'success': False,
                        'error': f"All {max_retries} submission attempts failed. Final error: {str(e)}",
                        'validation': validation,
                        'attempts': max_retries
                    }
        
        return {
            'success': False,
            'error': f'All {max_retries} submission attempts failed',
            'validation': validation,
            'attempts': max_retries
        }
    
    async def _determine_submission_method(self, url: str, validation: Dict[str, Any]) -> str:
        """Determine the best submission method based on validation results"""
        validation_method = validation.get('method_used', 'browser_automation')
        
        # If validation used HTTP session successfully, prefer that for speed
        if validation_method == 'http_session':
            return 'http_session'
        
        # For complex cases, use browser automation
        return 'browser_automation'
    
    async def _submit_with_session(self, url: str, field_data: Dict[str, str], 
                                 form_index: int, attempt: int) -> Dict[str, Any]:
        """Submit form using HTTP session for speed"""
        try:
            if not self.session_page:
                self.session_page = self.scraper._get_session_page()
            
            # Get form details
            self.session_page.get(url)
            forms = self.session_page.eles('tag:form')
            
            if form_index >= len(forms):
                return {'success': False, 'error': f'Form index {form_index} not found'}
            
            form = forms[form_index]
            form_action = self.scraper._get_form_action(form, self.session_page.url)
            form_method = (form.attr('method') or 'POST').upper()
            
            # Build submission data
            submission_data = {}
            
            # Include hidden fields
            hidden_fields = form.eles('css:input[type="hidden"]')
            for hidden in hidden_fields:
                name = hidden.attr('name')
                value = hidden.attr('value') or ''
                if name:
                    submission_data[name] = value
            
            # Add provided data with intelligent field matching
            form_fields = self.scraper._extract_field_details_from_element(form, self.session_page)
            for field in form_fields:
                provided_value = self.scraper._find_field_value(field, field_data)
                if provided_value:
                    field_name = field.get('name') or field.get('id')
                    if field_name:
                        submission_data[field_name] = provided_value
            
            # Submit form
            if form_method == 'GET':
                self.session_page.get(form_action, params=submission_data)
            else:
                self.session_page.post(form_action, data=submission_data)
            
            return await self._process_submission_response(self.session_page, url)
            
        except Exception as e:
            return {'success': False, 'error': f'Session submission failed: {str(e)}'}
    
    async def _submit_with_browser(self, url: str, field_data: Dict[str, str], 
                                 form_index: int, attempt: int) -> Dict[str, Any]:
        """Submit form using browser automation for complex cases"""
        try:
            if not self.browser_page:
                self.browser_page = await self.scraper._get_browser_page()
            
            # Navigate to page and handle challenges
            self.browser_page.get(url)
            await self.scraper._handle_cloudflare_challenges(self.browser_page)
            
            # Wait for page to be fully loaded
            await asyncio.sleep(2)
            
            # Find form
            forms = self.browser_page.eles('tag:form')
            if form_index >= len(forms):
                return {'success': False, 'error': f'Form index {form_index} not found'}
            
            form = forms[form_index]
            
            # Fill form fields
            fill_results = await self._fill_form_fields_intelligently(form, field_data)
            
            if fill_results['errors']:
                logger.warning(f"Field filling errors: {fill_results['errors']}")
            
            # Handle form submission
            submission_result = await self._handle_form_submission(form, self.browser_page)
            
            # Combine results
            result = await self._process_submission_response(self.browser_page, url)
            result['field_filling'] = fill_results
            result['submission_method'] = submission_result.get('method', 'unknown')
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': f'Browser submission failed: {str(e)}'}
    
    async def _fill_form_fields_intelligently(self, form, field_data: Dict[str, str]) -> Dict[str, Any]:
        """Fill form fields with intelligent field matching"""
        filled_fields = []
        errors = []
        warnings = []
        
        # Get all form fields
        field_elements = form.eles('tag:input, tag:textarea, tag:select')
        
        for element in field_elements:
            try:
                field_type = element.attr('type') or 'text'
                
                # Skip non-input fields
                if field_type.lower() in ['hidden', 'submit', 'button', 'image', 'reset']:
                    continue
                
                # Find value for this field
                field_info = {
                    'tag': element.tag,
                    'type': field_type,
                    'name': element.attr('name') or '',
                    'id': element.attr('id') or '',
                    'identifier': element.attr('id') or element.attr('name') or ''
                }
                
                value = self.scraper._find_field_value(field_info, field_data)
                
                if value:
                    success = await self._fill_single_field(element, value, field_info)
                    if success:
                        filled_fields.append({
                            'field': field_info['identifier'] or field_info['name'],
                            'value': value[:50] + '...' if len(value) > 50 else value
                        })
                    else:
                        errors.append(f"Failed to fill field: {field_info['identifier'] or field_info['name']}")
                
            except Exception as e:
                errors.append(f"Error processing field: {str(e)}")
        
        return {
            'filled_fields': filled_fields,
            'fields_filled': len(filled_fields),
            'errors': errors,
            'warnings': warnings
        }
    
    async def _fill_single_field(self, element, value: str, field_info: Dict[str, Any]) -> bool:
        """Fill a single form field with proper handling for different field types"""
        try:
            field_type = field_info.get('type', '').lower()
            tag = field_info.get('tag', '').lower()
            
            # Handle different field types
            if tag == 'select':
                # Handle select dropdowns
                options = element.eles('tag:option')
                for option in options:
                    option_value = option.attr('value') or option.text
                    if option_value.lower() == value.lower() or option.text.lower() == value.lower():
                        option.click()
                        await asyncio.sleep(0.5)
                        return True
                return False
                
            elif field_type == 'checkbox':
                # Handle checkboxes
                if value.lower() in ['true', '1', 'yes', 'on', 'checked']:
                    if not element.states.is_checked:
                        element.click()
                        await asyncio.sleep(0.3)
                return True
                
            elif field_type == 'radio':
                # Handle radio buttons
                radio_name = element.attr('name')
                if radio_name:
                    radio_group = element.parent().eles(f'css:input[name="{radio_name}"]')
                    for radio in radio_group:
                        radio_value = radio.attr('value') or ''
                        if radio_value.lower() == value.lower():
                            radio.click()
                            await asyncio.sleep(0.3)
                            return True
                return False
                
            elif field_type == 'file':
                # Handle file uploads (placeholder - would need actual file path)
                logger.warning(f"File upload field detected but not implemented: {field_info['identifier']}")
                return False
                
            else:
                # Handle text inputs, textareas, etc.
                element.clear()
                await asyncio.sleep(0.1)
                
                # Type value with human-like typing
                await self._human_like_typing(element, value)
                return True
                
        except Exception as e:
            logger.error(f"Error filling field {field_info.get('identifier', 'unknown')}: {str(e)}")
            return False
    
    async def _human_like_typing(self, element, text: str):
        """Type text with human-like delays and patterns"""
        element.click()  # Focus the element
        await asyncio.sleep(0.1)
        
        # Type with random delays between characters
        for char in text:
            element.input(char)
            # Random delay between 50-150ms
            await asyncio.sleep(random.uniform(0.05, 0.15))
    
    async def _handle_form_submission(self, form, browser_page) -> Dict[str, Any]:
        """Handle form submission with multiple strategies"""
        try:
            # Strategy 1: Look for submit button
            submit_buttons = form.eles('css:input[type="submit"], button[type="submit"], button')
            
            if submit_buttons:
                submit_button = submit_buttons[0]
                logger.info(f"Clicking submit button: {submit_button.attr('value') or submit_button.text}")
                submit_button.click()
                await asyncio.sleep(2)
                return {'method': 'submit_button', 'success': True}
            
            # Strategy 2: Submit form directly
            logger.info("No submit button found, submitting form directly")
            form.submit()
            await asyncio.sleep(2)
            return {'method': 'form_submit', 'success': True}
            
        except Exception as e:
            # Strategy 3: Press Enter in the last input field
            try:
                inputs = form.eles('css:input[type="text"], input[type="email"], textarea')
                if inputs:
                    last_input = inputs[-1]
                    last_input.click()
                    last_input.input('\n')  # Press Enter
                    await asyncio.sleep(2)
                    return {'method': 'enter_key', 'success': True}
            except:
                pass
            
            return {'method': 'failed', 'success': False, 'error': str(e)}
    
    async def _process_submission_response(self, page, original_url: str) -> Dict[str, Any]:
        """Process response after form submission"""
        try:
            current_url = page.url
            
            # Wait for any redirects or page changes
            await asyncio.sleep(3)
            final_url = page.url
            
            # Get page content
            if hasattr(page, 'html'):
                content = page.html
            else:
                content = page.raw_data.decode('utf-8', errors='ignore')
            
            # Analyze response
            success_indicators = self._detect_success_indicators(content, final_url, original_url)
            error_indicators = self._detect_error_indicators(content)
            
            # Determine success
            submission_success = (
                len(error_indicators) == 0 and
                len(success_indicators) > 0
            )
            
            # Extract confirmation message
            confirmation = self._extract_confirmation_message(content, success_indicators)
            
            result = {
                'success': submission_success,
                'original_url': original_url,
                'final_url': final_url,
                'url_changed': final_url != original_url,
                'success_indicators': success_indicators,
                'error_indicators': error_indicators,
                'confirmation': confirmation
            }
            
            if submission_success:
                result['message'] = confirmation or 'Form submitted successfully'
            else:
                error_msg = 'Form submission may have failed'
                if error_indicators:
                    error_msg = f"Errors detected: {', '.join(error_indicators)}"
                elif not success_indicators:
                    error_msg = 'No success confirmation detected'
                result['error'] = error_msg
                result['message'] = error_msg
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Response processing failed: {str(e)}'
            }
    
    def _detect_success_indicators(self, content: str, final_url: str, original_url: str) -> List[str]:
        """Detect success indicators in response"""
        indicators = []
        content_lower = content.lower()
        
        # URL change often indicates success
        if final_url != original_url:
            indicators.append('url_changed')
        
        # Text-based success indicators
        success_phrases = [
            'thank you', 'submitted successfully', 'application received',
            'form submitted', 'your application', 'confirmation',
            'we have received', 'successfully sent', 'message sent',
            'registration complete', 'account created', 'saved successfully',
            'submission successful', 'application submitted', 'success'
        ]
        
        for phrase in success_phrases:
            if phrase in content_lower:
                indicators.append(f'success_text_{phrase.replace(" ", "_")}')
        
        # Look for confirmation numbers
        confirmation_patterns = [
            r'confirmation\s*#?\s*:?\s*([a-zA-Z0-9]+)',
            r'reference\s*#?\s*:?\s*([a-zA-Z0-9]+)',
            r'application\s*#?\s*:?\s*([a-zA-Z0-9]+)',
            r'ticket\s*#?\s*:?\s*([a-zA-Z0-9]+)'
        ]
        
        for pattern in confirmation_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                indicators.append('confirmation_number_found')
                break
        
        return indicators
    
    def _detect_error_indicators(self, content: str) -> List[str]:
        """Detect error indicators in response"""
        indicators = []
        content_lower = content.lower()
        
        # Text-based error indicators
        error_phrases = [
            'error', 'failed', 'invalid', 'required field',
            'missing information', 'please correct', 'try again',
            'submission failed', 'could not submit', 'problem occurred',
            'validation error', 'form error', 'please fix'
        ]
        
        for phrase in error_phrases:
            if phrase in content_lower:
                indicators.append(f'error_text_{phrase.replace(" ", "_")}')
        
        # HTML error indicators
        if 'class="error"' in content or 'class="invalid"' in content:
            indicators.append('html_error_classes')
        
        return indicators
    
    def _extract_confirmation_message(self, content: str, success_indicators: List[str]) -> str:
        """Extract confirmation message from response"""
        # Simple extraction - look for common confirmation text
        content_lower = content.lower()
        
        if 'thank you' in content_lower:
            # Try to extract a reasonable thank you message
            lines = content.split('\n')
            for line in lines:
                line_clean = line.strip()
                if 'thank you' in line_clean.lower() and len(line_clean) < 200:
                    return line_clean
        
        # Default based on indicators
        if success_indicators:
            return "Form appears to have been submitted successfully"
        
        return ""
    
    def _record_submission_attempt(self, url: str, field_data: Dict[str, str], 
                                 result: Dict[str, Any], attempt: int):
        """Record submission attempt for debugging and analytics"""
        record = {
            'timestamp': time.time(),
            'url': url,
            'attempt': attempt,
            'success': result.get('success', False),
            'error': result.get('error'),
            'method': result.get('method_used', 'unknown'),
            'field_count': len(field_data)
        }
        
        self.submission_history.append(record)
        
        # Keep only last 100 records
        if len(self.submission_history) > 100:
            self.submission_history = self.submission_history[-100:]
    
    async def close(self):
        """Clean up resources"""
        await self.scraper.close()
        
        if self.browser_page:
            try:
                self.browser_page.quit()
            except:
                pass
        
        if self.session_page:
            try:
                self.session_page.close()
            except:
                pass

# Example usage
async def test_enhanced_submitter():
    """Test the enhanced form submitter"""
    submitter = EnhancedFormSubmitter(use_stealth=True, headless=False)
    
    try:
        test_url = "https://httpbin.org/forms/post"
        test_data = {
            "custname": "John Doe",
            "custtel": "555-1234", 
            "custemail": "john@example.com",
            "comments": "This is a test submission"
        }
        
        print("Validating form data...")
        validation = await submitter.validate_submission_enhanced(test_url, test_data)
        print(f"Validation result: {validation}")
        
        if validation.get('valid'):
            print("\nSubmitting form...")
            result = await submitter.submit_form_enhanced(test_url, test_data)
            print(f"Submission result: {result}")
        
    finally:
        await submitter.close()

if __name__ == "__main__":
    asyncio.run(test_enhanced_submitter())
