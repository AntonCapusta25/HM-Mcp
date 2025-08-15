#!/usr/bin/env python3
"""
Ultra-Enhanced Form Scraper with DrissionPage
Handles Cloudflare, CAPTCHAs, login walls, and any other barriers
"""

import asyncio
import time
import random
import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse
import json
from contextlib import asynccontextmanager

# DrissionPage imports
from DrissionPage import ChromiumPage, ChromiumOptions, SessionPage
from DrissionPage.common import Actions
from DrissionPage.errors import ElementNotFoundError, PageDisconnectedError

logger = logging.getLogger(__name__)

class EnhancedFormScraper:
    def __init__(self, use_stealth: bool = True, headless: bool = True):
        self.browser_page = None
        self.session_page = None
        self.use_stealth = use_stealth
        self.headless = headless
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
    def _get_stealth_options(self) -> ChromiumOptions:
        """Configure stealth browser options for maximum anti-detection"""
        co = ChromiumOptions()
        
        # Basic stealth settings
        if self.headless:
            co.headless(True)
        
        # Anti-detection arguments
        co.add_argument('--no-sandbox')
        co.add_argument('--disable-blink-features=AutomationControlled')
        co.add_argument('--disable-features=VizDisplayCompositor')
        co.add_argument('--disable-dev-shm-usage')
        co.add_argument('--disable-gpu')
        co.add_argument('--disable-web-security')
        co.add_argument('--disable-features=site-per-process')
        co.add_argument('--no-first-run')
        co.add_argument('--no-service-autorun')
        co.add_argument('--no-default-browser-check')
        co.add_argument('--password-store=basic')
        co.add_argument('--use-mock-keychain')
        
        # Randomize user agent
        user_agent = random.choice(self.user_agents)
        co.set_user_agent(user_agent)
        
        # Randomize window size
        widths = [1366, 1920, 1440, 1536, 1024]
        heights = [768, 1080, 900, 864, 768]
        width = random.choice(widths)
        height = random.choice(heights)
        co.set_window_size(width, height)
        
        # Set additional preferences for stealth
        prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.popups': 0,
            'profile.managed_default_content_settings.images': 2,  # Block images for speed
            'profile.default_content_setting_values.media_stream': 2,
        }
        co.set_pref(prefs)
        
        return co
    
    async def _get_browser_page(self) -> ChromiumPage:
        """Get or create browser page with stealth configuration"""
        if self.browser_page is None or self.browser_page.states.is_alive is False:
            if self.use_stealth:
                options = self._get_stealth_options()
                self.browser_page = ChromiumPage(addr_or_opts=options)
            else:
                self.browser_page = ChromiumPage()
            
            # Additional stealth JavaScript injections
            if self.use_stealth:
                await self._inject_stealth_scripts()
        
        return self.browser_page
    
    async def _inject_stealth_scripts(self):
        """Inject JavaScript to enhance stealth capabilities"""
        stealth_scripts = [
            # Remove webdriver property
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            
            # Fake plugins
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5].map(() => ({ length: 4 }))
            });
            """,
            
            # Fake languages
            "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})",
            
            # Mock chrome object
            "window.chrome = { runtime: {} };",
            
            # Mock permissions
            """
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            """
        ]
        
        for script in stealth_scripts:
            try:
                self.browser_page.run_js(script)
            except Exception as e:
                logger.debug(f"Failed to inject stealth script: {e}")
    
    def _get_session_page(self) -> SessionPage:
        """Get or create session page for HTTP requests"""
        if self.session_page is None:
            self.session_page = SessionPage()
            # Set random user agent
            user_agent = random.choice(self.user_agents)
            self.session_page.set_user_agent(user_agent)
        
        return self.session_page
    
    async def test_url_accessibility_enhanced(self, url: str) -> Dict[str, Any]:
        """Enhanced URL accessibility test with Cloudflare detection and bypass"""
        try:
            # First try with fast HTTP session
            session = self._get_session_page()
            try:
                session.get(url, timeout=10)
                initial_status = session.response.status_code
                initial_content = session.html
                
                # Quick check for obvious barriers
                barriers = self._detect_barriers_in_content(initial_content, initial_status)
                
                if not barriers or barriers == ['minor_javascript_required']:
                    return {
                        'accessible': True,
                        'status_code': initial_status,
                        'method_used': 'http_session',
                        'barriers': barriers,
                        'success_probability': 0.9,
                        'recommendations': ['HTTP session access successful']
                    }
            except Exception as e:
                logger.debug(f"HTTP session failed: {e}")
            
            # If HTTP fails or barriers detected, try with browser
            browser = await self._get_browser_page()
            
            start_time = time.time()
            browser.get(url)
            
            # Wait for page to load and handle any challenges
            await self._handle_cloudflare_challenges(browser)
            
            load_time = time.time() - start_time
            current_url = browser.url
            content = browser.html
            
            # Comprehensive barrier detection
            barriers = self._detect_barriers_in_content(content, 200)
            success_indicators = self._detect_success_indicators_in_content(content)
            
            # Find forms
            forms = browser.eles('tag:form')
            
            # Calculate success probability
            success_probability = self._calculate_success_probability(
                barriers, success_indicators, len(forms), load_time
            )
            
            return {
                'accessible': success_probability > 0.6,
                'status_code': 200,
                'method_used': 'browser_automation',
                'final_url': current_url,
                'barriers': barriers,
                'success_indicators': success_indicators,
                'success_probability': success_probability,
                'load_time': load_time,
                'forms_found': len(forms),
                'recommendations': self._generate_enhanced_recommendations(
                    barriers, success_indicators, len(forms)
                )
            }
            
        except Exception as e:
            return {
                'accessible': False,
                'error': str(e),
                'barriers': ['connection_failed'],
                'success_probability': 0.0,
                'recommendations': [f"Connection failed: {str(e)}"]
            }
    
    async def _handle_cloudflare_challenges(self, browser: ChromiumPage, max_wait: int = 30):
        """Handle Cloudflare challenges automatically"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                current_url = browser.url
                page_content = browser.html.lower()
                
                # Check for Cloudflare challenge indicators
                cf_indicators = [
                    'checking your browser',
                    'cloudflare',
                    'just a moment',
                    'please wait',
                    'ray id',
                    'challenge-running',
                    'cf-browser-verification'
                ]
                
                is_cf_challenge = any(indicator in page_content for indicator in cf_indicators)
                
                if not is_cf_challenge:
                    logger.info("No Cloudflare challenge detected or challenge completed")
                    break
                
                logger.info("Cloudflare challenge detected, waiting...")
                
                # Look for and click verification checkboxes if present
                checkbox_selectors = [
                    'input[type="checkbox"]',
                    '.cf-turnstile',
                    '#challenge-form input',
                    '.challenge-form input[type="checkbox"]'
                ]
                
                for selector in checkbox_selectors:
                    try:
                        checkbox = browser.ele(selector, timeout=2)
                        if checkbox:
                            logger.info(f"Found checkbox with selector: {selector}")
                            checkbox.click()
                            await asyncio.sleep(2)
                            break
                    except ElementNotFoundError:
                        continue
                
                # Wait for page changes
                await asyncio.sleep(3)
                
                # Check if URL changed (common after challenge completion)
                new_url = browser.url
                if new_url != current_url:
                    logger.info("URL changed, challenge likely completed")
                    break
                    
            except Exception as e:
                logger.warning(f"Error handling Cloudflare challenge: {e}")
                await asyncio.sleep(2)
        
        # Final wait for any remaining loading
        await asyncio.sleep(2)
    
    def _detect_barriers_in_content(self, content: str, status_code: int) -> List[str]:
        """Detect various barriers in page content"""
        barriers = []
        content_lower = content.lower()
        
        # Status code barriers
        if status_code == 403:
            barriers.append("access_forbidden")
        elif status_code == 404:
            barriers.append("page_not_found")
        elif status_code >= 400:
            barriers.append(f"http_error_{status_code}")
        
        # Content-based barriers
        if any(word in content_lower for word in ['captcha', 'recaptcha', 'hcaptcha', 'turnstile']):
            barriers.append("captcha_detected")
        
        if 'cloudflare' in content_lower and 'checking your browser' in content_lower:
            barriers.append("cloudflare_challenge")
        
        if any(word in content_lower for word in ['login', 'signin', 'sign in', 'authenticate']):
            if any(word in content_lower for word in ['password', 'username', 'email']):
                barriers.append("login_required")
        
        if 'blocked' in content_lower or 'access denied' in content_lower:
            barriers.append("access_blocked")
        
        if any(word in content_lower for word in ['javascript', 'js']) and 'required' in content_lower:
            barriers.append("javascript_required")
        
        return barriers
    
    def _detect_success_indicators_in_content(self, content: str) -> List[str]:
        """Detect positive indicators in page content"""
        indicators = []
        content_lower = content.lower()
        
        if '<form' in content_lower:
            indicators.append("forms_present")
        
        if any(word in content_lower for word in ['submit', 'apply', 'contact', 'register']):
            indicators.append("interactive_elements")
        
        if 'input' in content_lower and 'type=' in content_lower:
            indicators.append("input_fields_present")
        
        if len(content) > 10000:  # Substantial content
            indicators.append("substantial_content")
        
        return indicators
    
    def _calculate_success_probability(self, barriers: List[str], success_indicators: List[str], 
                                     form_count: int, load_time: float) -> float:
        """Calculate probability of successful form interaction"""
        probability = 0.8  # Base probability
        
        # Reduce for barriers
        barrier_penalties = {
            'captcha_detected': -0.3,
            'cloudflare_challenge': -0.1,  # Less penalty since we handle it
            'login_required': -0.4,
            'access_blocked': -0.6,
            'access_forbidden': -0.7,
            'http_error_404': -0.8,
            'javascript_required': -0.1
        }
        
        for barrier in barriers:
            penalty = barrier_penalties.get(barrier, -0.2)
            probability += penalty
        
        # Increase for success indicators
        for indicator in success_indicators:
            probability += 0.1
        
        # Form bonus
        if form_count > 0:
            probability += 0.2
        else:
            probability -= 0.3
        
        # Load time penalty (too fast might indicate blocking)
        if load_time < 1:
            probability -= 0.1
        elif load_time > 30:
            probability -= 0.2
        
        return max(0.0, min(1.0, probability))
    
    def _generate_enhanced_recommendations(self, barriers: List[str], 
                                         success_indicators: List[str], 
                                         form_count: int) -> List[str]:
        """Generate enhanced recommendations"""
        recommendations = []
        
        if form_count == 0:
            recommendations.append("No forms found - verify URL or wait for dynamic content")
        
        if 'captcha_detected' in barriers:
            recommendations.append("CAPTCHA detected - may require manual intervention or CAPTCHA solver")
        
        if 'cloudflare_challenge' in barriers:
            recommendations.append("Cloudflare challenge detected - using enhanced browser automation")
        
        if 'login_required' in barriers:
            recommendations.append("Login required - provide authentication credentials")
        
        if 'access_blocked' in barriers:
            recommendations.append("Access blocked - consider using different IP or proxy")
        
        if len(success_indicators) > 2 and form_count > 0:
            recommendations.append("Page looks excellent for automation - proceed with confidence")
        
        return recommendations
    
    async def analyze_page_comprehensive_enhanced(self, url: str) -> Dict[str, Any]:
        """Enhanced comprehensive page analysis with smart mode switching"""
        try:
            # Start with accessibility test
            access_result = await self.test_url_accessibility_enhanced(url)
            
            if not access_result.get('accessible', False):
                return {
                    'success': False,
                    'error': f"Page not accessible: {access_result.get('error', 'Unknown error')}",
                    'accessibility': access_result
                }
            
            # Use the method that worked for accessibility test
            method_used = access_result.get('method_used', 'browser_automation')
            
            if method_used == 'http_session':
                # Try session first for speed
                try:
                    return await self._analyze_with_session(url, access_result)
                except:
                    # Fall back to browser
                    return await self._analyze_with_browser(url, access_result)
            else:
                # Use browser directly
                return await self._analyze_with_browser(url, access_result)
                
        except Exception as e:
            logger.error(f"Error analyzing page {url}: {str(e)}")
            return {
                'success': False,
                'error': f"Analysis failed: {str(e)}"
            }
    
    async def _analyze_with_session(self, url: str, access_result: Dict) -> Dict[str, Any]:
        """Analyze page using HTTP session for speed"""
        session = self._get_session_page()
        session.get(url)
        
        # Extract basic information
        title_ele = session.ele('tag:title')
        title = title_ele.text if title_ele else 'No title'
        
        forms = session.eles('tag:form')
        
        return {
            'success': True,
            'method_used': 'http_session',
            'title': title,
            'url': session.url,
            'forms_count': len(forms),
            'forms_analysis': [self._analyze_form_basic(form, i) for i, form in enumerate(forms)],
            'accessibility': access_result,
            'page_type': self._determine_page_type(session.html, len(forms)),
            'recommendations': ['Fast HTTP session analysis completed successfully']
        }
    
    async def _analyze_with_browser(self, url: str, access_result: Dict) -> Dict[str, Any]:
        """Analyze page using browser automation for complex cases"""
        browser = await self._get_browser_page()
        
        if browser.url != url:
            browser.get(url)
            await self._handle_cloudflare_challenges(browser)
        
        # Extract comprehensive information
        title_ele = browser.ele('tag:title', timeout=5)
        title = title_ele.text if title_ele else 'No title'
        
        forms = browser.eles('tag:form')
        
        # Check for dynamic content
        await asyncio.sleep(2)  # Wait for any dynamic loading
        forms_after_wait = browser.eles('tag:form')
        
        if len(forms_after_wait) > len(forms):
            forms = forms_after_wait
            logger.info(f"Found {len(forms_after_wait) - len(forms)} additional forms after waiting")
        
        return {
            'success': True,
            'method_used': 'browser_automation',
            'title': title,
            'url': browser.url,
            'forms_count': len(forms),
            'forms_analysis': [self._analyze_form_comprehensive(form, i) for i, form in enumerate(forms)],
            'accessibility': access_result,
            'page_type': self._determine_page_type(browser.html, len(forms)),
            'dynamic_content_detected': len(forms_after_wait) > len(forms),
            'recommendations': ['Comprehensive browser analysis completed successfully']
        }
    
    def _analyze_form_basic(self, form, index: int) -> Dict[str, Any]:
        """Basic form analysis for session mode"""
        action = form.attr('action') or ''
        method = form.attr('method') or 'GET'
        
        fields = form.eles('tag:input, tag:textarea, tag:select')
        
        return {
            'index': index,
            'action': action,
            'method': method.upper(),
            'field_count': len(fields),
            'has_file_upload': bool(form.ele('css:input[type="file"]')),
            'has_required_fields': bool(form.ele('css:input[required], textarea[required], select[required]'))
        }
    
    def _analyze_form_comprehensive(self, form, index: int) -> Dict[str, Any]:
        """Comprehensive form analysis for browser mode"""
        basic_info = self._analyze_form_basic(form, index)
        
        # Additional browser-specific analysis
        submit_buttons = form.eles('tag:input[type="submit"], tag:button[type="submit"], tag:button')
        
        # Check for JavaScript form handling
        form_attrs = form.attrs
        has_js_handling = any(attr.startswith('on') for attr in form_attrs.keys())
        
        basic_info.update({
            'submit_buttons': len(submit_buttons),
            'has_javascript_handling': has_js_handling,
            'form_id': form.attr('id') or '',
            'form_class': form.attr('class') or ''
        })
        
        return basic_info
    
    def _determine_page_type(self, html_content: str, form_count: int) -> str:
        """Determine the type of page based on content"""
        content_lower = html_content.lower()
        
        if form_count == 0:
            return 'no_forms'
        
        # Job application patterns
        if any(word in content_lower for word in ['job', 'career', 'position', 'application', 'apply now', 'resume']):
            return 'job_application'
        
        # Contact form patterns
        if any(word in content_lower for word in ['contact', 'message', 'inquiry', 'get in touch']):
            return 'contact_form'
        
        # Registration patterns
        if any(word in content_lower for word in ['register', 'sign up', 'create account', 'join']):
            return 'registration'
        
        # Login patterns
        if any(word in content_lower for word in ['login', 'sign in', 'authenticate']):
            return 'login'
        
        return 'general_form'
    
    async def extract_form_fields_enhanced(self, url: str, form_index: int = 0) -> Dict[str, Any]:
        """Enhanced form field extraction with intelligent handling"""
        try:
            # First determine the best method to use
            access_result = await self.test_url_accessibility_enhanced(url)
            method = access_result.get('method_used', 'browser_automation')
            
            if method == 'http_session' and access_result.get('success_probability', 0) > 0.8:
                # Try session first for speed
                try:
                    return await self._extract_fields_with_session(url, form_index)
                except Exception as e:
                    logger.info(f"Session extraction failed, falling back to browser: {e}")
            
            # Use browser for complex cases
            return await self._extract_fields_with_browser(url, form_index)
            
        except Exception as e:
            logger.error(f"Error extracting form fields from {url}: {str(e)}")
            return {
                'success': False,
                'error': f"Field extraction failed: {str(e)}"
            }
    
    async def _extract_fields_with_session(self, url: str, form_index: int) -> Dict[str, Any]:
        """Extract form fields using HTTP session"""
        session = self._get_session_page()
        session.get(url)
        
        forms = session.eles('tag:form')
        if not forms:
            return {'success': False, 'error': 'No forms found on page'}
        
        if form_index >= len(forms):
            return {'success': False, 'error': f'Form index {form_index} not found. Page has {len(forms)} forms.'}
        
        form = forms[form_index]
        
        return {
            'success': True,
            'method_used': 'http_session',
            'fields': self._extract_field_details_from_element(form, session),
            'form_action': self._get_form_action(form, url),
            'form_method': (form.attr('method') or 'GET').upper(),
            'form_enctype': form.attr('enctype') or 'application/x-www-form-urlencoded',
            'form_index': form_index
        }
    
    async def _extract_fields_with_browser(self, url: str, form_index: int) -> Dict[str, Any]:
        """Extract form fields using browser automation"""
        browser = await self._get_browser_page()
        browser.get(url)
        await self._handle_cloudflare_challenges(browser)
        
        # Wait for dynamic content
        await asyncio.sleep(2)
        
        forms = browser.eles('tag:form')
        if not forms:
            return {'success': False, 'error': 'No forms found on page'}
        
        if form_index >= len(forms):
            return {'success': False, 'error': f'Form index {form_index} not found. Page has {len(forms)} forms.'}
        
        form = forms[form_index]
        
        return {
            'success': True,
            'method_used': 'browser_automation',
            'fields': self._extract_field_details_from_element(form, browser),
            'form_action': self._get_form_action(form, browser.url),
            'form_method': (form.attr('method') or 'GET').upper(),
            'form_enctype': form.attr('enctype') or 'application/x-www-form-urlencoded',
            'form_index': form_index
        }
    
    def _extract_field_details_from_element(self, form, page) -> List[Dict[str, Any]]:
        """Extract detailed field information from form element"""
        fields = []
        field_elements = form.eles('tag:input, tag:textarea, tag:select')
        
        for element in field_elements:
            field_type = element.attr('type') or 'text'
            
            # Skip non-input fields
            if field_type.lower() in ['hidden', 'submit', 'button', 'image', 'reset']:
                continue
            
            field_data = {
                'tag': element.tag,
                'type': field_type,
                'name': element.attr('name') or '',
                'id': element.attr('id') or '',
                'identifier': element.attr('id') or element.attr('name') or '',
                'value': element.attr('value') or '',
                'placeholder': element.attr('placeholder') or '',
                'required': element.attr('required') is not None,
                'disabled': element.attr('disabled') is not None,
                'readonly': element.attr('readonly') is not None
            }
            
            # Find label
            field_data['label'] = self._find_field_label(element, page)
            
            # Add field-specific attributes
            if element.tag == 'select':
                options = []
                option_elements = element.eles('tag:option')
                for option in option_elements:
                    options.append({
                        'value': option.attr('value') or option.text,
                        'text': option.text,
                        'selected': option.attr('selected') is not None
                    })
                field_data['options'] = options
            
            # Validation rules
            field_data['validation_rules'] = self._extract_validation_rules(element)
            
            fields.append(field_data)
        
        return fields
    
    def _find_field_label(self, element, page) -> str:
        """Find label for a form field"""
        # Try label tag first
        field_id = element.attr('id')
        if field_id:
            label = page.ele(f'css:label[for="{field_id}"]', timeout=1)
            if label:
                return label.text.strip()
        
        # Try aria-label
        aria_label = element.attr('aria-label')
        if aria_label:
            return aria_label.strip()
        
        # Try placeholder
        placeholder = element.attr('placeholder')
        if placeholder:
            return placeholder.strip()
        
        # Try name attribute
        name = element.attr('name')
        if name:
            return name.replace('_', ' ').replace('-', ' ').title()
        
        return 'Unnamed field'
    
    def _extract_validation_rules(self, element) -> List[str]:
        """Extract validation rules from element attributes"""
        rules = []
        
        if element.attr('required'):
            rules.append('required')
        
        field_type = element.attr('type', '').lower()
        if field_type == 'email':
            rules.append('email_format')
        elif field_type == 'url':
            rules.append('url_format')
        elif field_type == 'tel':
            rules.append('phone_format')
        
        pattern = element.attr('pattern')
        if pattern:
            rules.append(f'pattern: {pattern}')
        
        min_length = element.attr('minlength')
        if min_length:
            rules.append(f'min_length: {min_length}')
        
        max_length = element.attr('maxlength')
        if max_length:
            rules.append(f'max_length: {max_length}')
        
        return rules
    
    def _get_form_action(self, form, current_url: str) -> str:
        """Get form action URL"""
        action = form.attr('action') or ''
        if not action:
            return current_url
        elif action.startswith('http'):
            return action
        else:
            return urljoin(current_url, action)
    
    async def close(self):
        """Clean up resources"""
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

# Example usage and testing
async def test_enhanced_scraper():
    """Test the enhanced form scraper"""
    scraper = EnhancedFormScraper(use_stealth=True, headless=False)  # headless=False for testing
    
    try:
        # Test with a challenging site
        test_url = "https://nopecha.com/demo/cloudflare"
        
        print("Testing URL accessibility...")
        access_result = await scraper.test_url_accessibility_enhanced(test_url)
        print(f"Access result: {access_result}")
        
        if access_result.get('accessible'):
            print("\nAnalyzing page...")
            analysis_result = await scraper.analyze_page_comprehensive_enhanced(test_url)
            print(f"Analysis result: {analysis_result}")
            
            if analysis_result.get('success') and analysis_result.get('forms_count', 0) > 0:
                print("\nExtracting form fields...")
                fields_result = await scraper.extract_form_fields_enhanced(test_url)
                print(f"Fields result: {fields_result}")
    
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_enhanced_scraper())
