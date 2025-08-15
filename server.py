#!/usr/bin/env python3
"""
Fixed Form Automation MCP Server with DrissionPage
Resolves connection issues and import problems
"""

import asyncio
import logging
import os
import time
import sys
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

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

# Fix import paths - use relative imports within the same directory
try:
    from bulletproof_scraper import BulletproofFormScraper
    from bulletproof_submitter import BulletproofFormSubmitter
except ImportError:
    print("❌ Could not import scraper/submitter modules")
    print("Make sure the files are named correctly:")
    print("  - bulletproof_scraper.py")
    print("  - bulletproof_submitter.py")
    sys.exit(1)

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration with better defaults
PORT = int(os.getenv("PORT", 8000))  # Changed from 8083 to avoid conflicts
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
USE_STEALTH = os.getenv("USE_STEALTH", "true").lower() == "true"
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

if DEBUG_MODE:
    logging.getLogger().setLevel(logging.DEBUG)

# Initialize MCP server with better error handling
try:
    if MCP_VERSION == "new":
        mcp = FastMCP(
            "Form Automation Server",
            host="0.0.0.0", 
            port=PORT
        )
    else:
        mcp = FastMCP(
            name="Form Automation Server",
            host="0.0.0.0", 
            port=PORT
        )
    logger.info(f"✅ FastMCP initialized (version: {MCP_VERSION})")
except Exception as e:
    logger.error(f"❌ Failed to initialize FastMCP: {e}")
    sys.exit(1)

# Global components with better lifecycle management
scraper = None
submitter = None
_shutdown_requested = False

async def get_scraper() -> BulletproofFormScraper:
    """Get or create scraper instance with error handling"""
    global scraper
    try:
        if scraper is None or _shutdown_requested:
            if scraper:
                await safe_cleanup_scraper()
            scraper = BulletproofFormScraper(use_stealth=USE_STEALTH, headless=HEADLESS)
            logger.info("✅ Scraper initialized")
        return scraper
    except Exception as e:
        logger.error(f"❌ Failed to create scraper: {e}")
        raise

async def get_submitter() -> BulletproofFormSubmitter:
    """Get or create submitter instance with error handling"""
    global submitter
    try:
        if submitter is None or _shutdown_requested:
            if submitter:
                await safe_cleanup_submitter()
            submitter = BulletproofFormSubmitter(use_stealth=USE_STEALTH, headless=HEADLESS)
            logger.info("✅ Submitter initialized")
        return submitter
    except Exception as e:
        logger.error(f"❌ Failed to create submitter: {e}")
        raise

async def safe_cleanup_scraper():
    """Safely cleanup scraper"""
    global scraper
    if scraper:
        try:
            await scraper.close()
            logger.info("✅ Scraper cleaned up")
        except Exception as e:
            logger.warning(f"⚠️ Scraper cleanup error: {e}")
        finally:
            scraper = None

async def safe_cleanup_submitter():
    """Safely cleanup submitter"""
    global submitter
    if submitter:
        try:
            await submitter.close()
            logger.info("✅ Submitter cleaned up")
        except Exception as e:
            logger.warning(f"⚠️ Submitter cleanup error: {e}")
        finally:
            submitter = None

# Pydantic models
class FormSubmissionData(BaseModel):
    url: str = Field(description="The URL of the page with the form")
    form_index: int = Field(default=0, description="The 0-based index of the form")
    field_data: Dict[str, str] = Field(description="Dictionary of field names to values")

class FormAnalysisData(BaseModel):
    url: str = Field(description="The URL of the page to analyze")

class FormFieldsData(BaseModel):
    url: str = Field(description="The URL of the page with the form")
    form_index: int = Field(default=0, description="The 0-based index of the form")

class URLTestData(BaseModel):
    url: str = Field(description="The URL to test for accessibility")

# Remove the decorator - FastMCP handles errors internally
# Just use direct tool definitions

