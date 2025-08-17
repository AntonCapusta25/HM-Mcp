#!/usr/bin/env python3
"""
Email Automation MCP Server
Professional email sending with SMTP support
"""

import asyncio
import logging
import os
import time
import sys
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, EmailStr

# Enhanced error handling for imports
try:
    from mcp.server.fastmcp import FastMCP
    MCP_VERSION = "new"
except ImportError:
    try:
        from fastmcp import FastMCP
        MCP_VERSION = "old"
    except ImportError as e:
        print(f"❌ FastMCP not available: {e}")
        print("Install with: pip install fastmcp")
        sys.exit(1)

# Import email components
try:
    from bulletproof_emailer import BulletproofEmailSender
except ImportError:
    print("❌ Could not import email sender module")
    print("Make sure the file is named correctly:")
    print("  - bulletproof_emailer.py")
    sys.exit(1)

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration with better defaults
PORT = int(os.getenv("PORT", 8001))  # Different port from form server
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

# Email configuration from environment
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
USE_TLS = os.getenv("USE_TLS", "true").lower() == "true"

if DEBUG_MODE:
    logging.getLogger().setLevel(logging.DEBUG)

# Initialize MCP server with better error handling
try:
    if MCP_VERSION == "new":
        mcp = FastMCP(
            "Email Automation Server",
            host="0.0.0.0", 
            port=PORT
        )
    else:
        mcp = FastMCP(
            name="Email Automation Server",
            host="0.0.0.0", 
            port=PORT
        )
    logger.info(f"✅ FastMCP initialized (version: {MCP_VERSION})")
except Exception as e:
    logger.error(f"❌ Failed to initialize FastMCP: {e}")
    sys.exit(1)

# Global components with better lifecycle management
email_sender = None
_shutdown_requested = False

async def get_email_sender() -> BulletproofEmailSender:
    """Get or create email sender instance with error handling"""
    global email_sender
    try:
        if email_sender is None or _shutdown_requested:
            if email_sender:
                await safe_cleanup_email_sender()
            
            email_sender = BulletproofEmailSender(
                smtp_server=SMTP_SERVER,
                smtp_port=SMTP_PORT,
                username=EMAIL_USER,
                password=EMAIL_PASSWORD,
                use_tls=USE_TLS
            )
            logger.info("✅ Email sender initialized")
        return email_sender
    except Exception as e:
        logger.error(f"❌ Failed to create email sender: {e}")
        raise

async def safe_cleanup_email_sender():
    """Safely cleanup email sender"""
    global email_sender
    if email_sender:
        try:
            await email_sender.close()
            logger.info("✅ Email sender cleaned up")
        except Exception as e:
            logger.warning(f"⚠️ Email sender cleanup error: {e}")
        finally:
            email_sender = None

# Pydantic models for email operations
class EmailData(BaseModel):
    to: List[EmailStr] = Field(description="List of recipient email addresses")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content")
    cc: Optional[List[EmailStr]] = Field(default=None, description="CC recipients")
    bcc: Optional[List[EmailStr]] = Field(default=None, description="BCC recipients")
    is_html: bool = Field(default=False, description="Whether body is HTML")
    attachments: Optional[List[str]] = Field(default=None, description="List of file paths to attach")

class EmailConfigData(BaseModel):
    smtp_server: str = Field(description="SMTP server address")
    smtp_port: int = Field(description="SMTP server port")
    username: str = Field(description="Email username")
    password: str = Field(description="Email password")
    use_tls: bool = Field(default=True, description="Use TLS encryption")

class EmailValidationData(BaseModel):
    to: List[EmailStr] = Field(description="Recipient email addresses to validate")
    subject: Optional[str] = Field(default=None, description="Subject to validate")
    body: Optional[str] = Field(default=None, description="Body to validate")

