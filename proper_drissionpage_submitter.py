#!/usr/bin/env python3
"""
Bulletproof Form Submitter - Never Crashes the MCP Server
Handles all DrissionPage API variations with extensive error handling
"""

import asyncio
import time
import logging
import random
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import re

from enhanced_form_scraper import BulletproofFormScraper

logger = logging.getLogger(__name__)

class BulletproofFormSubmitter:
    def __init__(self, use_stealth: bool = True, headless: bool = True):
        self.scraper = BulletproofFormScraper(use_stealth=use_stealth, headless=headless)
        self.submission_history = []
        
    async def validate_submission_enhanced(self, url: str, field_data: Dict[str, str], 
                                         form_index: int = 0) -> Dict[str, Any]:
        """Bulletproof validation that never crashes"""
        try:
            # Always provide a baseline response
            result = {
                'valid': True,
                'issues': [],
                'warnings': [],
                'suggestions': [],
                'fields_checked': 0,
                'data_provided': len(field_data),
                'method_used': 'basic_validation'
            }
            
            # Try to get form structure
            try:
                form_result = await self.scraper.extract_form_fields_enhanced(url, form_index)
                
                if not form_result.get('success'):
                    result.update({
                        'valid': False,
                        'issues': [f"Cannot validate: {form_result.get('error', 'Unknown error')}"],
                        'method_used': form_result.get('method_used', 'unknown')
                    })
                    return result
                
                fields = form_result.get('fields', [])
                result['fields_checked'] = len(fields)
                result['method_used'] = form_result.get('method_used', 'unknown')
                
                # Validate each field safely
                issues = []
                warnings = []
                suggestions = []
                
                for field in fields:
                    try:
                        field_id = field.get('identifier', '')
                        field_name = field.get('name', '')
                        field_label = field.get('label', field_id or field_name or 'Unknown field')
                        
                        # Check if field is required
                        if field.get('required', False):
                            provided_value = self._safe_find_field_value(field, field_data)
                            if not provided_value or not provided_value.strip():
                                issues.append(f"Required field missing: {field_label}")
                                suggestions.append(f"Provide value for: {field_id or field_name}")
                        
                        # Basic field validation
                        provided_value = self._safe_find_field_value(field, field_data)
                        if provided_value:
                            field_issues = self._safe_validate_field_value(field, provided_value)
                            issues.extend(field_issues)
                            
                    except Exception as e:
                        logger.debug(f"Field validation error: {e}")
                        warnings.append(f"Could not validate field: {field.get('label', 'unknown')}")
                
                # Check for unknown fields
                known_fields = set()
                for field in fields:
                    if field.get('name'):
                        known_fields.add(field.get('name'))
                    if field.get('id'):
                        known_fields.add(field.get('id'))
                    if field.get('identifier'):
                        known_fields.add(field.get('identifier'))
                
                for provided_key in field_data.keys():
                    if provided_key not in known_fields:
                        # Simple fuzzy matching
                        best_match = self._safe_find_fuzzy_match(provided_key, known_fields)
                        if best_match:
                            suggestions.append(f"'{provided_key}' might be '{best_match}'")
                        else:
                            warnings.append(f"Unknown field: {provided_key}")
                
                result.update({
                    'valid': len(issues) == 0,
                    'issues': issues,
                    'warnings': warnings,
                    'suggestions': suggestions
                })
                
                return result
                
            except Exception as e:
                logger.warning(f"Form validation error: {e}")
                result.update({
                    'valid': False,
                    'issues': [f"Validation failed: {str(e)[:100]}"],
                    'warnings': ['Validation system encountered an error']
                })
                return result
                
        except Exception as e:
            # Ultimate fallback - never crash
            logger.error(f"Complete validation failure: {e}")
            return {
                'valid': False,
                'issues': [f"Validation system error: {str(e)[:100]}"],
                'warnings': ['Validation system is experiencing issues'],
                'suggestions': ['Try again or check the form manually'],
                'fields_checked': 0,
                'data_provided': len(field_data) if field_data else 0,
                'method_used': 'error_fallback'
            }
    
    async def submit_form_enhanced(self, url: str, field_data: Dict[str, str], 
                                 form_index: int = 0, max_retries: int = 2) -> Dict[str, Any]:
        """Bulletproof form submission that never crashes"""
        try:
            # Always provide a baseline response
            result = {
                'success': False,
                'message': 'Form submission in progress...',
                'method_used': 'unknown',
                'attempts': 0,
                'error': None
            }
            
            # Validate first (but don't fail if validation fails)
            try:
                validation = await self.validate_submission_enhanced(url, field_data, form_index)
                result['validation'] = validation
                
                # Continue even if validation failed (best effort)
                if not validation.get('valid', False):
                    result['warnings'] = validation.get('issues', [])
                    
            except Exception as e:
                logger.warning(f"Validation failed during submission: {e}")
                result['validation'] = {'valid': False, 'error': str(e)[:100]}
            
            # Attempt submission with retries
            for attempt in range(max_retries):
                try:
                    result['attempts'] = attempt + 1
                    
                    # Try browser automation (most reliable for complex forms)
                    submission_result = await self._safe_submit_with_browser(url, field_data, form_index)
                    
                    # Record attempt
                    self._safe_record_attempt(url, field_data, submission_result, attempt + 1)
                    
                    if submission_result.get('success', False):
                        # Success!
                        result.update(submission_result)
                        result['method_used'] = 'browser_automation'
                        return result
                    else:
                        # Failed, but continue to retry
                        result['error'] = submission_result.get('error', 'Unknown submission error')
                        
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                            logger.info(f"Submission attempt {attempt + 1} failed, retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                
                except Exception as e:
                    logger.warning(f"Submission attempt {attempt + 1} crashed: {e}")
                    result['error'] = f"Attempt {attempt + 1} failed: {str(e)[:100]}"
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
            
            # All attempts failed
            result.update({
                'success': False,
                'message': f'Form submission failed after {max_retries} attempts',
                'method_used': 'failed_all_attempts'
            })
            
            return result
            
        except Exception as e:
            # Ultimate fallback - never crash the server
            logger.error(f"Complete submission failure: {e}")
            return {
                'success': False,
                'error': f"Submission system error: {str(e)[:200]}",
                'message': 'Form submission system encountered an error',
                'method_used': 'error_fallback',
                'attempts': 1
            }
    
    async def _safe_submit_with_browser(self, url: str, field_data: Dict[str, str], 
                                      form_index: int) -> Dict[str, Any]:
        """Safely submit form using browser automation"""
        try:
            # Ensure we have a browser
            if not self.scraper.browser_page:
                try:
                    self.scraper.browser_page = await self.scraper._safe_create_browser()
                except Exception as e:
                    return {
                        'success': False,
                        'error': f"Could not create browser: {str(e)[:100]}"
                    }
            
            # Navigate to page
            try:
                self.scraper.browser_page.get(url)
                await asyncio.sleep(3)  # Wait for page load
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Could not navigate to page: {str(e)[:100]}"
                }
            
            # Find and fill the form
            try:
                # Get forms
                forms = self.scraper.browser_page.eles('tag:form')
                if not forms:
                    return {
                        'success': False,
                        'error': 'No forms found on the page'
                    }
                
                if form_index >= len(forms):
                    return {
                        'success': False,
                        'error': f'Form index {form_index} not found. Found {len(forms)} forms.'
                    }
                
                form = forms[form_index]
                
                # Fill form fields
                fill_result = await self._safe_fill_form_fields(form, field_data)
                
                # Submit form
                submit_result = await self._safe_submit_form(form)
                
                # Process response
                response_result = await self._safe_process_response(url)
                
                # Combine results
                final_result = {
                    'success': response_result.get('success', False),
                    'message': response_result.get('message', 'Form submitted'),
                    'field_filling': fill_result,
                    'submission': submit_result,
                    'response': response_result
                }
                
                return final_result
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Form interaction failed: {str(e)[:100]}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Browser submission failed: {str(e)[:100]}"
            }
    
    async def _safe_fill_form_fields(self, form, field_data: Dict[str, str]) -> Dict[str, Any]:
        """Safely fill form fields"""
        try:
            filled_fields = []
            errors = []
            
            # Get field elements
            try:
                field_elements = form.eles('tag:input, tag:textarea, tag:select')
            except Exception as e:
                return {
                    'fields_filled': 0,
                    'errors': [f"Could not find form fields: {str(e)[:50]}"]
                }
            
            for element in field_elements:
                try:
                    # Get field info
                    field_type = element.attr('type') or 'text'
                    field_name = element.attr('name') or ''
                    field_id = element.attr('id') or ''
                    
                    # Skip non-input fields
                    if field_type.lower() in ['hidden', 'submit', 'button', 'image', 'reset']:
                        continue
                    
                    # Find value for this field
                    field_identifier = field_id or field_name
                    value = field_data.get(field_identifier) or field_data.get(field_name) or field_data.get(field_id)
                    
                    # Try case-insensitive matching if no exact match
                    if not value:
                        for key, val in field_data.items():
                            if (field_identifier and key.lower() == field_identifier.lower()) or \
                               (field_name and key.lower() == field_name.lower()) or \
                               (field_id and key.lower() == field_id.lower()):
                                value = val
                                break
                    
                    if value:
                        success = await self._safe_fill_single_field(element, value, field_type)
                        if success:
                            filled_fields.append({
                                'field': field_identifier or f'field_{len(filled_fields)}',
                                'value': value[:30] + '...' if len(value) > 30 else value
                            })
                        else:
                            errors.append(f"Failed to fill field: {field_identifier}")
                
                except Exception as e:
                    logger.debug(f"Field filling error: {e}")
                    errors.append(f"Error with field: {str(e)[:50]}")
            
            return {
                'fields_filled': len(filled_fields),
                'filled_fields': filled_fields,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'fields_filled': 0,
                'errors': [f"Form filling failed: {str(e)[:100]}"]
            }
    
    async def _safe_fill_single_field(self, element, value: str, field_type: str) -> bool:
        """Safely fill a single field"""
        try:
            field_type_lower = field_type.lower()
            
            if field_type_lower in ['text', 'email', 'password', 'url', 'tel', 'number']:
                # Text input fields
                try:
                    element.clear()
                    await asyncio.sleep(0.1)
                    element.input(value)
                    await asyncio.sleep(0.1)
                    return True
                except Exception as e:
                    logger.debug(f"Text input failed: {e}")
                    return False
                    
            elif field_type_lower == 'textarea':
                # Textarea
                try:
                    element.clear()
                    await asyncio.sleep(0.1)
                    element.input(value)
                    await asyncio.sleep(0.1)
                    return True
                except Exception as e:
                    logger.debug(f"Textarea input failed: {e}")
                    return False
                    
            elif field_type_lower == 'checkbox':
                # Checkbox
                try:
                    should_check = value.lower() in ['true', '1', 'yes', 'on', 'checked']
                    is_checked = element.states.is_checked if hasattr(element, 'states') else False
                    
                    if should_check != is_checked:
                        element.click()
                        await asyncio.sleep(0.2)
                    return True
                except Exception as e:
                    logger.debug(f"Checkbox handling failed: {e}")
                    return False
                    
            elif field_type_lower == 'radio':
                # Radio button
                try:
                    element.click()
                    await asyncio.sleep(0.2)
                    return True
                except Exception as e:
                    logger.debug(f"Radio button failed: {e}")
                    return False
                    
            elif element.tag == 'select':
                # Select dropdown
                try:
                    # Try multiple methods to select
                    try:
                        element.select(value)
                        return True
                    except:
                        # Try clicking option
                        options = element.eles('tag:option')
                        for option in options:
                            if option.text.strip().lower() == value.lower() or \
                               option.attr('value', '').lower() == value.lower():
                                option.click()
                                await asyncio.sleep(0.2)
                                return True
                        return False
                except Exception as e:
                    logger.debug(f"Select dropdown failed: {e}")
                    return False
            
            return False
            
        except Exception as e:
            logger.debug(f"Single field fill failed: {e}")
            return False
    
    async def _safe_submit_form(self, form) -> Dict[str, Any]:
        """Safely submit the form"""
        try:
            # Strategy 1: Find and click submit button
            try:
                submit_buttons = form.eles('css:input[type="submit"], button[type="submit"], button')
                if submit_buttons:
                    button = submit_buttons[0]
                    button_text = button.attr('value') or button.text or 'Submit'
                    logger.info(f"Clicking submit button: {button_text}")
                    button.click()
                    await asyncio.sleep(3)
                    return {
                        'method': 'submit_button',
                        'success': True,
                        'button_text': button_text
                    }
            except Exception as e:
                logger.debug(f"Submit button click failed: {e}")
            
            # Strategy 2: Press Enter in a text field
            try:
                text_inputs = form.eles('css:input[type="text"], input[type="email"], textarea')
                if text_inputs:
                    last_input = text_inputs[-1]
                    last_input.click()
                    last_input.input('\n')
                    await asyncio.sleep(3)
                    return {
                        'method': 'enter_key',
                        'success': True
                    }
            except Exception as e:
                logger.debug(f"Enter key submission failed: {e}")
            
            return {
                'method': 'none_found',
                'success': False,
                'error': 'No submission method found'
            }
            
        except Exception as e:
            return {
                'method': 'error',
                'success': False,
                'error': f"Submission failed: {str(e)[:100]}"
            }
    
    async def _safe_process_response(self, original_url: str) -> Dict[str, Any]:
        """Safely process the response after submission"""
        try:
            # Wait for page to settle
            await asyncio.sleep(3)
            
            current_url = self.scraper.browser_page.url
            content = self.scraper.browser_page.html
            
            # Look for success indicators
            success_indicators = self._safe_detect_success_indicators(content, current_url, original_url)
            error_indicators = self._safe_detect_error_indicators(content)
            
            # Determine success
            submission_success = (
                len(error_indicators) == 0 and 
                len(success_indicators) > 0
            )
            
            # Get confirmation message
            confirmation = self._safe_extract_confirmation(content, success_indicators)
            
            result = {
                'success': submission_success,
                'original_url': original_url,
                'final_url': current_url,
                'url_changed': current_url != original_url,
                'success_indicators': success_indicators,
                'error_indicators': error_indicators,
                'confirmation': confirmation
            }
            
            if submission_success:
                result['message'] = confirmation or 'Form appears to have been submitted successfully'
            else:
                if error_indicators:
                    result['message'] = f"Possible errors: {', '.join(error_indicators[:2])}"
                else:
                    result['message'] = 'Form submission result unclear'
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Response processing failed: {str(e)[:100]}",
                'message': 'Could not determine submission result'
            }
    
    def _safe_detect_success_indicators(self, content: str, final_url: str, original_url: str) -> List[str]:
        """Safely detect success indicators"""
        try:
            indicators = []
            
            if final_url != original_url:
                indicators.append('url_changed')
            
            content_lower = content.lower()
            
            success_phrases = [
                'thank you', 'success', 'submitted', 'received', 'confirmation',
                'message sent', 'application submitted', 'saved successfully'
            ]
            
            for phrase in success_phrases:
                if phrase in content_lower:
                    indicators.append(f'text_{phrase.replace(" ", "_")}')
            
            # Look for confirmation numbers
            if re.search(r'confirmation|reference|ticket.*#?\s*:?\s*[a-zA-Z0-9]+', content, re.IGNORECASE):
                indicators.append('confirmation_number')
            
            return indicators
            
        except Exception as e:
            logger.debug(f"Success detection failed: {e}")
            return []
    
    def _safe_detect_error_indicators(self, content: str) -> List[str]:
        """Safely detect error indicators"""
        try:
            indicators = []
            content_lower = content.lower()
            
            error_phrases = [
                'error', 'failed', 'invalid', 'required', 'missing',
                'try again', 'problem', 'incorrect'
            ]
            
            for phrase in error_phrases:
                if phrase in content_lower:
                    indicators.append(f'error_{phrase}')
            
            return indicators
            
        except Exception as e:
            logger.debug(f"Error detection failed: {e}")
            return []
    
    def _safe_extract_confirmation(self, content: str, success_indicators: List[str]) -> str:
        """Safely extract confirmation message"""
        try:
            content_lower = content.lower()
            
            if 'thank you' in content_lower:
                lines = content.split('\n')
                for line in lines:
                    line_clean = line.strip()
                    if 'thank you' in line_clean.lower() and len(line_clean) < 150:
                        return line_clean
            
            if success_indicators:
                return "Form submission appears successful"
            
            return ""
            
        except Exception as e:
            logger.debug(f"Confirmation extraction failed: {e}")
            return ""
    
    def _safe_find_field_value(self, field: Dict[str, Any], field_data: Dict[str, str]) -> str:
        """Safely find field value with fuzzy matching"""
        try:
            # Try exact matches
            for key in [field.get('id'), field.get('name'), field.get('identifier')]:
                if key and key in field_data:
                    return field_data[key]
            
            # Try case-insensitive
            field_keys = [k.lower() for k in [field.get('id'), field.get('name'), field.get('identifier')] if k]
            for provided_key, value in field_data.items():
                if provided_key.lower() in field_keys:
                    return value
            
            return ""
        except Exception as e:
            logger.debug(f"Field value finding failed: {e}")
            return ""
    
    def _safe_validate_field_value(self, field: Dict[str, Any], value: str) -> List[str]:
        """Safely validate field value"""
        try:
            issues = []
            field_type = field.get('type', '').lower()
            field_label = field.get('label', 'field')
            
            if field_type == 'email':
                if '@' not in value or '.' not in value:
                    issues.append(f"{field_label}: Invalid email format")
            elif field_type == 'url':
                if not value.startswith(('http://', 'https://')):
                    issues.append(f"{field_label}: Invalid URL format")
            
            return issues
        except Exception as e:
            logger.debug(f"Field validation failed: {e}")
            return []
    
    def _safe_find_fuzzy_match(self, target: str, candidates) -> Optional[str]:
        """Safely find fuzzy match"""
        try:
            target_lower = target.lower()
            
            # Exact match
            for candidate in candidates:
                if candidate.lower() == target_lower:
                    return candidate
            
            # Partial match
            for candidate in candidates:
                if target_lower in candidate.lower() or candidate.lower() in target_lower:
                    return candidate
            
            return None
        except Exception as e:
            logger.debug(f"Fuzzy matching failed: {e}")
            return None
    
    def _safe_record_attempt(self, url: str, field_data: Dict[str, str], 
                           result: Dict[str, Any], attempt: int):
        """Safely record submission attempt"""
        try:
            record = {
                'timestamp': time.time(),
                'url': url,
                'attempt': attempt,
                'success': result.get('success', False),
                'error': result.get('error', '')[:100],  # Limit error length
                'field_count': len(field_data)
            }
            
            self.submission_history.append(record)
            
            # Keep only last 50 records
            if len(self.submission_history) > 50:
                self.submission_history = self.submission_history[-50:]
        except Exception as e:
            logger.debug(f"Recording attempt failed: {e}")
    
    async def close(self):
        """Safely clean up resources"""
        try:
            await self.scraper.close()
        except Exception as e:
            logger.debug(f"Cleanup failed: {e}")

# Create alias for compatibility
EnhancedFormSubmitter = BulletproofFormSubmitter