# Fixed MCP Tools (no decorator)
@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Health check endpoint with comprehensive status"""
    try:
        # Test basic functionality
        test_results = {}
        
        # Test scraper creation
        try:
            test_scraper = BulletproofFormScraper(use_stealth=False, headless=True)
            await test_scraper.close()
            test_results["scraper"] = "✅ OK"
        except Exception as e:
            test_results["scraper"] = f"❌ Error: {str(e)[:50]}"
        
        # Test submitter creation
        try:
            test_submitter = BulletproofFormSubmitter(use_stealth=False, headless=True)
            await test_submitter.close()
            test_results["submitter"] = "✅ OK"
        except Exception as e:
            test_results["submitter"] = f"❌ Error: {str(e)[:50]}"
        
        return {
            "status": "healthy",
            "server": "form-automation-mcp",
            "version": "2.1.0-fixed",
            "timestamp": time.time(),
            "port": PORT,
            "config": {
                "headless": HEADLESS,
                "stealth": USE_STEALTH,
                "debug": DEBUG_MODE
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
async def analyze_page(data: FormAnalysisData) -> Dict[str, Any]:
    """Enhanced page analysis"""
    try:
        scraper_instance = await get_scraper()
        result = await scraper_instance.analyze_page_comprehensive_enhanced(data.url)
        return result
    except Exception as e:
        logger.error(f"❌ Error in analyze_page: {str(e)}")
        return {
            "success": False,
            "error": f"Page analysis failed: {str(e)[:200]}",
            "url": data.url
        }

@mcp.tool()
async def scrape_form_fields(data: FormFieldsData) -> Dict[str, Any]:
    """Enhanced form field extraction"""
    try:
        scraper_instance = await get_scraper()
        result = await scraper_instance.extract_form_fields_enhanced(data.url, data.form_index)
        return result
    except Exception as e:
        logger.error(f"❌ Error in scrape_form_fields: {str(e)}")
        return {
            "success": False,
            "error": f"Field extraction failed: {str(e)[:200]}",
            "url": data.url
        }

@mcp.tool()
async def validate_form_data(data: FormSubmissionData) -> Dict[str, Any]:
    """Enhanced form data validation"""
    try:
        submitter_instance = await get_submitter()
        result = await submitter_instance.validate_submission_enhanced(
            data.url, data.field_data, data.form_index
        )
        return result
    except Exception as e:
        logger.error(f"❌ Error in validate_form_data: {str(e)}")
        return {
            "valid": False,
            "error": f"Validation failed: {str(e)[:200]}",
            "url": data.url
        }

@mcp.tool()
async def submit_form(data: FormSubmissionData) -> Dict[str, Any]:
    """Enhanced form submission"""
    try:
        submitter_instance = await get_submitter()
        result = await submitter_instance.submit_form_enhanced(
            data.url, data.field_data, data.form_index
        )
        return result
    except Exception as e:
        logger.error(f"❌ Error in submit_form: {str(e)}")
        return {
            "success": False,
            "error": f"Form submission failed: {str(e)[:200]}",
            "url": data.url
        }

@mcp.tool()
async def test_form_access(data: URLTestData) -> Dict[str, Any]:
    """Enhanced URL accessibility testing"""
    try:
        scraper_instance = await get_scraper()
        result = await scraper_instance.test_url_accessibility_enhanced(data.url)
        return result
    except Exception as e:
        logger.error(f"❌ Error in test_form_access: {str(e)}")
        return {
            "accessible": False,
            "error": f"Access test failed: {str(e)[:200]}",
            "url": data.url
        }

@mcp.tool()
async def get_submission_history() -> Dict[str, Any]:
    """Get recent form submission history"""
    try:
        submitter_instance = await get_submitter()
        history = getattr(submitter_instance, 'submission_history', [])
        
        recent_history = history[-10:] if len(history) > 10 else history
        
        if history:
            success_count = sum(1 for record in history if record.get('success'))
            success_rate = success_count / len(history)
        else:
            success_rate = 0.0
        
        return {
            "total_submissions": len(history),
            "recent_submissions": recent_history,
            "success_rate": success_rate
        }
    except Exception as e:
        logger.error(f"❌ Error in get_submission_history: {str(e)}")
        return {
            "error": f"Failed to get submission history: {str(e)[:200]}"
        }

@mcp.tool()
async def configure_stealth_mode(enable_stealth: bool = True, headless: bool = True) -> Dict[str, Any]:
    """Configure stealth and anti-detection settings"""
    try:
        global USE_STEALTH, HEADLESS
        
        # Update settings
        USE_STEALTH = enable_stealth
        HEADLESS = headless
        
        # Clean up existing instances
        await safe_cleanup_scraper()
        await safe_cleanup_submitter()
        
        return {
            "success": True,
            "stealth_mode": USE_STEALTH,
            "headless_mode": HEADLESS,
            "message": "Configuration updated. Components will be reinitialized."
        }
    except Exception as e:
        logger.error(f"❌ Error in configure_stealth_mode: {str(e)}")
        return {
            "success": False,
            "error": f"Configuration failed: {str(e)[:200]}"
        }

# Enhanced cleanup and startup
async def cleanup():
    """Enhanced cleanup with proper resource management"""
    global _shutdown_requested
    _shutdown_requested = True
    
    try:
        await safe_cleanup_scraper()
        await safe_cleanup_submitter()
        logger.info("🔒 Cleanup completed successfully")
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")

async def startup():
    """Initialize components on startup"""
    try:
        logger.info("🚀 Starting Form Automation Server...")
        
        # Test basic functionality
        logger.info("🧪 Testing components...")
        
        # Quick test without keeping instances
        test_scraper = BulletproofFormScraper(use_stealth=False, headless=True)
        await test_scraper.close()
        logger.info("✅ Scraper test passed")
        
        test_submitter = BulletproofFormSubmitter(use_stealth=False, headless=True)
        await test_submitter.close()
        logger.info("✅ Submitter test passed")
        
        logger.info("🎯 All components ready")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise

# Main execution
if __name__ == "__main__":
    print("🤖 Starting Fixed Form Automation MCP Server...")
    print(f"⚙️  Configuration:")
    print(f"  - Port: {PORT}")
    print(f"  - Stealth Mode: {USE_STEALTH}")
    print(f"  - Headless Mode: {HEADLESS}")
    print(f"  - Debug Mode: {DEBUG_MODE}")
    print(f"  - MCP Version: {MCP_VERSION}")
    print()
    
    try:
        # Run startup
        asyncio.run(startup())
        
        # Start server
        print(f"🌐 Server starting on http://0.0.0.0:{PORT}")
        if MCP_VERSION == "new":
            mcp.run(transport="sse")
        else:
            mcp.run()
            
    except KeyboardInterrupt:
        print("\n🛑 Server shutting down...")
        asyncio.run(cleanup())
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        asyncio.run(cleanup())
        sys.exit(1)