# MCP Tools
@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Health check endpoint with comprehensive status"""
    try:
        # Test basic functionality
        test_results = {}
        
        # Test email sender creation
        try:
            test_sender = BulletproofEmailSender(
                smtp_server=SMTP_SERVER,
                smtp_port=SMTP_PORT,
                username=EMAIL_USER,
                password=EMAIL_PASSWORD,
                use_tls=USE_TLS
            )
            # Test connection without sending
            connection_test = await test_sender.test_connection()
            await test_sender.close()
            test_results["email_sender"] = "✅ OK" if connection_test else "⚠️ Connection issue"
        except Exception as e:
            test_results["email_sender"] = f"❌ Error: {str(e)[:50]}"
        
        return {
            "status": "healthy",
            "server": "email-automation-mcp",
            "version": "1.0.0",
            "timestamp": time.time(),
            "port": PORT,
            "config": {
                "smtp_server": SMTP_SERVER,
                "smtp_port": SMTP_PORT,
                "use_tls": USE_TLS,
                "debug": DEBUG_MODE,
                "email_configured": bool(EMAIL_USER and EMAIL_PASSWORD)
            },
            "components": test_results,
            "mcp_version": MCP_VERSION
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@mcp.tool()
async def send_email(data: EmailData) -> Dict[str, Any]:
    """Send email with comprehensive error handling"""
    try:
        sender_instance = await get_email_sender()
        result = await sender_instance.send_email_enhanced(
            to=data.to,
            subject=data.subject,
            body=data.body,
            cc=data.cc,
            bcc=data.bcc,
            is_html=data.is_html,
            attachments=data.attachments
        )
        return result
    except Exception as e:
        logger.error(f"❌ Error in send_email: {str(e)}")
        return {
            "success": False,
            "error": f"Email sending failed: {str(e)[:200]}",
            "recipients": data.to
        }

@mcp.tool()
async def validate_email_data(data: EmailValidationData) -> Dict[str, Any]:
    """Validate email data before sending"""
    try:
        sender_instance = await get_email_sender()
        result = await sender_instance.validate_email_data(
            to=data.to,
            subject=data.subject,
            body=data.body
        )
        return result
    except Exception as e:
        logger.error(f"❌ Error in validate_email_data: {str(e)}")
        return {
            "valid": False,
            "error": f"Email validation failed: {str(e)[:200]}",
            "recipients": data.to
        }

@mcp.tool()
async def test_email_connection() -> Dict[str, Any]:
    """Test SMTP connection"""
    try:
        sender_instance = await get_email_sender()
        result = await sender_instance.test_connection_detailed()
        return result
    except Exception as e:
        logger.error(f"❌ Error in test_email_connection: {str(e)}")
        return {
            "connected": False,
            "error": f"Connection test failed: {str(e)[:200]}"
        }

@mcp.tool()
async def get_email_history() -> Dict[str, Any]:
    """Get recent email sending history"""
    try:
        sender_instance = await get_email_sender()
        history = getattr(sender_instance, 'email_history', [])
        
        recent_history = history[-20:] if len(history) > 20 else history
        
        if history:
            success_count = sum(1 for record in history if record.get('success'))
            success_rate = success_count / len(history)
        else:
            success_rate = 0.0
        
        return {
            "total_emails_sent": len(history),
            "recent_emails": recent_history,
            "success_rate": success_rate
        }
    except Exception as e:
        logger.error(f"❌ Error in get_email_history: {str(e)}")
        return {
            "error": f"Failed to get email history: {str(e)[:200]}"
        }

@mcp.tool()
async def configure_email_settings(data: EmailConfigData) -> Dict[str, Any]:
    """Configure email SMTP settings"""
    try:
        global SMTP_SERVER, SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD, USE_TLS
        
        # Update settings
        SMTP_SERVER = data.smtp_server
        SMTP_PORT = data.smtp_port
        EMAIL_USER = data.username
        EMAIL_PASSWORD = data.password
        USE_TLS = data.use_tls
        
        # Clean up existing instance to use new settings
        await safe_cleanup_email_sender()
        
        # Test new configuration
        test_sender = BulletproofEmailSender(
            smtp_server=SMTP_SERVER,
            smtp_port=SMTP_PORT,
            username=EMAIL_USER,
            password=EMAIL_PASSWORD,
            use_tls=USE_TLS
        )
        
        connection_test = await test_sender.test_connection()
        await test_sender.close()
        
        return {
            "success": True,
            "smtp_server": SMTP_SERVER,
            "smtp_port": SMTP_PORT,
            "username": EMAIL_USER,
            "use_tls": USE_TLS,
            "connection_test": connection_test,
            "message": "Email configuration updated successfully"
        }
    except Exception as e:
        logger.error(f"❌ Error in configure_email_settings: {str(e)}")
        return {
            "success": False,
            "error": f"Configuration failed: {str(e)[:200]}"
        }

@mcp.tool()
async def send_simple_email(to: str, subject: str, body: str, is_html: bool = False) -> Dict[str, Any]:
    """Send a simple email with basic parameters"""
    try:
        email_data = EmailData(
            to=[to],
            subject=subject,
            body=body,
            is_html=is_html
        )
        return await send_email(email_data)
    except Exception as e:
        logger.error(f"❌ Error in send_simple_email: {str(e)}")
        return {
            "success": False,
            "error": f"Simple email sending failed: {str(e)[:200]}",
            "recipient": to
        }

# Enhanced cleanup and startup
async def cleanup():
    """Enhanced cleanup with proper resource management"""
    global _shutdown_requested
    _shutdown_requested = True
    
    try:
        await safe_cleanup_email_sender()
        logger.info("🔒 Email server cleanup completed successfully")
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")

async def startup():
    """Initialize components on startup"""
    try:
        logger.info("🚀 Starting Email Automation Server...")
        
        # Test basic functionality
        logger.info("🧪 Testing email components...")
        
        if not EMAIL_USER or not EMAIL_PASSWORD:
            logger.warning("⚠️ Email credentials not configured - some features may not work")
        else:
            # Quick test without keeping instances
            test_sender = BulletproofEmailSender(
                smtp_server=SMTP_SERVER,
                smtp_port=SMTP_PORT,
                username=EMAIL_USER,
                password=EMAIL_PASSWORD,
                use_tls=USE_TLS
            )
            
            try:
                connection_test = await test_sender.test_connection()
                if connection_test:
                    logger.info("✅ Email connection test passed")
                else:
                    logger.warning("⚠️ Email connection test failed")
            except Exception as e:
                logger.warning(f"⚠️ Email connection test error: {e}")
            finally:
                await test_sender.close()
        
        logger.info("🎯 Email server components ready")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise

# Main execution
if __name__ == "__main__":
    print("📧 Starting Email Automation MCP Server...")
    print(f"⚙️  Configuration:")
    print(f"  - Port: {PORT}")
    print(f"  - SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"  - Use TLS: {USE_TLS}")
    print(f"  - Debug Mode: {DEBUG_MODE}")
    print(f"  - Email User: {EMAIL_USER[:5]}***" if EMAIL_USER else "  - Email User: Not configured")
    print(f"  - MCP Version: {MCP_VERSION}")
    print()
    
    try:
        # Run startup
        asyncio.run(startup())
        
        # Start server
        print(f"🌐 Email server starting on http://0.0.0.0:{PORT}")
        if MCP_VERSION == "new":
            mcp.run(transport="sse")
        else:
            mcp.run()
            
    except KeyboardInterrupt:
        print("\n🛑 Email server shutting down...")
        asyncio.run(cleanup())
    except Exception as e:
        logger.error(f"❌ Email server error: {e}")
        asyncio.run(cleanup())
        sys.exit(1)