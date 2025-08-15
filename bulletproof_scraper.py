#!/usr/bin/env python3
"""
Fixed Bulletproof Form Scraper
Resolves import issues and connection problems
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
        self._browser_created = False
        self._session_created = False
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
    def _safe_import_drissionpage(self):
        """Safely import DrissionPage with better error handling"""
        try:
            from DrissionPage import ChromiumPage, ChromiumOptions, SessionPage
            logger.debug("✅ DrissionPage imported successfully")
            return ChromiumPage, ChromiumOptions, SessionPage, True
        except ImportError as e:
            logger.error(f"❌ DrissionPage not available: {e}")
            logger.error("Install with: pip install DrissionPage")
            return None, None, None, False
        except Exception as e:
            logger.error(f"❌ Error importing DrissionPage: {e}")
            return None, None, None, False
    
    def _create_safe_options(self):
        """Create browser options with Docker-specific fixes"""
        ChromiumPage, ChromiumOptions, SessionPage, available = self._safe_import_drissionpage()
        
        if not available or not ChromiumOptions:
            return None
            
        try:
            co = ChromiumOptions()
            
            # CRITICAL DOCKER FLAGS (from forum post)
            docker_args = [
                '--no-sandbox',                    # ESSENTIAL for root in Docker
                '--disable-dev-shm-usage',         # Shared memory issues
                '--disable-gpu',                   # GPU not available in container
                '--disable-software-rasterizer',   # Software rendering issues
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-web-security',          # Cross-origin issues
                '--disable-features=TranslateUI',
                '--disable-extensions',
                '--disable-component-extensions-with-background-pages',
                '--disable-default-apps',
                '--mute-audio',
                '--no-first-run',
                '--disable-background-networking',
                '--disable-sync',                  # No Google sync
                '--disable-default-browser-check',
                '--disable-popup-blocking',
                '--disable-translate',
                '--disable-plugins',
                '--disable-images',                # Speed up loading
                '--disable-javascript',            # We just need form structure
                '--disable-css',                  # Speed up loading
                '--virtual-time-budget=1000'      # Speed up page load
            ]
            
            # Add all Docker-specific arguments
            for arg in docker_args:
                try:
                    co.set_argument(arg)
                    logger.debug(f"✅ Added Docker arg: {arg}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to add arg {arg}: {e}")
            
            # Headless mode
            if self.headless:
                try:
                    co.headless(True)
                    logger.debug("✅ Headless mode enabled")
                except Exception as e:
                    logger.debug(f"⚠️ Headless mode failed: {e}")
            
            # User agent
            user_agent = random.choice(self.user_agents)
            try:
                co.set_user_agent(user_agent)
                logger.debug("✅ User agent set")
            except Exception as e:
                logger.debug(f"⚠️ User agent failed: {e}")
            
            # Performance optimizations
            try:
                co.no_imgs(True)
                co.mute(True)
                logger.debug("✅ Performance optimizations applied")
            except Exception as e:
                logger.debug(f"⚠️ Performance options failed: {e}")
            
            return co
            
        except Exception as e:
            logger.error(f"❌ Failed to create ChromiumOptions: {e}")
            return None
    
    async def _safe_create_browser(self):
        """Safely create browser with extensive fallbacks and timeout"""
        ChromiumPage, ChromiumOptions, SessionPage, available = self._safe_import_drissionpage()
        
        if not available:
            raise Exception("DrissionPage not available")
        
        # Prevent multiple browser creation
        if self._browser_created:
            return self.browser_page
        
        try:
            logger.info("🚀 Creating browser instance...")
            
            # Try with options first
            options = self._create_safe_options()
            if options and self.use_stealth:
                try:
                    browser = ChromiumPage(options)
                    # Test the browser
                    await asyncio.sleep(1)
                    browser.get('about:blank')
                    logger.info("✅ Browser created with stealth options")
                    self._browser_created = True
                    return browser
                except Exception as e:
                    logger.warning(f"⚠️ Failed to create browser with options: {e}")
                    try:
                        browser.quit()
                    except:
                        pass
            
            # Fallback to basic browser
            try:
                browser = ChromiumPage()
                await asyncio.sleep(1)
                browser.get('about:blank')
                logger.info("✅ Basic browser created")
                self._browser_created = True
                return browser
            except Exception as e:
                logger.error(f"❌ Failed to create basic browser: {e}")
                raise
                
        except Exception as e:
            logger.error(f"❌ Complete browser creation failure: {e}")
            self._browser_created = False
            raise
    
    async def _safe_create_session(self):
        """Safely create session page with timeout"""
        ChromiumPage, ChromiumOptions, SessionPage, available = self._safe_import_drissionpage()
        
        if not available:
            raise Exception("DrissionPage not available")
        
        # Prevent multiple session creation
        if self._session_created:
            return self.session_page
        
        try:
            logger.debug("🔗 Creating session instance...")
            session = SessionPage()
            
            # Set headers
            user_agent = random.choice(self.user_agents)
            try:
                session.set_headers({'User-Agent': user_agent})
                logger.debug("✅ Session headers set")
            except Exception as e:
                logger.debug(f"⚠️ Failed to set session headers: {e}")
            
            self._session_created = True
            logger.debug("✅ Session created")
            return session
            
        except Exception as e:
            logger.error(f"❌ Session creation failed: {e}")
            self._session_created = False
            raise
    
    async def test_url_accessibility_enhanced(self, url: str) -> Dict[str, Any]:
        """Enhanced URL accessibility test with better error handling"""
        try:
            logger.info(f"🧪 Testing accessibility for: {url}")
            
            # Default response
            result = {
                'accessible': True,
                'status_code': 200,
                'method_used': 'unknown',
                'barriers': [],
                'success_probability': 0.5,
                'recommendations': ['Basic connectivity check'],
                'forms_found': 0,
                'final_url': url
            }
            
            # Try session method first (faster)
            session_success = False
            try:
                if not self.session_page:
                    self.session_page = await self._safe_create_session()
                
                logger.debug("📡 Testing with HTTP session...")
                response = self.session_page.get(url, timeout=15)
                content = self.session_page.html or ""
                actual_url = getattr(self.session_page, 'url', url)
                
                barriers = self._safe_detect_barriers(content, 200)
                forms = self._safe_count_forms(content)
                
                result.update({
                    'method_used': 'http_session',
                    'barriers': barriers,
                    'forms_found': forms,
                    'final_url': actual_url,
                    'success_probability': 0.9 if not barriers else 0.6,
                    'recommendations': ['Session method successful'] + (
                        [f'Found {forms} forms'] if forms > 0 else ['No forms detected']
                    )
                })
                
                session_success = True
                logger.info(f"✅ Session test successful - Forms: {forms}, Barriers: {len(barriers)}")
                
            except Exception as e:
                logger.debug(f"⚠️ Session test failed: {e}")
                result['warnings'] = [f'Session method failed: {str(e)[:100]}']
            
            # Try browser method if session failed or found barriers
            if not session_success or result.get('barriers'):
                try:
                    logger.debug("🌐 Testing with browser automation...")
                    if not self.browser_page:
                        self.browser_page = await self._safe_create_browser()
                    
                    self.browser_page.get(url)
                    await asyncio.sleep(3)  # Wait for JS/dynamic content
                    
                    content = self.browser_page.html or ""
                    actual_url = self.browser_page.url
                    
                    barriers = self._safe_detect_barriers(content, 200)
                    forms = self._safe_count_forms(content)
                    
                    result.update({
                        'method_used': 'browser_automation',
                        'final_url': actual_url,
                        'barriers': barriers,
                        'forms_found': forms,
                        'success_probability': 0.8 if not barriers else 0.4,
                        'recommendations': ['Browser method used'] + (
                            [f'Found {forms} forms'] if forms > 0 else ['No forms detected - may need JavaScript']
                        )
                    })
                    
                    logger.info(f"✅ Browser test completed - Forms: {forms}, Barriers: {len(barriers)}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Browser test failed: {e}")
                    result.update({
                        'method_used': 'fallback',
                        'barriers': ['browser_failed'],
                        'success_probability': 0.2,
                        'recommendations': [f'Both methods failed. Error: {str(e)[:100]}']
                    })
            
            return result
                
        except Exception as e:
            logger.error(f"❌ Complete accessibility test failure: {e}")
            return {
                'accessible': False,
                'error': f"Accessibility test failed: {str(e)[:200]}",
                'barriers': ['complete_failure'],
                'success_probability': 0.0,
                'recommendations': ['Check URL validity and network connectivity'],
                'method_used': 'error'
            }
    
    async def analyze_page_comprehensive_enhanced(self, url: str) -> Dict[str, Any]:
        """Enhanced page analysis with better error handling"""
        try:
            logger.info(f"🔍 Analyzing page: {url}")
            
            # Get accessibility first
            access_result = await self.test_url_accessibility_enhanced(url)
            
            # Base response
            result = {
                'success': access_result.get('accessible', False),
                'method_used': access_result.get('method_used', 'unknown'),
                'title': 'Unknown Title',
                'url': access_result.get('final_url', url),
                'forms_count': access_result.get('forms_found', 0),
                'forms_analysis': [],
                'accessibility': access_result,
                'page_type': 'unknown',
                'recommendations': access_result.get('recommendations', [])
            }
            
            # Enhanced analysis if accessible
            if access_result.get('accessible', False):
                try:
                    content = None
                    method = access_result.get('method_used')
                    
                    # Get content based on successful method
                    if method == 'http_session' and self.session_page:
                        try:
                            content = self.session_page.html
                            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
                            if title_match:
                                result['title'] = title_match.group(1).strip()[:200]
                        except Exception as e:
                            logger.debug(f"⚠️ Session content extraction failed: {e}")
                    
                    elif method == 'browser_automation' and self.browser_page:
                        try:
                            content = self.browser_page.html
                            try:
                                title_elem = self.browser_page.ele('tag:title', timeout=2)
                                if title_elem and title_elem.text:
                                    result['title'] = title_elem.text.strip()[:200]
                            except:
                                # Fallback to regex
                                title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
                                if title_match:
                                    result['title'] = title_match.group(1).strip()[:200]
                        except Exception as e:
                            logger.debug(f"⚠️ Browser content extraction failed: {e}")
                    
                    # Analyze content if available
                    if content:
                        result['page_type'] = self._determine_page_type_safe(content, result['forms_count'])
                        
                        if result['forms_count'] > 0:
                            forms_analysis = self._safe_analyze_forms(content)
                            result['forms_analysis'] = forms_analysis
                            if forms_analysis:
                                result['recommendations'].append(f"Analyzed {len(forms_analysis)} forms successfully")
                
                except Exception as e:
                    logger.warning(f"⚠️ Enhanced analysis failed: {e}")
                    result['recommendations'].append(f"Analysis limited: {str(e)[:100]}")
            
            logger.info(f"✅ Analysis complete - Forms: {result['forms_count']}, Type: {result['page_type']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Page analysis failed completely: {e}")
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
        """Enhanced form field extraction with better error handling"""
        try:
            logger.info(f"📝 Extracting form fields from: {url} (form #{form_index})")
            
            # Base response
            result = {
                'success': False,
                'method_used': 'unknown',
                'fields': [],
                'form_action': url,
                'form_method': 'POST',
                'form_index': form_index,
                'error': None
            }
            
            # Analyze page first
            analysis = await self.analyze_page_comprehensive_enhanced(url)
            
            if not analysis.get('success', False):
                result['error'] = 'Page not accessible or analysis failed'
                return result
            
            if analysis.get('forms_count', 0) == 0:
                result['error'] = 'No forms found on page'
                return result
            
            if form_index >= analysis.get('forms_count', 0):
                result['error'] = f'Form index {form_index} not found. Page has {analysis.get("forms_count", 0)} forms.'
                return result
            
            # Extract fields using successful method
            method = analysis.get('method_used', 'browser_automation')
            
            try:
                if method == 'http_session' and self.session_page:
                    fields = await self._extract_fields_with_session_safe(url, form_index)
                elif method == 'browser_automation' and self.browser_page:
                    fields = await self._extract_fields_with_browser_safe(url, form_index)
                else:
                    # Fallback: try both methods
                    try:
                        if not self.session_page:
                            self.session_page = await self._safe_create_session()
                        fields = await self._extract_fields_with_session_safe(url, form_index)
                        method = 'http_session_fallback'
                    except:
                        if not self.browser_page:
                            self.browser_page = await self._safe_create_browser()
                        fields = await self._extract_fields_with_browser_safe(url, form_index)
                        method = 'browser_automation_fallback'
                
                result.update({
                    'success': True,
                    'method_used': method,
                    'fields': fields,
                    'error': None
                })
                
                logger.info(f"✅ Extracted {len(fields)} fields using {method}")
                return result
                
            except Exception as e:
                result['error'] = f"Field extraction failed: {str(e)[:200]}"
                logger.error(f"❌ Field extraction error: {e}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Complete field extraction failure: {e}")
            return {
                'success': False,
                'error': f"Extraction system error: {str(e)[:200]}",
                'method_used': 'error',
                'fields': [],
                'form_action': url,
                'form_method': 'POST',
                'form_index': form_index
            }
    
    # Helper methods (keeping existing logic but with better error handling)
    def _safe_detect_barriers(self, content: str, status_code: int) -> List[str]:
        """Safely detect barriers"""
        try:
            barriers = []
            if not content:
                return ['no_content']
                
            content_lower = content.lower()
            
            # Check for common barriers
            barrier_checks = [
                (lambda: status_code >= 400, f"http_error_{status_code}"),
                (lambda: any(word in content_lower for word in ['captcha', 'recaptcha', 'hcaptcha']), "captcha_detected"),
                (lambda: 'cloudflare' in content_lower and 'checking' in content_lower, "cloudflare_challenge"),
                (lambda: any(word in content_lower for word in ['login', 'signin']) and 'password' in content_lower, "login_required"),
                (lambda: 'access denied' in content_lower or 'forbidden' in content_lower, "access_denied")
            ]
            
            for check, barrier_name in barrier_checks:
                try:
                    if check():
                        barriers.append(barrier_name)
                except:
                    continue
            
            return barriers
        except Exception as e:
            logger.debug(f"⚠️ Barrier detection failed: {e}")
            return ['detection_failed']
    
    def _safe_count_forms(self, content: str) -> int:
        """Safely count forms"""
        try:
            if not content:
                return 0
            # More robust form detection
            form_pattern = r'<form[^>]*>.*?</form>'
            forms = re.findall(form_pattern, content, re.IGNORECASE | re.DOTALL)
            return len(forms)
        except Exception as e:
            logger.debug(f"⚠️ Form counting failed: {e}")
            return 0
    
    def _determine_page_type_safe(self, content: str, form_count: int) -> str:
        """Safely determine page type"""
        try:
            if form_count == 0:
                return 'no_forms'
            
            content_lower = content.lower()
            
            # Page type detection with more keywords
            type_keywords = [
                (['contact', 'message', 'inquiry', 'reach out', 'get in touch'], 'contact_form'),
                (['job', 'career', 'application', 'apply', 'position'], 'job_application'),
                (['register', 'signup', 'sign up', 'create account'], 'registration'),
                (['login', 'signin', 'sign in', 'log in'], 'login'),
                (['subscribe', 'newsletter', 'email list'], 'subscription'),
                (['feedback', 'review', 'comment', 'survey'], 'feedback')
            ]
            
            for keywords, page_type in type_keywords:
                if any(keyword in content_lower for keyword in keywords):
                    return page_type
            
            return 'general_form'
        except Exception as e:
            logger.debug(f"⚠️ Page type detection failed: {e}")
            return 'unknown'
    
    def _safe_analyze_forms(self, content: str) -> List[Dict[str, Any]]:
        """Safely analyze forms in content"""
        try:
            forms = []
            form_pattern = r'<form[^>]*>(.*?)</form>'
            form_matches = re.finditer(form_pattern, content, re.IGNORECASE | re.DOTALL)
            
            for i, match in enumerate(form_matches):
                try:
                    form_html = match.group(0)
                    
                    # Extract form attributes
                    action_match = re.search(r'action=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
                    method_match = re.search(r'method=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
                    
                    # Count different field types
                    input_count = len(re.findall(r'<input[^>]*>', form_html, re.IGNORECASE))
                    textarea_count = len(re.findall(r'<textarea[^>]*>', form_html, re.IGNORECASE))
                    select_count = len(re.findall(r'<select[^>]*>', form_html, re.IGNORECASE))
                    
                    # Detect special features
                    has_file = bool(re.search(r'type=["\']file["\']', form_html, re.IGNORECASE))
                    has_required = bool(re.search(r'\brequired\b', form_html, re.IGNORECASE))
                    has_validation = bool(re.search(r'pattern=|maxlength=|minlength=', form_html, re.IGNORECASE))
                    
                    form_info = {
                        'index': i,
                        'action': action_match.group(1) if action_match else '',
                        'method': method_match.group(1).upper() if method_match else 'GET',
                        'field_count': input_count + textarea_count + select_count,
                        'input_count': input_count,
                        'textarea_count': textarea_count,
                        'select_count': select_count,
                        'has_file_upload': has_file,
                        'has_required_fields': has_required,
                        'has_validation': has_validation
                    }
                    
                    forms.append(form_info)
                    
                except Exception as e:
                    logger.debug(f"⚠️ Error analyzing form {i}: {e}")
                    continue
            
            return forms
        except Exception as e:
            logger.debug(f"⚠️ Form analysis failed: {e}")
            return []
    
    async def _extract_fields_with_session_safe(self, url: str, form_index: int) -> List[Dict[str, Any]]:
        """Safely extract fields using session"""
        try:
            self.session_page.get(url)
            content = self.session_page.html
            
            if not content:
                return []
            
            # Parse forms from HTML
            form_pattern = r'<form[^>]*>(.*?)</form>'
            form_matches = list(re.finditer(form_pattern, content, re.IGNORECASE | re.DOTALL))
            
            if form_index >= len(form_matches):
                return []
            
            form_html = form_matches[form_index].group(0)
            return self._parse_fields_from_html(form_html)
            
        except Exception as e:
            logger.debug(f"⚠️ Session field extraction failed: {e}")
            return []
    
    async def _extract_fields_with_browser_safe(self, url: str, form_index: int) -> List[Dict[str, Any]]:
        """Safely extract fields using browser with FIXED selectors"""
        try:
            self.browser_page.get(url)
            await asyncio.sleep(2)  # Wait for dynamic content
            
            # Use CSS selectors instead of tag selectors (FIXED!)
            forms = self.browser_page.eles('css:form')
            if form_index >= len(forms):
                return []
            
            form = forms[form_index]
            fields = []
            
            # Get elements using CSS selectors (this is the fix!)
            input_elements = form.eles('css:input')
            textarea_elements = form.eles('css:textarea')
            select_elements = form.eles('css:select')
            
            # Process input elements
            for element in input_elements:
                try:
                    field_type = element.attr('type') or 'text'
                    if field_type.lower() in ['hidden', 'submit', 'button']:
                        continue
                    
                    field_data = {
                        'tag': 'input',
                        'type': field_type,
                        'name': element.attr('name') or '',
                        'id': element.attr('id') or '',
                        'identifier': element.attr('id') or element.attr('name') or f'input_{len(fields)}',
                        'placeholder': element.attr('placeholder') or '',
                        'required': element.attr('required') is not None,
                        'label': self._safe_find_label(element),
                        'value': element.attr('value') or '',
                        'maxlength': element.attr('maxlength') or '',
                        'pattern': element.attr('pattern') or ''
                    }
                    
                    fields.append(field_data)
                    
                except Exception as e:
                    logger.debug(f"⚠️ Input field extraction error: {e}")
                    continue
            
            # Process textarea elements  
            for element in textarea_elements:
                try:
                    field_data = {
                        'tag': 'textarea',
                        'type': 'textarea',
                        'name': element.attr('name') or '',
                        'id': element.attr('id') or '',
                        'identifier': element.attr('id') or element.attr('name') or f'textarea_{len(fields)}',
                        'placeholder': element.attr('placeholder') or '',
                        'required': element.attr('required') is not None,
                        'label': self._safe_find_label(element),
                        'value': element.text or '',
                        'maxlength': element.attr('maxlength') or '',
                        'pattern': ''
                    }
                    
                    fields.append(field_data)
                    
                except Exception as e:
                    logger.debug(f"⚠️ Textarea field extraction error: {e}")
                    continue
            
            # Process select elements
            for element in select_elements:
                try:
                    # Get select options
                    options = []
                    try:
                        option_elements = element.eles('css:option')
                        options = [
                            {
                                'value': opt.attr('value') or '',
                                'text': opt.text or '',
                                'selected': opt.attr('selected') is not None
                            } for opt in option_elements
                        ]
                    except:
                        options = []
                    
                    field_data = {
                        'tag': 'select',
                        'type': 'select',
                        'name': element.attr('name') or '',
                        'id': element.attr('id') or '',
                        'identifier': element.attr('id') or element.attr('name') or f'select_{len(fields)}',
                        'placeholder': '',
                        'required': element.attr('required') is not None,
                        'label': self._safe_find_label(element),
                        'value': '',
                        'maxlength': '',
                        'pattern': '',
                        'options': options
                    }
                    
                    fields.append(field_data)
                    
                except Exception as e:
                    logger.debug(f"⚠️ Select field extraction error: {e}")
                    continue
            
            return fields
            
        except Exception as e:
            logger.debug(f"⚠️ Browser field extraction failed: {e}")
            return []
    
    def _parse_fields_from_html(self, form_html: str) -> List[Dict[str, Any]]:
        """Parse form fields from HTML string with enhanced detection"""
        try:
            fields = []
            
            # Enhanced input field detection
            input_pattern = r'<input[^>]*>'
            input_matches = re.finditer(input_pattern, form_html, re.IGNORECASE)
            
            for match in input_matches:
                input_tag = match.group(0)
                
                # Extract attributes with better regex
                attrs = {}
                attr_patterns = [
                    ('type', r'type=["\']([^"\']*)["\']'),
                    ('name', r'name=["\']([^"\']*)["\']'),
                    ('id', r'id=["\']([^"\']*)["\']'),
                    ('placeholder', r'placeholder=["\']([^"\']*)["\']'),
                    ('value', r'value=["\']([^"\']*)["\']'),
                    ('maxlength', r'maxlength=["\']([^"\']*)["\']'),
                    ('pattern', r'pattern=["\']([^"\']*)["\']')
                ]
                
                for attr_name, pattern in attr_patterns:
                    match_obj = re.search(pattern, input_tag, re.IGNORECASE)
                    attrs[attr_name] = match_obj.group(1) if match_obj else ''
                
                field_type = attrs['type'] or 'text'
                
                if field_type.lower() in ['hidden', 'submit', 'button', 'image', 'reset']:
                    continue
                
                field_name = attrs['name']
                field_id = attrs['id']
                
                field_data = {
                    'tag': 'input',
                    'type': field_type,
                    'name': field_name,
                    'id': field_id,
                    'identifier': field_id or field_name or f'field_{len(fields)}',
                    'placeholder': attrs['placeholder'],
                    'required': 'required' in input_tag.lower(),
                    'label': self._generate_label_from_name(field_name or field_id),
                    'value': attrs['value'],
                    'maxlength': attrs['maxlength'],
                    'pattern': attrs['pattern']
                }
                
                fields.append(field_data)
            
            # Add textarea fields
            textarea_pattern = r'<textarea[^>]*>.*?</textarea>'
            textarea_matches = re.finditer(textarea_pattern, form_html, re.IGNORECASE | re.DOTALL)
            
            for match in textarea_matches:
                textarea_tag = match.group(0)
                
                name_match = re.search(r'name=["\']([^"\']*)["\']', textarea_tag, re.IGNORECASE)
                id_match = re.search(r'id=["\']([^"\']*)["\']', textarea_tag, re.IGNORECASE)
                placeholder_match = re.search(r'placeholder=["\']([^"\']*)["\']', textarea_tag, re.IGNORECASE)
                
                field_name = name_match.group(1) if name_match else ''
                field_id = id_match.group(1) if id_match else ''
                
                field_data = {
                    'tag': 'textarea',
                    'type': 'textarea',
                    'name': field_name,
                    'id': field_id,
                    'identifier': field_id or field_name or f'textarea_{len(fields)}',
                    'placeholder': placeholder_match.group(1) if placeholder_match else '',
                    'required': 'required' in textarea_tag.lower(),
                    'label': self._generate_label_from_name(field_name or field_id),
                    'value': '',
                    'maxlength': '',
                    'pattern': ''
                }
                
                fields.append(field_data)
            
            return fields
            
        except Exception as e:
            logger.debug(f"⚠️ HTML field parsing failed: {e}")
            return []
    
    def _safe_find_label(self, element) -> str:
        """Safely find label for an element"""
        try:
            # Try multiple methods to find label
            methods = [
                lambda: self._find_label_by_for(element),
                lambda: element.attr('aria-label'),
                lambda: element.attr('placeholder'),
                lambda: self._generate_label_from_name(element.attr('name') or element.attr('id'))
            ]
            
            for method in methods:
                try:
                    label = method()
                    if label and label.strip():
                        return label.strip()
                except:
                    continue
            
            return 'Unnamed field'
            
        except Exception as e:
            logger.debug(f"⚠️ Label finding failed: {e}")
            return 'Unnamed field'
    
    def _find_label_by_for(self, element) -> str:
        """Find label using for attribute"""
        try:
            field_id = element.attr('id')
            if field_id:
                label = element.parent().ele(f'css:label[for="{field_id}"]', timeout=1)
                if label and label.text:
                    return label.text.strip()
        except:
            pass
        return ''
    
    def _generate_label_from_name(self, name: str) -> str:
        """Generate human-readable label from field name"""
        if not name:
            return 'Unnamed field'
        
        # Clean up the name
        label = name.replace('_', ' ').replace('-', ' ')
        label = re.sub(r'([a-z])([A-Z])', r'\1 \2', label)  # camelCase to words
        return label.title()
    
    async def close(self):
        """Enhanced cleanup with better error handling"""
        try:
            cleanup_tasks = []
            
            if self.browser_page:
                try:
                    self.browser_page.quit()
                    logger.debug("✅ Browser cleaned up")
                except Exception as e:
                    logger.debug(f"⚠️ Browser cleanup error: {e}")
                finally:
                    self.browser_page = None
                    self._browser_created = False
            
            if self.session_page:
                try:
                    self.session_page.close()
                    logger.debug("✅ Session cleaned up")
                except Exception as e:
                    logger.debug(f"⚠️ Session cleanup error: {e}")
                finally:
                    self.session_page = None
                    self._session_created = False
            
        except Exception as e:
            logger.debug(f"⚠️ General cleanup error: {e}")

# Alias for compatibility
EnhancedFormScraper = BulletproofFormScraper
