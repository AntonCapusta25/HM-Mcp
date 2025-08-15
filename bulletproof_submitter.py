#!/usr/bin/env python3
"""
Fixed Bulletproof Form Submitter
Resolves import issues and connection problems
"""

import asyncio
import time
import logging
import random
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import re

# Fixed import - use relative import
from bulletproof_scraper import BulletproofFormScraper

logger = logging.getLogger(__name__)

class BulletproofFormSubmitter:
    def __init__(self, use_stealth: bool = True, headless: bool = True):
        self.scraper = BulletproofFormScraper(use_stealth=use_stealth, headless=headless)
        self.submission_history = []
        self._max_history = 50
        
    async def validate_submission_enhanced(self, url: str, field_data: Dict[str, str], 
                                           form_index: int = 0) -> Dict[str, Any]:
        """Enhanced validation with comprehensive error handling"""
        try:
            logger.info(f"🔍 Validating form submission for: {url}")
            
            # Base response
            result = {
                'valid': True,
                'issues': [],
                'warnings': [],
                'suggestions': [],
                'fields_checked': 0,
                'data_provided': len(field_data) if field_data else 0,
                'method_used': 'basic_validation'
            }
            
            # Input validation
            if not url or not isinstance(url, str):
                result.update({
                    'valid': False,
                    'issues': ['Invalid URL provided'],
                    'method_used': 'input_validation'
                })
                return result
            
            if not field_data or not isinstance(field_data, dict):
                result.update({
                    'valid': False,
                    'issues': ['No field data provided or invalid format'],
                    'method_used': 'input_validation'
                })
                return result
            
            # Try to get form structure
            try:
                form_result = await self.scraper.extract_form_fields_enhanced(url, form_index)
                
                if not form_result.get('success'):
                    result.update({
                        'valid': False,
                        'issues': [f"Cannot validate: {form_result.get('error', 'Unknown error')}"],
                        'method_used': form_result.get('method_used', 'unknown'),
                        'warnings': ['Form structure analysis failed']
                    })
                    return result
                
                fields = form_result.get('fields', [])
                result['fields_checked'] = len(fields)
                result['method_used'] = form_result.get('method_used', 'unknown')
                
                # Validate each field
                issues = []
                warnings = []
                suggestions = []
                
                # Track which fields we found values for
                matched_fields = set()
                
                for field in fields:
                    try:
                        field_id = field.get('identifier', '')
                        field_name = field.get('name', '')
                        field_label = field.get('label', field_id or field_name or 'Unknown field')
                        
                        # Check if field is required
                        if field.get('required', False):
                            provided_value = self._safe_find_field_value(field, field_data)
                            if not provided_value or not str(provided_value).strip():
                                issues.append(f"Required field missing: {field_label}")
                                suggestions.append(f"Provide value for: {field_id or field_name}")
                            else:
                                matched_fields.add(field_id or field_name)
                        
                        # Validate field value if provided
                        provided_value = self._safe_find_field_value(field, field_data)
                        if provided_value:
                            matched_fields.add(field_id or field_name)
                            field_issues = self._safe_validate_field_value(field, str(provided_value))
                            issues.extend(field_issues)
                            
                    except Exception as e:
                        logger.debug(f"⚠️ Field validation error: {e}")
                        warnings.append(f"Could not validate field: {field.get('label', 'unknown')}")
                
                # Check for unknown fields in provided data
                known_fields = set()
                for field in fields:
                    for key in ['name', 'id', 'identifier']:
                        value = field.get(key)
                        if value:
                            known_fields.add(value)
                
                for provided_key in field_data.keys():
                    if provided_key not in known_fields and provided_key not in matched_fields:
                        # Fuzzy matching for suggestions
                        best_match = self._safe_find_fuzzy_match(provided_key, known_fields)
                        if best_match:
                            suggestions.append(f"'{provided_key}' might be '{best_match}'")
                        else:
                            warnings.append(f"Unknown field: {provided_key}")
                
                # Calculate match score
                provided_count = len(field_data)
                matched_count = len(matched_fields)
                match_score = matched_count / max(provided_count, 1)
                
                result.update({
                    'valid': len(issues) == 0,
                    'issues': issues,
                    'warnings': warnings,
                    'suggestions': suggestions,
                    'match_score': match_score,
                    'matched_fields': matched_count,
                    'total_fields': len(fields)
                })
                
                logger.info(f"✅ Validation complete - Valid: {result['valid']}, Issues: {len(issues)}, Score: {match_score:.2f}")
                return result
                
            except Exception as e:
                logger.warning(f"⚠️ Form validation error: {e}")
                result.update({
                    'valid': False,
                    'issues': [f"Validation failed: {str(e)[:100]}"],
                    'warnings': ['Validation system encountered an error'],
                    'method_used': 'error_fallback'
                })
                return result
                
        except Exception as e:
            logger.error(f"❌ Complete validation failure: {e}")
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
                                   form_index: int = 0, max_retries: int = 3) -> Dict[str, Any]:
        """Enhanced form submission with comprehensive error handling"""
        submission_start = time.time()
        
        try:
            logger.info(f"🚀 Starting form submission for: {url}")
            
            # Base response
            result = {
                'success': False,
                'message': 'Form submission in progress...',
                'method_used': 'unknown',
                'attempts': 0,
                'error': None,
                'submission_time': 0,
                'validation': None
            }
            
            # Input validation
            if not url or not field_data:
                result.update({
                    'success': False,
                    'error': 'Invalid input: URL and field_data are required',
                    'message': 'Submission failed due to invalid input'
                })
                return result
            
            # Pre-submission validation (but don't fail if validation fails)
            try:
                logger.debug("🔍 Running pre-submission validation...")
                validation = await self.validate_submission_enhanced(url, field_data, form_index)
                result['validation'] = validation
                
                if not validation.get('valid', False):
                    result['warnings'] = validation.get('issues', [])
                    logger.warning(f"⚠️ Validation issues found: {len(validation.get('issues', []))}")
                else:
                    logger.info("✅ Pre-submission validation passed")
                    
            except Exception as e:
                logger.warning(f"⚠️ Validation failed during submission: {e}")
                result['validation'] = {'valid': False, 'error': str(e)[:100]}
            
            # Attempt submission with intelligent retry
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    result['attempts'] = attempt + 1
                    logger.info(f"🎯 Submission attempt {attempt + 1} of {max_retries}")
                    
                    # Use browser automation for form submission
                    submission_result = await self._safe_submit_with_browser(url, field_data, form_index)
                    
                    # Record the attempt
                    self._safe_record_attempt(url, field_data, submission_result, attempt + 1)
                    
                    if submission_result.get('success', False):
                        # Success!
                        result.update(submission_result)
                        result['method_used'] = 'browser_automation'
                        result['submission_time'] = time.time() - submission_start
                        logger.info(f"✅ Form submission successful on attempt {attempt + 1}")
                        return result
                    else:
                        # Failed, prepare for retry
                        last_error = submission_result.get('error', 'Unknown submission error')
                        result['error'] = last_error
                        
                        logger.warning(f"⚠️ Attempt {attempt + 1} failed: {last_error}")
                        
                        # Wait before retry with exponential backoff
                        if attempt < max_retries - 1:
                            wait_time = min((attempt + 1) * 2, 10)  # Max 10 seconds
                            logger.info(f"⏳ Waiting {wait_time}s before retry...")
                            await asyncio.sleep(wait_time)
                
                except Exception as e:
                    last_error = f"Attempt {attempt + 1} crashed: {str(e)[:100]}"
                    logger.error(f"❌ {last_error}")
                    result['error'] = last_error
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
            
            # All attempts failed
            result.update({
                'success': False,
                'message': f'Form submission failed after {max_retries} attempts',
                'method_used': 'failed_all_attempts',
                'error': last_error,
                'submission_time': time.time() - submission_start
            })
            
            logger.error(f"❌ Form submission completely failed after {max_retries} attempts")
            return result
            
        except Exception as e:
            # Ultimate fallback
            logger.error(f"❌ Complete submission failure: {e}")
            return {
                'success': False,
                'error': f"Submission system error: {str(e)[:200]}",
                'message': 'Form submission system encountered an error',
                'method_used': 'error_fallback',
                'attempts': 1,
                'submission_time': time.time() - submission_start
            }
    
    async def _safe_submit_with_browser(self, url: str, field_data: Dict[str, str], 
                                      form_index: int) -> Dict[str, Any]:
        """Enhanced browser-based form submission"""
        try:
            logger.debug("🌐 Preparing browser for form submission...")
            
            # Ensure browser is available
            if not self.scraper.browser_page:
                try:
                    self.scraper.browser_page = await self.scraper._safe_create_browser()
                except Exception as e:
                    return {
                        'success': False,
                        'error': f"Could not create browser: {str(e)[:100]}"
                    }
            
            # Navigate to page with retry
            for nav_attempt in range(2):
                try:
                    logger.debug(f"📍 Navigating to page (attempt {nav_attempt + 1})...")
                    self.scraper.browser_page.get(url)
                    await asyncio.sleep(3)  # Wait for page load
                    
                    # Verify page loaded
                    current_url = self.scraper.browser_page.url
                    if current_url:
                        logger.debug(f"✅ Navigation successful: {current_url}")
                        break
                    else:
                        raise Exception("Page did not load properly")
                        
                except Exception as e:
                    if nav_attempt == 0:
                        logger.warning(f"⚠️ Navigation attempt {nav_attempt + 1} failed: {e}")
                        await asyncio.sleep(2)
                    else:
                        return {
                            'success': False,
                            'error': f"Could not navigate to page: {str(e)[:100]}"
                        }
            
            # Find and interact with the form
            try:
                logger.debug("🔍 Looking for forms on page...")
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
                logger.debug(f"✅ Found form at index {form_index}")
                
                # Fill form fields
                logger.debug("📝 Filling form fields...")
                fill_result = await self._safe_fill_form_fields(form, field_data)
                
                if fill_result.get('fields_filled', 0) == 0:
                    logger.warning("⚠️ No fields were filled successfully")
                else:
                    logger.info(f"✅ Filled {fill_result.get('fields_filled', 0)} fields")
                
                # Submit the form
                logger.debug("🚀 Submitting form...")
                submit_result = await self._safe_submit_form(form)
                
                # Wait and process response
                logger.debug("⏳ Processing submission response...")
                await asyncio.sleep(3)  # Wait for response
                response_result = await self._safe_process_response(url)
                
                # Combine all results
                final_result = {
                    'success': response_result.get('success', False),
                    'message': response_result.get('message', 'Form submitted'),
                    'field_filling': fill_result,
                    'submission': submit_result,
                    'response': response_result,
                    'final_url': response_result.get('final_url', url)
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
        """Enhanced form field filling with better error handling"""
        try:
            filled_fields = []
            errors = []
            skipped_fields = []
            
            # Get field elements with timeout
            try:
                field_elements = form.eles('tag:input, tag:textarea, tag:select')
                logger.debug(f"🔍 Found {len(field_elements)} form elements")
            except Exception as e:
                return {
                    'fields_filled': 0,
                    'errors': [f"Could not find form fields: {str(e)[:50]}"],
                    'filled_fields': [],
                    'skipped_fields': []
                }
            
            for i, element in enumerate(field_elements):
                try:
                    # Get field information
                    field_type = element.attr('type') or 'text'
                    field_name = element.attr('name') or ''
                    field_id = element.attr('id') or ''
                    field_placeholder = element.attr('placeholder') or ''
                    
                    # Skip non-fillable fields
                    if field_type.lower() in ['hidden', 'submit', 'button', 'image', 'reset']:
                        skipped_fields.append(f"{field_type} field skipped")
                        continue
                    
                    # Find value for this field using multiple strategies
                    field_identifier = field_id or field_name or f'field_{i}'
                    value = self._find_field_value_multiple_strategies(
                        field_data, field_identifier, field_name, field_id, field_placeholder
                    )
                    
                    if value is not None:
                        success = await self._safe_fill_single_field(element, str(value), field_type)
                        if success:
                            filled_fields.append({
                                'field': field_identifier,
                                'type': field_type,
                                'value': str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
                            })
                            logger.debug(f"✅ Filled field: {field_identifier}")
                        else:
                            errors.append(f"Failed to fill field: {field_identifier}")
                            logger.debug(f"⚠️ Failed to fill: {field_identifier}")
                    else:
                        skipped_fields.append(f"No value found for: {field_identifier}")
                
                except Exception as e:
                    error_msg = f"Error with field {i}: {str(e)[:50]}"
                    errors.append(error_msg)
                    logger.debug(f"⚠️ {error_msg}")
            
            result = {
                'fields_filled': len(filled_fields),
                'filled_fields': filled_fields,
                'errors': errors,
                'skipped_fields': skipped_fields,
                'total_elements': len(field_elements)
            }
            
            logger.info(f"📊 Field filling summary: {len(filled_fields)} filled, {len(errors)} errors, {len(skipped_fields)} skipped")
            return result
            
        except Exception as e:
            return {
                'fields_filled': 0,
                'errors': [f"Form filling failed: {str(e)[:100]}"],
                'filled_fields': [],
                'skipped_fields': []
            }
    
    def _find_field_value_multiple_strategies(self, field_data: Dict[str, str], 
                                            identifier: str, name: str, id_attr: str, placeholder: str) -> Optional[str]:
        """Find field value using multiple matching strategies"""
        try:
            # Strategy 1: Exact matches
            for key in [id_attr, name, identifier]:
                if key and key in field_data:
                    return field_data[key]
            
            # Strategy 2: Case-insensitive matching
            field_keys_lower = {k.lower(): v for k, v in field_data.items()}
            for key in [id_attr, name, identifier]:
                if key and key.lower() in field_keys_lower:
                    return field_keys_lower[key.lower()]
            
            # Strategy 3: Partial matching
            for provided_key, value in field_data.items():
                for field_key in [id_attr, name, identifier, placeholder]:
                    if field_key and (
                        provided_key.lower() in field_key.lower() or 
                        field_key.lower() in provided_key.lower()
                    ):
                        return value
            
            # Strategy 4: Common field name mappings
            field_mappings = {
                'email': ['email', 'e-mail', 'mail', 'email_address'],
                'name': ['name', 'full_name', 'fullname', 'username'],
                'first_name': ['first_name', 'firstname', 'fname'],
                'last_name': ['last_name', 'lastname', 'lname'],
                'phone': ['phone', 'telephone', 'mobile', 'phone_number'],
                'message': ['message', 'comment', 'comments', 'description'],
                'subject': ['subject', 'title', 'topic']
            }
            
            for field_key in [id_attr, name, identifier]:
                if not field_key:
                    continue
                    
                field_key_lower = field_key.lower()
                for provided_key, value in field_data.items():
                    provided_key_lower = provided_key.lower()
                    
                    # Check if they map to the same concept
                    for concept, variations in field_mappings.items():
                        if (field_key_lower in variations and provided_key_lower in variations):
                            return value
            
            return None
            
        except Exception as e:
            logger.debug(f"⚠️ Field value matching failed: {e}")
            return None
    
    async def _safe_fill_single_field(self, element, value: str, field_type: str) -> bool:
        """Enhanced single field filling with better error handling"""
        try:
            field_type_lower = field_type.lower()
            
            # Add small delay to simulate human behavior
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
            if field_type_lower in ['text', 'email', 'password', 'url', 'tel', 'number', 'search']:
                # Text-based input fields
                try:
                    # Clear field first
                    element.clear()
                    await asyncio.sleep(0.1)
                    
                    # Type the value
                    element.input(value)
                    await asyncio.sleep(0.1)
                    
                    # Verify the value was set
                    current_value = element.attr('value') or ''
                    return bool(current_value.strip())
                    
                except Exception as e:
                    logger.debug(f"⚠️ Text input failed: {e}")
                    return False
                    
            elif element.tag == 'textarea' or field_type_lower == 'textarea':
                # Textarea
                try:
                    element.clear()
                    await asyncio.sleep(0.1)
                    element.input(value)
                    await asyncio.sleep(0.1)
                    return True
                except Exception as e:
                    logger.debug(f"⚠️ Textarea input failed: {e}")
                    return False
                    
            elif field_type_lower == 'checkbox':
                # Checkbox
                try:
                    should_check = str(value).lower() in ['true', '1', 'yes', 'on', 'checked']
                    
                    # Get current state
                    try:
                        is_checked = element.states.is_checked
                    except:
                        is_checked = element.attr('checked') is not None
                    
                    # Click if state needs to change
                    if should_check != is_checked:
                        element.click()
                        await asyncio.sleep(0.2)
                    
                    return True
                except Exception as e:
                    logger.debug(f"⚠️ Checkbox handling failed: {e}")
                    return False
                    
            elif field_type_lower == 'radio':
                # Radio button
                try:
                    element.click()
                    await asyncio.sleep(0.2)
                    return True
                except Exception as e:
                    logger.debug(f"⚠️ Radio button failed: {e}")
                    return False
                    
            elif element.tag == 'select':
                # Select dropdown
                try:
                    # Try multiple selection methods
                    success = False
                    
                    # Method 1: Direct select
                    try:
                        element.select(value)
                        success = True
                    except:
                        # Method 2: Find and click option
                        try:
                            options = element.eles('tag:option')
                            for option in options:
                                option_text = (option.text or '').strip()
                                option_value = (option.attr('value') or '').strip()
                                
                                if (option_text.lower() == value.lower() or 
                                    option_value.lower() == value.lower()):
                                    option.click()
                                    success = True
                                    break
                        except:
                            pass
                    
                    if success:
                        await asyncio.sleep(0.2)
                    
                    return success
                    
                except Exception as e:
                    logger.debug(f"⚠️ Select dropdown failed: {e}")
                    return False
            
            # Unsupported field type
            logger.debug(f"⚠️ Unsupported field type: {field_type}")
            return False
            
        except Exception as e:
            logger.debug(f"⚠️ Single field fill failed: {e}")
            return False
    
    async def _safe_submit_form(self, form) -> Dict[str, Any]:
        """Enhanced form submission with multiple strategies"""
        try:
            logger.debug("🎯 Attempting form submission...")
            
            # Strategy 1: Find and click submit button
            submit_selectors = [
                'css:input[type="submit"]',
                'css:button[type="submit"]', 
                'css:button',
                'css:input[value*="submit" i]',
                'css:button:contains("Submit")',
                'css:button:contains("Send")',
                'css:input[value*="send" i]'
            ]
            
            for selector in submit_selectors:
                try:
                    buttons = form.eles(selector)
                    if buttons:
                        button = buttons[0]
                        button_text = button.attr('value') or button.text or 'Submit'
                        logger.debug(f"🎯 Clicking submit button: {button_text}")
                        
                        button.click()
                        await asyncio.sleep(2)  # Wait for submission
                        
                        return {
                            'method': 'submit_button',
                            'success': True,
                            'button_text': button_text,
                            'selector': selector
                        }
                except Exception as e:
                    logger.debug(f"⚠️ Submit button strategy failed ({selector}): {e}")
                    continue
            
            # Strategy 2: Press Enter in a focusable field
            try:
                focusable_selectors = [
                    'css:input[type="text"]',
                    'css:input[type="email"]', 
                    'css:textarea',
                    'css:input:not([type="hidden"]):not([type="submit"]):not([type="button"])'
                ]
                
                for selector in focusable_selectors:
                    try:
                        inputs = form.eles(selector)
                        if inputs:
                            last_input = inputs[-1]  # Use last input
                            last_input.click()
                            await asyncio.sleep(0.2)
                            last_input.input('\n')  # Press Enter
                            await asyncio.sleep(2)
                            
                            return {
                                'method': 'enter_key',
                                'success': True,
                                'selector': selector
                            }
                    except Exception as e:
                        logger.debug(f"⚠️ Enter key strategy failed ({selector}): {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"⚠️ Enter key submission failed: {e}")
            
            # Strategy 3: Submit via JavaScript
            try:
                form_element = form
                script = "arguments[0].submit();"
                self.scraper.browser_page.run_js(script, form_element)
                await asyncio.sleep(2)
                
                return {
                    'method': 'javascript_submit',
                    'success': True
                }
                
            except Exception as e:
                logger.debug(f"⚠️ JavaScript submission failed: {e}")
            
            # All strategies failed
            return {
                'method': 'none_found',
                'success': False,
                'error': 'No working submission method found'
            }
            
        except Exception as e:
            return {
                'method': 'error',
                'success': False,
                'error': f"Submission failed: {str(e)[:100]}"
            }
    
    async def _safe_process_response(self, original_url: str) -> Dict[str, Any]:
        """Enhanced response processing with better success detection"""
        try:
            logger.debug("📊 Processing submission response...")
            
            # Wait for page to settle
            await asyncio.sleep(3)
            
            current_url = self.scraper.browser_page.url
            content = self.scraper.browser_page.html or ""
            
            # Detect success/error indicators
            success_indicators = self._safe_detect_success_indicators(content, current_url, original_url)
            error_indicators = self._safe_detect_error_indicators(content)
            
            # Determine submission success
            has_errors = len(error_indicators) > 0
            has_success = len(success_indicators) > 0
            url_changed = current_url != original_url
            
            # Success scoring
            success_score = 0
            if has_success:
                success_score += 50
            if url_changed:
                success_score += 30
            if not has_errors:
                success_score += 20
            
            submission_success = success_score >= 50 and not has_errors
            
            # Extract confirmation message
            confirmation = self._safe_extract_confirmation(content, success_indicators)
            
            result = {
                'success': submission_success,
                'success_score': success_score,
                'original_url': original_url,
                'final_url': current_url,
                'url_changed': url_changed,
                'success_indicators': success_indicators,
                'error_indicators': error_indicators,
                'confirmation': confirmation
            }
            
            # Generate appropriate message
            if submission_success:
                if confirmation:
                    result['message'] = confirmation
                elif url_changed:
                    result['message'] = 'Form submitted successfully (redirected to confirmation page)'
                else:
                    result['message'] = 'Form appears to have been submitted successfully'
            else:
                if error_indicators:
                    result['message'] = f"Submission may have failed: {'; '.join(error_indicators[:2])}"
                else:
                    result['message'] = 'Form submission result unclear - please verify manually'
            
            logger.info(f"📊 Response analysis: Success={submission_success}, Score={success_score}")
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Response processing failed: {e}")
            return {
                'success': False,
                'error': f"Response processing failed: {str(e)[:100]}",
                'message': 'Could not determine submission result',
                'original_url': original_url,
                'success_score': 0
            }
    
    def _safe_detect_success_indicators(self, content: str, final_url: str, original_url: str) -> List[str]:
        """Enhanced success indicator detection"""
        try:
            indicators = []
            
            # URL change often indicates success
            if final_url != original_url and final_url:
                # Check if it's a meaningful redirect
                if any(keyword in final_url.lower() for keyword in ['thank', 'success', 'confirm', 'complete']):
                    indicators.append('success_url_redirect')
                else:
                    indicators.append('url_changed')
            
            content_lower = content.lower()
            
            # Strong success phrases
            strong_success_phrases = [
                'thank you', 'thanks', 'message sent', 'form submitted',
                'successfully submitted', 'submission successful', 'sent successfully',
                'we have received', 'received your message', 'confirmation'
            ]
            
            for phrase in strong_success_phrases:
                if phrase in content_lower:
                    indicators.append(f'text_{phrase.replace(" ", "_")}')
            
            # Look for confirmation numbers/IDs
            confirmation_patterns = [
                r'confirmation\s*(?:number|id|code)?\s*:?\s*([a-zA-Z0-9]+)',
                r'reference\s*(?:number|id|code)?\s*:?\s*([a-zA-Z0-9]+)',
                r'ticket\s*(?:number|id)?\s*:?\s*([a-zA-Z0-9]+)'
            ]
            
            for pattern in confirmation_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    indicators.append('confirmation_number')
                    break
            
            # Check for success page elements
            success_elements = [
                'class.*success', 'class.*thank', 'class.*confirm',
                'id.*success', 'id.*thank', 'id.*confirm'
            ]
            
            for element_pattern in success_elements:
                if re.search(element_pattern, content, re.IGNORECASE):
                    indicators.append('success_element')
                    break
            
            return indicators
            
        except Exception as e:
            logger.debug(f"⚠️ Success detection failed: {e}")
            return []
    
    def _safe_detect_error_indicators(self, content: str) -> List[str]:
        """Enhanced error indicator detection"""
        try:
            indicators = []
            content_lower = content.lower()
            
            # Strong error phrases
            error_phrases = [
                ('error', 'error_general'),
                ('failed', 'error_failed'),
                ('invalid', 'error_invalid'),
                ('required field', 'error_required'),
                ('missing', 'error_missing'),
                ('try again', 'error_retry'),
                ('problem', 'error_problem'),
                ('incorrect', 'error_incorrect'),
                ('not allowed', 'error_not_allowed'),
                ('forbidden', 'error_forbidden')
            ]
            
            for phrase, indicator in error_phrases:
                if phrase in content_lower:
                    indicators.append(indicator)
            
            # Check for error CSS classes/IDs
            error_patterns = [
                r'class=["\'][^"\']*error[^"\']*["\']',
                r'class=["\'][^"\']*danger[^"\']*["\']',
                r'class=["\'][^"\']*alert[^"\']*["\']',
                r'id=["\'][^"\']*error[^"\']*["\']'
            ]
            
            for pattern in error_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    indicators.append('error_element')
                    break
            
            return indicators
            
        except Exception as e:
            logger.debug(f"⚠️ Error detection failed: {e}")
            return []
    
    def _safe_extract_confirmation(self, content: str, success_indicators: List[str]) -> str:
        """Enhanced confirmation message extraction"""
        try:
            content_lines = content.split('\n')
            
            # Look for lines containing success keywords
            success_keywords = ['thank you', 'success', 'sent', 'received', 'confirmation']
            
            for line in content_lines:
                line_clean = line.strip()
                if (len(line_clean) > 10 and len(line_clean) < 200 and
                    any(keyword in line_clean.lower() for keyword in success_keywords)):
                    # Clean up HTML tags
                    clean_line = re.sub(r'<[^>]+>', '', line_clean)
                    clean_line = re.sub(r'\s+', ' ', clean_line).strip()
                    if clean_line and len(clean_line) > 10:
                        return clean_line
            
            # Fallback: generic success message if indicators suggest success
            if success_indicators:
                return "Form submission appears to have been successful"
            
            return ""
            
        except Exception as e:
            logger.debug(f"⚠️ Confirmation extraction failed: {e}")
            return ""
    
    # Utility methods with enhanced error handling
    def _safe_find_field_value(self, field: Dict[str, Any], field_data: Dict[str, str]) -> str:
        """Enhanced field value finder with multiple strategies"""
        try:
            # Try multiple field identifiers
            for key in [field.get('id'), field.get('name'), field.get('identifier')]:
                if key and key in field_data:
                    return field_data[key]
            
            # Case-insensitive matching
            field_keys = [k.lower() for k in [field.get('id'), field.get('name'), field.get('identifier')] if k]
            for provided_key, value in field_data.items():
                if provided_key.lower() in field_keys:
                    return value
            
            return ""
        except Exception as e:
            logger.debug(f"⚠️ Field value finding failed: {e}")
            return ""
    
    def _safe_validate_field_value(self, field: Dict[str, Any], value: str) -> List[str]:
        """Enhanced field value validation"""
        try:
            issues = []
            field_type = field.get('type', '').lower()
            field_label = field.get('label', 'field')
            
            # Type-specific validation
            if field_type == 'email':
                if '@' not in value or '.' not in value.split('@')[-1]:
                    issues.append(f"{field_label}: Invalid email format")
            elif field_type == 'url':
                if not value.startswith(('http://', 'https://', 'www.')):
                    issues.append(f"{field_label}: Invalid URL format")
            elif field_type == 'tel':
                # Basic phone validation
                phone_clean = re.sub(r'[^\d+\-\(\)\s]', '', value)
                if len(phone_clean) < 7:
                    issues.append(f"{field_label}: Phone number seems too short")
            
            # Length validation
            max_length = field.get('maxlength')
            if max_length and len(value) > int(max_length):
                issues.append(f"{field_label}: Value too long (max {max_length} characters)")
            
            # Pattern validation
            pattern = field.get('pattern')
            if pattern:
                try:
                    if not re.match(pattern, value):
                        issues.append(f"{field_label}: Value doesn't match required pattern")
                except:
                    pass  # Invalid regex pattern
            
            return issues
        except Exception as e:
            logger.debug(f"⚠️ Field validation failed: {e}")
            return []
    
    def _safe_find_fuzzy_match(self, target: str, candidates) -> Optional[str]:
        """Enhanced fuzzy matching with better algorithms"""
        try:
            if not target or not candidates:
                return None
                
            target_lower = target.lower()
            
            # Exact match
            for candidate in candidates:
                if candidate and candidate.lower() == target_lower:
                    return candidate
            
            # Substring matching
            matches = []
            for candidate in candidates:
                if not candidate:
                    continue
                    
                candidate_lower = candidate.lower()
                
                # Bidirectional substring matching
                if target_lower in candidate_lower or candidate_lower in target_lower:
                    matches.append(candidate)
            
            # Return the shortest match (likely most relevant)
            if matches:
                return min(matches, key=len)
            
            # Edit distance matching for close matches
            def simple_edit_distance(s1: str, s2: str) -> int:
                if len(s1) < len(s2):
                    return simple_edit_distance(s2, s1)
                
                if len(s2) == 0:
                    return len(s1)
                
                previous_row = list(range(len(s2) + 1))
                for i, c1 in enumerate(s1):
                    current_row = [i + 1]
                    for j, c2 in enumerate(s2):
                        insertions = previous_row[j + 1] + 1
                        deletions = current_row[j] + 1
                        substitutions = previous_row[j] + (c1 != c2)
                        current_row.append(min(insertions, deletions, substitutions))
                    previous_row = current_row
                
                return previous_row[-1]
            
            # Find candidates with low edit distance
            close_matches = []
            for candidate in candidates:
                if candidate and len(candidate) > 2:  # Skip very short candidates
                    distance = simple_edit_distance(target_lower, candidate.lower())
                    max_distance = max(len(target), len(candidate)) // 3  # Allow 33% difference
                    if distance <= max_distance:
                        close_matches.append((candidate, distance))
            
            if close_matches:
                # Return closest match
                return min(close_matches, key=lambda x: x[1])[0]
            
            return None
            
        except Exception as e:
            logger.debug(f"⚠️ Fuzzy matching failed: {e}")
            return None
    
    def _safe_record_attempt(self, url: str, field_data: Dict[str, str], 
                           result: Dict[str, Any], attempt: int):
        """Enhanced attempt recording with better data management"""
        try:
            record = {
                'timestamp': time.time(),
                'url': url[:200] if url else '',  # Limit URL length
                'attempt': attempt,
                'success': result.get('success', False),
                'error': result.get('error', '')[:200] if result.get('error') else '',  # Limit error length
                'field_count': len(field_data) if field_data else 0,
                'method_used': result.get('method_used', 'unknown'),
                'submission_time': result.get('submission_time', 0)
            }
            
            self.submission_history.append(record)
            
            # Keep only recent records to prevent memory issues
            if len(self.submission_history) > self._max_history:
                self.submission_history = self.submission_history[-self._max_history:]
                
            logger.debug(f"📝 Recorded submission attempt: {record['success']}")
            
        except Exception as e:
            logger.debug(f"⚠️ Recording attempt failed: {e}")
    
    async def close(self):
        """Enhanced cleanup with proper resource management"""
        try:
            if self.scraper:
                await self.scraper.close()
                logger.debug("✅ Scraper resources cleaned up")
        except Exception as e:
            logger.debug(f"⚠️ Cleanup failed: {e}")

# Alias for compatibility
EnhancedFormSubmitter = BulletproofFormSubmitter
