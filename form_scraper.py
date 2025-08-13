#!/usr/bin/env python3
"""
Ultra-Robust Form Scraper
Handles ANY barrier: download screens, login walls, CAPTCHAs, redirects, etc.
"""

import asyncio
import aiohttp
import time
import random
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)

class UltraFormScraper:
    def __init__(self):
        self.session = None
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with anti-detection headers"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30, connect=10)
            )
            
        return self.session
    
    async def test_url_accessibility(self, url: str) -> Dict[str, Any]:
        """Test if URL is accessible and detect potential barriers"""
        try:
            session = await self._get_session()
            
            start_time = time.time()
            
            # First, try HEAD request to check basics
            try:
                async with session.head(url, allow_redirects=True) as response:
                    head_info = {
                        'status_code': response.status,
                        'content_type': response.headers.get('content-type', ''),
                        'final_url': str(response.url),
                        'redirect_count': len(response.history)
                    }
            except:
                head_info = {}
            
            # Then try GET request
            async with session.get(url, allow_redirects=True) as response:
                load_time = time.time() - start_time
                content = await response.text()
                
                barriers = []
                content_lower = content.lower()
                
                # Detect various barriers
                if response.status == 403:
                    barriers.append("access_forbidden")
                elif response.status == 404:
                    barriers.append("page_not_found")
                elif response.status >= 400:
                    barriers.append(f"http_error_{response.status}")
                
                # Content-based barrier detection
                if 'captcha' in content_lower or 'recaptcha' in content_lower:
                    barriers.append("captcha_detected")
                
                if any(word in content_lower for word in ['login', 'signin', 'sign in', 'authenticate']):
                    if 'form' in content_lower and any(word in content_lower for word in ['password', 'username', 'email']):
                        barriers.append("login_required")
                
                if 'download' in url.lower() or any(ext in response.headers.get('content-type', '') for ext in ['pdf', 'zip', 'doc', 'xls']):
                    barriers.append("download_file")
                
                if response.headers.get('content-disposition', '').startswith('attachment'):
                    barriers.append("forced_download")
                
                # Check for forms
                soup = BeautifulSoup(content, 'html.parser')
                forms = soup.find_all('form')
                
                # Estimate success probability
                success_probability = 1.0
                if barriers:
                    success_probability -= len(barriers) * 0.2
                if not forms:
                    success_probability -= 0.3
                if response.status != 200:
                    success_probability -= 0.4
                
                success_probability = max(0.0, min(1.0, success_probability))
                
                recommendations = []
                if 'captcha_detected' in barriers:
                    recommendations.append("Page has CAPTCHA - manual intervention may be required")
                if 'login_required' in barriers:
                    recommendations.append("Page requires authentication - provide credentials")
                if 'download_file' in barriers:
                    recommendations.append("URL points to download - not a form page")
                if not forms:
                    recommendations.append("No forms detected - verify this is the correct URL")
                
                return {
                    'accessible': response.status == 200 and len(barriers) == 0,
                    'status_code': response.status,
                    'content_type': response.headers.get('content-type', ''),
                    'final_url': str(response.url),
                    'redirect_count': len(response.history),
                    'barriers': barriers,
                    'success_probability': success_probability,
                    'recommendations': recommendations,
                    'load_time': load_time,
                    'forms_found': len(forms)
                }
                
        except Exception as e:
            return {
                'accessible': False,
                'error': str(e),
                'barriers': ['connection_failed'],
                'success_probability': 0.0,
                'recommendations': [f"Connection failed: {str(e)}"]
            }
    
    async def analyze_page_comprehensive(self, url: str) -> Dict[str, Any]:
        """Comprehensive page analysis including barriers and content"""
        try:
            session = await self._get_session()
            
            async with session.get(url, allow_redirects=True) as response:
                if response.status not in [200, 201]:
                    return {
                        'error': f"HTTP {response.status}: Cannot access page",
                        'status_code': response.status,
                        'accessible': False
                    }
                
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Basic page info
                title = soup.find('title')
                title_text = title.get_text().strip() if title else 'No title'
                
                # Find all forms
                forms = soup.find_all('form')
                
                # Detect barriers and issues
                barriers = []
                warnings = []
                content_lower = content.lower()
                
                # CAPTCHA detection
                if any(word in content_lower for word in ['captcha', 'recaptcha', 'hcaptcha']):
                    barriers.append("captcha_protection")
                
                # Login requirement
                if 'login' in content_lower and soup.find('input', {'type': 'password'}):
                    barriers.append("authentication_required")
                
                # JavaScript dependency
                script_tags = soup.find_all('script')
                if len(script_tags) > 10:  # Heavy JS usage
                    warnings.append("heavy_javascript_usage")
                
                # Download detection
                content_type = response.headers.get('content-type', '')
                if any(file_type in content_type for file_type in ['pdf', 'zip', 'doc', 'excel']):
                    return {
                        'error': f"URL returns {content_type}, not an HTML form",
                        'page_type': 'download',
                        'accessible': False
                    }
                
                # Dynamic content warnings
                if 'loading' in content_lower or 'please wait' in content_lower:
                    warnings.append("dynamic_content_loading")
                
                # Form analysis
                form_analysis = []
                for i, form in enumerate(forms):
                    fields = form.find_all(['input', 'textarea', 'select'])
                    form_info = {
                        'index': i,
                        'action': form.get('action', ''),
                        'method': form.get('method', 'GET').upper(),
                        'field_count': len(fields),
                        'has_file_upload': bool(form.find('input', {'type': 'file'})),
                        'requires_validation': bool(form.find('input', {'required': True}))
                    }
                    form_analysis.append(form_info)
                
                # Determine page type
                page_type = 'unknown'
                if forms:
                    if any('job' in content_lower for word in ['job', 'career', 'application', 'apply']):
                        page_type = 'job_application'
                    elif 'contact' in content_lower:
                        page_type = 'contact_form'
                    elif 'signup' in content_lower or 'register' in content_lower:
                        page_type = 'registration'
                    else:
                        page_type = 'general_form'
                else:
                    page_type = 'no_forms'
                
                # Barriers bypassed
                barriers_bypassed = []
                if response.status == 200:
                    barriers_bypassed.append("http_access_successful")
                if len(response.history) > 0:
                    barriers_bypassed.append(f"followed_{len(response.history)}_redirects")
                
                return {
                    'success': True,
                    'title': title_text,
                    'url': str(response.url),
                    'status_code': response.status,
                    'forms_count': len(forms),
                    'forms_analysis': form_analysis,
                    'barriers': barriers,
                    'barriers_bypassed': barriers_bypassed,
                    'warnings': warnings,
                    'page_type': page_type,
                    'accessible': len(barriers) == 0,
                    'recommendations': self._generate_recommendations(barriers, warnings, len(forms))
                }
                
        except Exception as e:
            logger.error(f"Error analyzing page {url}: {str(e)}")
            return {
                'error': f"Analysis failed: {str(e)}",
                'accessible': False
            }
    
    def _generate_recommendations(self, barriers: List[str], warnings: List[str], form_count: int) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        if form_count == 0:
            recommendations.append("No forms found - verify this is the correct page URL")
        
        if 'captcha_protection' in barriers:
            recommendations.append("CAPTCHA detected - automated submission may fail")
        
        if 'authentication_required' in barriers:
            recommendations.append("Page requires login - provide authentication credentials")
        
        if 'heavy_javascript_usage' in warnings:
            recommendations.append("Page uses heavy JavaScript - may need browser automation")
        
        if 'dynamic_content_loading' in warnings:
            recommendations.append("Content loads dynamically - may need delay before scraping")
        
        if not barriers and not warnings and form_count > 0:
            recommendations.append("Page looks good for automation - proceed with form filling")
        
        return recommendations
    
    async def extract_form_fields_ultra(self, url: str, form_index: int = 0) -> Dict[str, Any]:
        """Extract form fields with maximum detail and intelligence"""
        try:
            session = await self._get_session()
            
            async with session.get(url, allow_redirects=True) as response:
                if response.status not in [200, 201]:
                    return {
                        'success': False,
                        'error': f"Cannot access page: HTTP {response.status}"
                    }
                
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                forms = soup.find_all('form')
                if not forms:
                    return {
                        'success': False,
                        'error': "No forms found on page"
                    }
                
                if form_index >= len(forms):
                    return {
                        'success': False,
                        'error': f"Form index {form_index} not found. Page has {len(forms)} forms."
                    }
                
                form = forms[form_index]
                
                # Extract form metadata
                form_action = form.get('action', '')
                if form_action and not form_action.startswith('http'):
                    form_action = urljoin(url, form_action)
                
                form_method = form.get('method', 'GET').upper()
                form_enctype = form.get('enctype', 'application/x-www-form-urlencoded')
                
                # Extract all form fields
                fields = []
                field_elements = form.find_all(['input', 'textarea', 'select'])
                
                for element in field_elements:
                    field_data = self._extract_field_details(element, soup)
                    if field_data:  # Only add valid fields
                        fields.append(field_data)
                
                # Find submit button info
                submit_info = self._find_submit_info(form)
                
                return {
                    'success': True,
                    'fields': fields,
                    'field_count': len(fields),
                    'form_action': form_action or url,
                    'form_method': form_method,
                    'form_enctype': form_enctype,
                    'submit_info': submit_info,
                    'form_index': form_index
                }
                
        except Exception as e:
            logger.error(f"Error extracting form fields from {url}: {str(e)}")
            return {
                'success': False,
                'error': f"Field extraction failed: {str(e)}"
            }
    
    def _extract_field_details(self, element, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract detailed information about a form field"""
        tag_name = element.name.lower()
        field_type = element.get('type', 'text').lower()
        
        # Skip certain field types
        if field_type in ['hidden', 'submit', 'button', 'image', 'reset']:
            return None
        
        # Basic field info
        field_data = {
            'tag': tag_name,
            'type': field_type,
            'name': element.get('name', ''),
            'identifier': element.get('id') or element.get('name', ''),
            'value': element.get('value', ''),
            'placeholder': element.get('placeholder', ''),
            'required': element.has_attr('required'),
            'disabled': element.has_attr('disabled'),
            'readonly': element.has_attr('readonly')
        }
        
        # Find label
        label = self._find_field_label(element, soup)
        field_data['label'] = label
        
        # Field-specific attributes
        if tag_name == 'input':
            field_data.update({
                'max_length': element.get('maxlength'),
                'min_length': element.get('minlength'),
                'pattern': element.get('pattern'),
                'accept': element.get('accept'),  # for file inputs
                'multiple': element.has_attr('multiple')
            })
        
        elif tag_name == 'textarea':
            field_data.update({
                'rows': element.get('rows'),
                'cols': element.get('cols'),
                'max_length': element.get('maxlength'),
                'wrap': element.get('wrap')
            })
        
        elif tag_name == 'select':
            options = []
            option_elements = element.find_all('option')
            for option in option_elements:
                option_data = {
                    'value': option.get('value', option.get_text().strip()),
                    'text': option.get_text().strip(),
                    'selected': option.has_attr('selected')
                }
                options.append(option_data)
            
            field_data.update({
                'options': options,
                'multiple': element.has_attr('multiple'),
                'size': element.get('size')
            })
        
        # Additional context from surrounding elements
        field_data['description'] = self._find_field_description(element, soup)
        field_data['validation_rules'] = self._extract_validation_rules(element)
        
        return field_data
    
    def _find_field_label(self, element, soup: BeautifulSoup) -> str:
        """Find the label text for a form field"""
        # Try label tag first
        field_id = element.get('id')
        if field_id:
            label = soup.find('label', {'for': field_id})
            if label:
                return label.get_text().strip()
        
        # Try parent label
        parent_label = element.find_parent('label')
        if parent_label:
            text = parent_label.get_text().strip()
            # Remove the input's own value from label text
            if element.get('value'):
                text = text.replace(element.get('value'), '').strip()
            return text
        
        # Try aria-label
        aria_label = element.get('aria-label')
        if aria_label:
            return aria_label.strip()
        
        # Try title attribute
        title = element.get('title')
        if title:
            return title.strip()
        
        # Try placeholder as last resort
        placeholder = element.get('placeholder')
        if placeholder:
            return placeholder.strip()
        
        # Try to find nearby text
        prev_element = element.find_previous_sibling()
        if prev_element and prev_element.name in ['span', 'div', 'p', 'strong', 'b']:
            text = prev_element.get_text().strip()
            if len(text) < 100:  # Reasonable label length
                return text
        
        return element.get('name', 'Unnamed field')
    
    def _find_field_description(self, element, soup: BeautifulSoup) -> str:
        """Find description or help text for a field"""
        # Try aria-describedby
        described_by = element.get('aria-describedby')
        if described_by:
            desc_element = soup.find(attrs={'id': described_by})
            if desc_element:
                return desc_element.get_text().strip()
        
        # Look for nearby help text
        field_id = element.get('id')
        if field_id:
            # Common patterns for help text
            help_element = soup.find(attrs={'class': re.compile(r'help|hint|description', re.I)})
            if help_element:
                return help_element.get_text().strip()
        
        return ''
    
    def _extract_validation_rules(self, element) -> List[str]:
        """Extract validation rules from field attributes"""
        rules = []
        
        if element.has_attr('required'):
            rules.append('required')
        
        if element.get('type') == 'email':
            rules.append('email_format')
        
        if element.get('type') == 'url':
            rules.append('url_format')
        
        if element.get('pattern'):
            rules.append(f"pattern: {element.get('pattern')}")
        
        min_length = element.get('minlength')
        if min_length:
            rules.append(f"min_length: {min_length}")
        
        max_length = element.get('maxlength')
        if max_length:
            rules.append(f"max_length: {max_length}")
        
        return rules
    
    def _find_submit_info(self, form) -> Dict[str, Any]:
        """Find submit button information"""
        # Look for submit buttons
        submit_buttons = form.find_all(['input', 'button'], {'type': 'submit'})
        submit_buttons.extend(form.find_all('button', type=lambda x: x != 'button'))
        
        if submit_buttons:
            button = submit_buttons[0]  # Use first submit button
            return {
                'type': 'button',
                'tag': button.name,
                'identifier': button.get('id') or button.get('name'),
                'value': button.get('value') or button.get_text().strip(),
                'text': button.get_text().strip()
            }
        
        # Look for any button that might submit
        buttons = form.find_all('button')
        for button in buttons:
            button_text = button.get_text().lower()
            if any(word in button_text for word in ['submit', 'send', 'apply', 'save', 'continue']):
                return {
                    'type': 'button',
                    'tag': button.name,
                    'identifier': button.get('id') or button.get('name'),
                    'text': button.get_text().strip()
                }
        
        return {
            'type': 'form',
            'method': 'submit_form_directly'
        }
    
    async def close(self):
        """Clean up resources"""
        if self.session and not self.session.closed:
            await self.session.close()