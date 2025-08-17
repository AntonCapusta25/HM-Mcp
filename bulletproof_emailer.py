#!/usr/bin/env python3
"""
Bulletproof Email Sender
Professional email sending with SMTP support and error handling
"""

import asyncio
import smtplib
import time
import logging
import re
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class BulletproofEmailSender:
    def __init__(self, smtp_server: str, smtp_port: int, username: str, 
                 password: str, use_tls: bool = True, timeout: int = 30):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.timeout = timeout
        self.email_history = []
        self._max_history = 100
        
        # Connection state
        self._connection = None
        self._connected = False
        
    async def test_connection(self) -> bool:
        """Test SMTP connection without keeping it open"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.timeout)
            
            if self.use_tls:
                server.starttls()
                
            server.login(self.username, self.password)
            server.quit()
            
            logger.info("✅ SMTP connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ SMTP connection test failed: {e}")
            return False
    
    async def test_connection_detailed(self) -> Dict[str, Any]:
        """Detailed connection test with diagnostics"""
        result = {
            "connected": False,
            "server": self.smtp_server,
            "port": self.smtp_port,
            "use_tls": self.use_tls,
            "username": self.username,
            "error": None,
            "response_time": 0
        }
        
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Testing connection to {self.smtp_server}:{self.smtp_port}")
            
            # Test basic connection
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.timeout)
            logger.debug("✅ Basic SMTP connection established")
            
            # Test TLS if enabled
            if self.use_tls:
                server.starttls()
                logger.debug("✅ TLS encryption enabled")
            
            # Test authentication
            server.login(self.username, self.password)
            logger.debug("✅ Authentication successful")
            
            # Clean disconnect
            server.quit()
            
            result["connected"] = True
            result["response_time"] = time.time() - start_time
            
            logger.info(f"✅ Connection test successful in {result['response_time']:.2f}s")
            
        except smtplib.SMTPAuthenticationError as e:
            result["error"] = f"Authentication failed: {str(e)}"
            logger.error(f"❌ Authentication error: {e}")
        except smtplib.SMTPConnectError as e:
            result["error"] = f"Connection failed: {str(e)}"
            logger.error(f"❌ Connection error: {e}")
        except smtplib.SMTPException as e:
            result["error"] = f"SMTP error: {str(e)}"
            logger.error(f"❌ SMTP error: {e}")
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Unexpected error: {e}")
        finally:
            result["response_time"] = time.time() - start_time
        
        return result
    
    async def validate_email_data(self, to: List[str], subject: Optional[str] = None, 
                                body: Optional[str] = None) -> Dict[str, Any]:
        """Validate email data before sending"""
        result = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "recipients_checked": len(to),
            "valid_recipients": [],
            "invalid_recipients": []
        }
        
        try:
            # Validate recipients
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            
            for email in to:
                if isinstance(email, str) and email_pattern.match(email.strip()):
                    result["valid_recipients"].append(email.strip())
                else:
                    result["invalid_recipients"].append(email)
                    result["issues"].append(f"Invalid email format: {email}")
            
            if not result["valid_recipients"]:
                result["valid"] = False
                result["issues"].append("No valid recipients found")
            
            # Validate subject
            if subject is not None:
                if not subject.strip():
                    result["warnings"].append("Subject line is empty")
                elif len(subject) > 200:
                    result["warnings"].append("Subject line is very long (>200 chars)")
            
            # Validate body
            if body is not None:
                if not body.strip():
                    result["warnings"].append("Email body is empty")
                elif len(body) > 100000:  # 100KB limit
                    result["warnings"].append("Email body is very large (>100KB)")
            
            # Check credentials
            if not self.username or not self.password:
                result["valid"] = False
                result["issues"].append("Email credentials not configured")
            
            if result["issues"]:
                result["valid"] = False
            
            logger.info(f"📋 Email validation: Valid={result['valid']}, Issues={len(result['issues'])}")
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Validation error: {str(e)[:100]}")
            logger.error(f"❌ Email validation failed: {e}")
        
        return result
    
    async def send_email_enhanced(self, to: List[str], subject: str, body: str,
                                cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None,
                                is_html: bool = False, attachments: Optional[List[str]] = None,
                                max_retries: int = 3) -> Dict[str, Any]:
        """Enhanced email sending with comprehensive error handling"""
        send_start = time.time()
        
        try:
            logger.info(f"📧 Starting email send to {len(to)} recipients")
            
            # Base response
            result = {
                'success': False,
                'message': 'Email sending in progress...',
                'recipients': to,
                'attempts': 0,
                'error': None,
                'send_time': 0,
                'validation': None
            }
            
            # Input validation
            if not to or not subject or not body:
                result.update({
                    'success': False,
                    'error': 'Missing required fields: to, subject, or body',
                    'message': 'Email sending failed due to missing data'
                })
                return result
            
            # Pre-send validation
            try:
                logger.debug("🔍 Running pre-send validation...")
                all_recipients = to + (cc or []) + (bcc or [])
                validation = await self.validate_email_data(all_recipients, subject, body)
                result['validation'] = validation
                
                if not validation.get('valid', False):
                    result['warnings'] = validation.get('issues', [])
                    logger.warning(f"⚠️ Validation issues: {len(validation.get('issues', []))}")
                else:
                    logger.info("✅ Pre-send validation passed")
                    
            except Exception as e:
                logger.warning(f"⚠️ Validation failed during send: {e}")
                result['validation'] = {'valid': False, 'error': str(e)[:100]}
            
            # Attempt sending with retries
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    result['attempts'] = attempt + 1
                    logger.info(f"📤 Send attempt {attempt + 1} of {max_retries}")
                    
                    # Compose and send email
                    send_result = await self._safe_send_email(
                        to=to, subject=subject, body=body,
                        cc=cc, bcc=bcc, is_html=is_html, attachments=attachments
                    )
                    
                    # Record the attempt
                    self._record_send_attempt(to, subject, send_result, attempt + 1)
                    
                    if send_result.get('success', False):
                        # Success!
                        result.update(send_result)
                        result['send_time'] = time.time() - send_start
                        logger.info(f"✅ Email sent successfully on attempt {attempt + 1}")
                        return result
                    else:
                        # Failed, prepare for retry
                        last_error = send_result.get('error', 'Unknown sending error')
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
                'message': f'Email sending failed after {max_retries} attempts',
                'error': last_error,
                'send_time': time.time() - send_start
            })
            
            logger.error(f"❌ Email sending completely failed after {max_retries} attempts")
            return result
            
        except Exception as e:
            # Ultimate fallback
            logger.error(f"❌ Complete email sending failure: {e}")
            return {
                'success': False,
                'error': f"Email system error: {str(e)[:200]}",
                'message': 'Email sending system encountered an error',
                'recipients': to,
                'attempts': 1,
                'send_time': time.time() - send_start
            }
    
    async def _safe_send_email(self, to: List[str], subject: str, body: str,
                             cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None,
                             is_html: bool = False, attachments: Optional[List[str]] = None) -> Dict[str, Any]:
        """Safely send email with proper error handling"""
        try:
            logger.debug("📧 Composing email message...")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = formataddr((self.username, self.username))
            msg['To'] = ', '.join(to)
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            attachment_results = []
            if attachments:
                for file_path in attachments:
                    attach_result = await self._safe_add_attachment(msg, file_path)
                    attachment_results.append(attach_result)
            
            # Prepare recipients
            all_recipients = to + (cc or []) + (bcc or [])
            
            # Send email
            logger.debug(f"📤 Connecting to SMTP server {self.smtp_server}:{self.smtp_port}")
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.timeout)
            
            if self.use_tls:
                server.starttls()
                logger.debug("🔒 TLS encryption enabled")
            
            server.login(self.username, self.password)
            logger.debug("✅ SMTP authentication successful")
            
            # Send the email
            text = msg.as_string()
            server.sendmail(self.username, all_recipients, text)
            server.quit()
            
            logger.info(f"📧 Email sent successfully to {len(all_recipients)} recipients")
            
            return {
                'success': True,
                'message': f'Email sent successfully to {len(to)} recipients',
                'recipients_count': len(all_recipients),
                'attachments_added': len([r for r in attachment_results if r.get('success')]),
                'attachment_results': attachment_results
            }
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
            
        except smtplib.SMTPRecipientsRefused as e:
            error_msg = f"Recipients refused: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
            
        except smtplib.SMTPSenderRefused as e:
            error_msg = f"Sender refused: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
            
        except smtplib.SMTPDataError as e:
            error_msg = f"SMTP data error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
            
        except Exception as e:
            error_msg = f"Email sending failed: {str(e)[:100]}"
            logger.error(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
    
    async def _safe_add_attachment(self, msg: MIMEMultipart, file_path: str) -> Dict[str, Any]:
        """Safely add attachment to email"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {
                    'success': False,
                    'file': str(file_path),
                    'error': 'File not found'
                }
            
            if file_path.stat().st_size > 25 * 1024 * 1024:  # 25MB limit
                return {
                    'success': False,
                    'file': str(file_path),
                    'error': 'File too large (>25MB)'
                }
            
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {file_path.name}'
            )
            
            msg.attach(part)
            
            logger.debug(f"📎 Attachment added: {file_path.name}")
            
            return {
                'success': True,
                'file': str(file_path),
                'filename': file_path.name,
                'size': file_path.stat().st_size
            }
            
        except Exception as e:
            error_msg = f"Failed to add attachment {file_path}: {str(e)[:100]}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'file': str(file_path),
                'error': error_msg
            }
    
    def _record_send_attempt(self, recipients: List[str], subject: str, 
                           result: Dict[str, Any], attempt: int):
        """Record email sending attempt"""
        try:
            record = {
                'timestamp': time.time(),
                'recipients': recipients[:5],  # Limit stored recipients
                'recipient_count': len(recipients),
                'subject': subject[:100] if subject else '',  # Limit subject length
                'attempt': attempt,
                'success': result.get('success', False),
                'error': result.get('error', '')[:200] if result.get('error') else '',  # Limit error length
            }
            
            self.email_history.append(record)
            
            # Keep only recent records
            if len(self.email_history) > self._max_history:
                self.email_history = self.email_history[-self._max_history:]
                
            logger.debug(f"📝 Recorded email attempt: {record['success']}")
            
        except Exception as e:
            logger.debug(f"⚠️ Recording attempt failed: {e}")
    
    async def send_simple_text_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Send a simple text email to single recipient"""
        return await self.send_email_enhanced(
            to=[to],
            subject=subject,
            body=body,
            is_html=False
        )
    
    async def send_html_email(self, to: List[str], subject: str, html_body: str,
                            cc: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send HTML email"""
        return await self.send_email_enhanced(
            to=to,
            subject=subject,
            body=html_body,
            cc=cc,
            is_html=True
        )
    
    async def send_email_with_attachments(self, to: List[str], subject: str, body: str,
                                        attachments: List[str], is_html: bool = False) -> Dict[str, Any]:
        """Send email with attachments"""
        return await self.send_email_enhanced(
            to=to,
            subject=subject,
            body=body,
            attachments=attachments,
            is_html=is_html
        )
    
    def get_email_statistics(self) -> Dict[str, Any]:
        """Get email sending statistics"""
        try:
            if not self.email_history:
                return {
                    'total_emails': 0,
                    'success_rate': 0.0,
                    'recent_activity': []
                }
            
            total = len(self.email_history)
            successful = sum(1 for record in self.email_history if record.get('success'))
            success_rate = successful / total if total > 0 else 0.0
            
            # Recent activity (last 24 hours)
            cutoff_time = time.time() - 86400  # 24 hours ago
            recent_activity = [
                record for record in self.email_history 
                if record.get('timestamp', 0) > cutoff_time
            ]
            
            return {
                'total_emails': total,
                'successful_emails': successful,
                'failed_emails': total - successful,
                'success_rate': success_rate,
                'recent_24h': len(recent_activity),
                'recent_activity': recent_activity[-10:]  # Last 10 recent
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return {'error': str(e)}
    
    async def close(self):
        """Clean up resources"""
        try:
            if self._connection:
                try:
                    self._connection.quit()
                except:
                    pass
                self._connection = None
                self._connected = False
            
            logger.debug("✅ Email sender cleaned up")
            
        except Exception as e:
            logger.debug(f"⚠️ Email sender cleanup error: {e}")

# Alias for compatibility
EnhancedEmailSender = BulletproofEmailSender