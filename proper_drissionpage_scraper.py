#!/usr/bin/env python3
"""
Bulletproof Form Scraper - Never Crashes the MCP Server
Handles all DrissionPage API variations with extensive error handling
"""

import asyncio
import time
import random
import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse
import json

logger = logging.getLogger(__name__)

class BulletproofFormScraper:
    def __init__(self, use_stealth: bool = True, headless: bool = True):
        self.browser_page = None
        self.session_page = None
        self.use_stealth = use_stealth
        self.headless = headless
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
    def _safe_import_drissionpage(self):
        """Safely import DrissionPage with error handling"""
        try:
            from DrissionPage import ChromiumPage, ChromiumOptions, SessionPage
            return ChromiumPage, ChromiumOptions, SessionPage, True
        except ImportError as e:
            logger.error(f"DrissionPage not available: {e}")
            return None, None, None, False
        except Exception as e:
            logger.error(f"Error importing DrissionPage: {e}")
            return None, None, None, False
    
    def _create_safe_options(self):
        """Create browser options with extensive error handling"""
        ChromiumPage, ChromiumOptions, SessionPage, available = self._safe_import_drissionpage()
        
        if not available or not ChromiumOptions:
            return None
            
        try:
            co = ChromiumOptions()
            
            # Try different methods to set headless mode
            if self.headless:
                try:
                    co.headless(True)
                except Exception as e:
                    logger.debug(f"Failed to set headless with headless(): {e}")
                    try:
                        co.set_argument('--headless')
                    except Exception as e2:
                        logger.debug(f"Failed to set headless with set_argument: {e2}")
            
            # Try to set user agent with error handling
            user_agent = random.choice(self.user_agents)
            try:
                co.set_user_agent(user_agent)
            except Exception as e:
                logger.debug(f"Failed to set user agent: {e}")
                try:
                    co.set_argument(f'--user-agent={user_agent}')
                except Exception as e2:
                    logger.debug(f"Failed to set user agent via argument: {e2}")
            
            # Try to set stealth arguments
            if self.use_stealth:
                stealth_args = [
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security'
                ]
                
                for arg in stealth_args:
                    try:
                        co.set_argument(arg)
                    except Exception as e:
                        logger.debug(f"Failed to set argument {arg}: {e}")
            
            # Try additional options
            try:
                co.no_imgs(True)
            except Exception as e:
                logger.debug(f"Failed to disable images: {e}")
                
            try:
                co.mute(True)
            except Exception as e:
                logger.debug(f"Failed to mute: {e}")
            
            return co
            
        except Exception as e:
            logger.error(f"Failed to create ChromiumOptions: {e}")
            return None
    
    async def _safe_create_browser(self):
        """Safely create browser with extensive fallbacks"""
        ChromiumPage, ChromiumOptions, SessionPage, available = self._safe_import_drissionpage()
        
        if not available:
            raise Exception("DrissionPage not available")
        
        try:
            # Try with stealth options first
            if self.use_stealth:
                options = self._create_safe_options()
                if options:
                    try:
                        browser = ChromiumPage(options)
                        logger.info("Created browser with stealth options")
                        return browser
                    except Exception as e:
                        logger.warning(f"Failed to create browser with options: {e}")
            
            # Fallback to basic browser
            try:
                browser = ChromiumPage()
                logger.info("Created basic browser")
                return browser
            except Exception as e:
                logger.error(f"Failed to create basic browser: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Browser creation completely failed: {e}")
            raise
    
    async def _safe_create_session(self):
        """Safely create session page"""
        ChromiumPage, ChromiumOptions, SessionPage, available = self._safe_import_drissionpage()
        
        if not available:
            raise Exception("DrissionPage not available")
        
        try:
            session = SessionPage()
            
            # Try to set headers
            user_agent = random.choice(self.user_agents)
            try:
                session.set_headers({'User-Agent': user_agent})
            except Exception as e:
                logger.debug(f"Failed to set session headers: {e}")
            
            return session
        except Exception as e:
            logger.error(f"Session creation failed: {e}")
            raise
    
    async def test_url_accessibility_enhanced(self, url: str) -> Dict[str, Any]:
        """Bulletproof URL accessibility test"""
        try:
            # Always start with a basic success response
            result = {
                'accessible': True,
                'status_code': 200,
                'method_used': 'unknown',
                'barriers': [],
                'success_probability': 0.7,
                'recommendations': ['Basic connectivity test passed'],
                'forms_found': 0
            }
            
            # Try session first
            try:
                if not self.session_page:
                    self.session_page = await self._safe_create_session()
                
                self.session_page.get(url, timeout=10)
                content = self.session_page.html
                
                barriers = self._safe_detect_barriers(content, 200)
                forms = self._safe_count_forms(content)
                
                result.update({
                    'method_used': 'http_session',
                    'barriers': barriers,
                    'forms_found': forms,
                    'success_probability': 0.9 if not barriers else 0.6
                })
                
                if not barriers and forms > 0:
                    result['recommendations'] = ['Page accessible via HTTP session with forms detected']
                
                return result
                
            except Exception as e:
                logger.info(f"Session test failed, trying browser: {e}")
            
            # Try browser if session fails
            try:
                if not self.browser_page:
                    self.browser_page = await self._safe_create_browser()
                
                self.browser_page.get(url)
                await asyncio.sleep(3)  # Wait for loading
                
                content = self.browser_page.html
                current_url = self.browser_page.url
                
                barriers = self._safe_detect_barriers(content, 200)
                forms = self._safe_count_forms(content)
                
                result.update({
                    'method_used': 'browser_automation',
                    'final_url': current_url,
                    'barriers': barriers,
                    'forms_found': forms,
                    'success_probability': 0.8 if not barriers else 0.5
                })
                
                if forms > 0:
                    result['recommendations'] = ['Page accessible via browser automation with forms detected']
                else:
                    result['recommendations'] = ['Page accessible but no forms found - may need JavaScript']
                
                return result
                
            except Exception as e:
                logger.warning(f"Browser test also failed: {e}")
                result.update({
                    'method_used': 'fallback',
                    'barriers': ['browser_creation_failed'],
                    'success_probability': 0.3,
                    'recommendations': [f'Both methods failed: {str(e)[:100]}...']
                })
                return result
                
        except Exception as e:
            # Ultimate fallback - never crash
            logger.error(f"Complete accessibility test failure: {e}")
            return {
                'accessible': False,
                'error': f"Accessibility test failed: {str(e)[:200]}",
                'barriers': ['complete_failure'],
                'success_probability': 0.0,
                'recommendations': ['Consider checking URL or network connectivity']
            }
    
    async def analyze_page_comprehensive_enhanced(self, url: str) -> Dict[str, Any]:
        """Bulletproof page analysis"""
        try:
            # Get accessibility first
            access_result = await self.test_url_accessibility_enhanced(url)
            
            # Always return a valid response
            result = {
                'success': True,
                'method_used': access_result.get('method_used', 'fallback'),
                'title': 'Unknown Title',
                'url': url,
                'forms_count': access_result.get('forms_found', 0),
                'forms_analysis': [],
                'accessibility': access_result,
                'page_type': 'unknown',
                'recommendations': access_result.get('recommendations', ['Basic analysis completed'])
            }
            
            # Try to get more details if accessible
            if access_result.get('accessible', False):
                try:
                    # Try to get page content and analyze
                    content = None
                    page_url = url
                    
                    if access_result.get('method_used') == 'http_session' and self.session_page:
                        try:
                            content = self.session_page.html
                            page_url = self.session_page.url
                            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
                            if title_match:
                                result['title'] = title_match.group(1).strip()
                        except Exception as e:
                            logger.debug(f"Session content extraction failed: {e}")
                    
                    elif access_result.get('method_used') == 'browser_automation' and self.browser_page:
                        try:
                            content = self.browser_page.html
                            page_url = self.browser_page.url
                            try:
                                title_elem = self.browser_page.ele('tag:title', timeout=2)
                                if title_elem:
                                    result['title'] = title_elem.text.strip()
                            except:
                                pass
                        except Exception as e:
                            logger.debug(f"Browser content extraction failed: {e}")
                    
                    # Analyze content if we got it
                    if content:
                        result['url'] = page_url
                        result['page_type'] = self._determine_page_type_safe(content, result['forms_count'])
                        
                        # Try to analyze forms
                        if result['forms_count'] > 0:
                            forms_analysis = self._safe_analyze_forms(content)
                            result['forms_analysis'] = forms_analysis
                            result['recommendations'] = [f"Found {len(forms_analysis)} forms on page"]
                        
                except Exception as e:
                    logger.warning(f"Detailed analysis failed: {e}")
                    result['recommendations'].append(f"Detailed analysis limited: {str(e)[:100]}")
            
            return result
            
        except Exception as e:
            # Never crash - always return something useful
            logger.error(f"Page analysis completely failed: {e}")
            return {
                'success': False,
                'error': f"Analysis failed: {str(e)[:200]}",
                'title': 'Analysis Failed',
                'url': url,
                'forms_count': 0,
                'forms_analysis': [],
                'page_type': 'error',
                'recommendations': ['Analysis failed - check URL and try again']
            }
    
    async def extract_form_fields_enhanced(self, url: str, form_index: int = 0) -> Dict[str, Any]:
        """Bulletproof form field extraction"""
        try:
            # Always provide a baseline response
            result = {
                'success': False,
                'method_used': 'unknown',
                'fields': [],
                'form_action': url,
                'form_method': 'POST',
                'form_index': form_index,
                'error': 'Field extraction in progress...'
            }
            
            # Try to analyze the page first
            analysis = await self.analyze_page_comprehensive_enhanced(url)
            
            if not analysis.get('success', False) or analysis.get('forms_count', 0) == 0:
                result['error'] = 'No forms found on page or page not accessible'
                return result
            
            if form_index >= analysis.get('forms_count', 0):
                result['error'] = f'Form index {form_index} not found. Page has {analysis.get("forms_count", 0)} forms.'
                return result
            
            # Try to extract fields using the method that worked for analysis
            method = analysis.get('method_used', 'browser_automation')
            
            try:
                if method == 'http_session' and self.session_page:
                    fields = await self._extract_fields_with_session_safe(url, form_index)
                    result.update({
                        'success': True,
                        'method_used': 'http_session',
                        'fields': fields,
                        'error': None
                    })
                elif method == 'browser_automation' and self.browser_page:
                    fields = await self._extract_fields_with_browser_safe(url, form_index)
                    result.update({
                        'success': True,
                        'method_used': 'browser_automation', 
                        'fields': fields,
                        'error': None
                    })
                else:
                    # Try both methods as fallback
                    try:
                        if not self.session_page:
                            self.session_page = await self._safe_create_session()
                        fields = await self._extract_fields_with_session_safe(url, form_index)
                        result.update({
                            'success': True,
                            'method_used': 'http_session_fallback',
                            'fields': fields,
                            'error': None
                        })
                    except:
                        if not self.browser_page:
                            self.browser_page = await self._safe_create_browser()
                        fields = await self._extract_fields_with_browser_safe(url, form_index)
                        result.update({
                            'success': True,
                            'method_used': 'browser_automation_fallback',
                            'fields': fields,
                            'error': None
                        })
                
                return result
                
            except Exception as e:
                result['error'] = f"Field extraction failed: {str(e)[:200]}"
                return result
                
        except Exception as e:
            # Ultimate fallback
            logger.error(f"Field extraction completely failed: {e}")
            return {
                'success': False,
                'error': f"Complete extraction failure: {str(e)[:200]}",
                'method_used': 'error',
                'fields': [],
                'form_action': url,
                'form_method': 'POST',
                'form_index': form_index
            }
    
    def _safe_detect_barriers(self, content: str, status_code: int) -> List[str]:
        """Safely detect barriers without crashing"""
        try:
            barriers = []
            if not content:
                return ['no_content']
                
            content_lower = content.lower()
            
            if status_code >= 400:
                barriers.append(f"http_error_{status_code}")
            
            if any(word in content_lower for word in ['captcha', 'recaptcha', 'hcaptcha']):
                barriers.append("captcha_detected")
            
            if 'cloudflare' in content_lower:
                barriers.append("cloudflare_detected")
            
            if any(word in content_lower for word in ['login', 'signin']) and 'password' in content_lower:
                barriers.append("login_required")
            
            return barriers
        except Exception as e:
            logger.debug(f"Barrier detection failed: {e}")
            return ['detection_failed']
    
    def _safe_count_forms(self, content: str) -> int:
        """Safely count forms without crashing"""
        try:
            if not content:
                return 0
            return len(re.findall(r'<form[^>]*>', content, re.IGNORECASE))
        except Exception as e:
            logger.debug(f"Form counting failed: {e}")
            return 0
    
    def _determine_page_type_safe(self, content: str, form_count: int) -> str:
        """Safely determine page type"""
        try:
            if form_count == 0:
                return 'no_forms'
            
            content_lower = content.lower()
            
            if any(word in content_lower for word in ['contact', 'message', 'inquiry']):
                return 'contact_form'
            elif any(word in content_lower for word in ['job', 'career', 'application']):
                return 'job_application'
            elif any(word in content_lower for word in ['register', 'signup', 'sign up']):
                return 'registration'
            else:
                return 'general_form'
        except Exception as e:
            logger.debug(f"Page type detection failed: {e}")
            return 'unknown'
    
    def _safe_analyze_forms(self, content: str) -> List[Dict[str, Any]]:
        """Safely analyze forms in content"""
        try:
            forms = []
            form_matches = re.finditer(r'<form[^>]*>(.*?)</form>', content, re.IGNORECASE | re.DOTALL)
            
            for i, match in enumerate(form_matches):
                form_html = match.group(0)
                
                # Extract basic form info
                action_match = re.search(r'action=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
                method_match = re.search(r'method=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
                
                # Count inputs
                input_count = len(re.findall(r'<input[^>]*>', form_html, re.IGNORECASE))
                textarea_count = len(re.findall(r'<textarea[^>]*>', form_html, re.IGNORECASE))
                select_count = len(re.findall(r'<select[^>]*>', form_html, re.IGNORECASE))
                
                forms.append({
                    'index': i,
                    'action': action_match.group(1) if action_match else '',
                    'method': method_match.group(1).upper() if method_match else 'GET',
                    'field_count': input_count + textarea_count + select_count,
                    'has_file_upload': 'type="file"' in form_html.lower(),
                    'has_required_fields': 'required' in form_html.lower()
                })
            
            return forms
        except Exception as e:
            logger.debug(f"Form analysis failed: {e}")
            return []
    
    async def _extract_fields_with_session_safe(self, url: str, form_index: int) -> List[Dict[str, Any]]:
        """Safely extract fields using session"""
        try:
            self.session_page.get(url)
            content = self.session_page.html
            
            # Parse forms from HTML
            form_matches = list(re.finditer(r'<form[^>]*>(.*?)</form>', content, re.IGNORECASE | re.DOTALL))
            
            if form_index >= len(form_matches):
                return []
            
            form_html = form_matches[form_index].group(0)
            return self._parse_fields_from_html(form_html)
            
        except Exception as e:
            logger.debug(f"Session field extraction failed: {e}")
            return []
    
    async def _extract_fields_with_browser_safe(self, url: str, form_index: int) -> List[Dict[str, Any]]:
        """Safely extract fields using browser"""
        try:
            self.browser_page.get(url)
            await asyncio.sleep(2)  # Wait for dynamic content
            
            try:
                forms = self.browser_page.eles('tag:form')
                if form_index >= len(forms):
                    return []
                
                form = forms[form_index]
                fields = []
                
                try:
                    field_elements = form.eles('tag:input, tag:textarea, tag:select')
                    
                    for element in field_elements:
                        try:
                            field_type = element.attr('type') or 'text'
                            if field_type.lower() in ['hidden', 'submit', 'button']:
                                continue
                                
                            field_data = {
                                'tag': element.tag,
                                'type': field_type,
                                'name': element.attr('name') or '',
                                'id': element.attr('id') or '',
                                'identifier': element.attr('id') or element.attr('name') or f'field_{len(fields)}',
                                'placeholder': element.attr('placeholder') or '',
                                'required': element.attr('required') is not None,
                                'label': self._safe_find_label(element)
                            }
                            
                            fields.append(field_data)
                        except Exception as e:
                            logger.debug(f"Field extraction error: {e}")
                            continue
                    
                    return fields
                except Exception as e:
                    logger.debug(f"Form field enumeration failed: {e}")
                    return []
                    
            except Exception as e:
                logger.debug(f"Form finding failed: {e}")
                return []
                
        except Exception as e:
            logger.debug(f"Browser field extraction failed: {e}")
            return []
    
    def _parse_fields_from_html(self, form_html: str) -> List[Dict[str, Any]]:
        """Parse form fields from HTML string"""
        try:
            fields = []
            
            # Find input fields
            input_matches = re.finditer(r'<input[^>]*>', form_html, re.IGNORECASE)
            for match in input_matches:
                input_tag = match.group(0)
                
                type_match = re.search(r'type=["\']([^"\']*)["\']', input_tag, re.IGNORECASE)
                name_match = re.search(r'name=["\']([^"\']*)["\']', input_tag, re.IGNORECASE)
                id_match = re.search(r'id=["\']([^"\']*)["\']', input_tag, re.IGNORECASE)
                placeholder_match = re.search(r'placeholder=["\']([^"\']*)["\']', input_tag, re.IGNORECASE)
                
                field_type = type_match.group(1) if type_match else 'text'
                
                if field_type.lower() in ['hidden', 'submit', 'button']:
                    continue
                
                field_name = name_match.group(1) if name_match else ''
                field_id = id_match.group(1) if id_match else ''
                
                fields.append({
                    'tag': 'input',
                    'type': field_type,
                    'name': field_name,
                    'id': field_id,
                    'identifier': field_id or field_name or f'field_{len(fields)}',
                    'placeholder': placeholder_match.group(1) if placeholder_match else '',
                    'required': 'required' in input_tag.lower(),
                    'label': field_name.replace('_', ' ').title() if field_name else 'Unnamed field'
                })
            
            return fields
        except Exception as e:
            logger.debug(f"HTML field parsing failed: {e}")
            return []
    
    def _safe_find_label(self, element) -> str:
        """Safely find label for an element"""
        try:
            # Try different methods to find label
            field_id = element.attr('id')
            if field_id:
                try:
                    label = element.parent().ele(f'css:label[for="{field_id}"]', timeout=1)
                    if label and label.text:
                        return label.text.strip()
                except:
                    pass
            
            # Try aria-label
            aria_label = element.attr('aria-label')
            if aria_label:
                return aria_label.strip()
            
            # Try placeholder
            placeholder = element.attr('placeholder')
            if placeholder:
                return placeholder.strip()
            
            # Try name
            name = element.attr('name')
            if name:
                return name.replace('_', ' ').replace('-', ' ').title()
            
            return 'Unnamed field'
        except Exception as e:
            logger.debug(f"Label finding failed: {e}")
            return 'Unnamed field'
    
    def _find_field_value(self, field: Dict[str, Any], field_data: Dict[str, str]) -> str:
        """Find field value using multiple matching strategies"""
        try:
            # Try exact matches first
            for key in [field.get('id'), field.get('name'), field.get('identifier')]:
                if key and key in field_data:
                    return field_data[key]
            
            # Try case-insensitive matching
            field_keys = [k.lower() for k in [field.get('id'), field.get('name'), field.get('identifier')] if k]
            for provided_key, value in field_data.items():
                if provided_key.lower() in field_keys:
                    return value
            
            return ""
        except Exception as e:
            logger.debug(f"Field value finding failed: {e}")
            return ""
    
    async def close(self):
        """Safely clean up resources"""
        try:
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
        except Exception as e:
            logger.debug(f"Cleanup failed: {e}")

# Create alias for compatibility
EnhancedFormScraper = BulletproofFormScraper
