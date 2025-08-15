#!/usr/bin/env python3
"""
Ultra-Enhanced Form Automation MCP Server with DrissionPage
Superior Cloudflare bypass and anti-detection capabilities
"""

import asyncio
import logging
import os
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

# Import FastMCP with compatibility for newer versions
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from fastmcp import FastMCP

# Import enhanced components
from enhanced_form_scraper import EnhancedFormScraper
from enhanced_form_submitter import EnhancedFormSubmitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration from environment
PORT = int(os.getenv("PORT", 8083))
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
USE_STEALTH = os.getenv("USE_STEALTH", "true").lower() == "true"

# Initialize the MCP server with updated configuration
try:
    # Try newer FastMCP initialization
    mcp = FastMCP(
        "Enhanced Form Automation Server with DrissionPage",
        host="0.0.0.0", 
        port=PORT
    )
except TypeError:
    # Fall back to older initialization style
    mcp = FastMCP(
        name="Enhanced Form Automation Server with DrissionPage",
        host="0.0.0.0", 
        port=PORT
    )

# Global components - initialized lazily
scraper = None
submitter = None

async def get_scraper() -> EnhancedFormScraper:
    """Get or create scraper instance"""
    global scraper
    if scraper is None:
        scraper = EnhancedFormScraper(use_stealth=USE_STEALTH, headless=HEADLESS)
    return scraper

async def get_submitter() -> EnhancedFormSubmitter:
    """Get or create submitter instance"""
    global submitter
    if submitter is None:
        submitter = EnhancedFormSubmitter(use_stealth=USE_STEALTH, headless=HEADLESS)
    return submitter

# Pydantic models for validation
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

# Enhanced MCP Tools
@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Health check endpoint with DrissionPage status for Railway deployment monitoring"""
    try:
        # Test scraper
        scraper_status = "healthy"
        try:
            test_scraper = await get_scraper()
            # Quick test without actually navigating
            scraper_status = "healthy"
        except Exception as e:
            scraper_status = f"error: {str(e)}"
        
        return {
            "status": "healthy",
            "server": "enhanced-form-automation-mcp-drissionpage",
            "version": "2.0.0",
            "timestamp": time.time(),
            "components": {
                "scraper": scraper_status,
                "drissionpage": "available",
                "stealth_mode": USE_STEALTH,
                "headless_mode": HEADLESS
            },
            "features": [
                "cloudflare_bypass",
                "anti_detection",
                "intelligent_form_handling",
                "dual_mode_operation",
                "enhanced_validation"
            ],
            "tools": [
                "analyze_page",
                "scrape_form_fields", 
                "validate_form_data",
                "submit_form",
                "test_form_access",
                "health_check"
            ]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@mcp.tool()
async def analyze_page(data: FormAnalysisData) -> Dict[str, Any]:
    """Enhanced page analysis with superior Cloudflare bypass and anti-detection. Automatically handles CAPTCHAs, login walls, and dynamic content."""
    try:
        scraper_instance = await get_scraper()
        result = await scraper_instance.analyze_page_comprehensive_enhanced(data.url)
        
        # Add metadata about the analysis
        result['enhanced_features'] = {
            'cloudflare_bypass': True,
            'anti_detection': USE_STEALTH,
            'dynamic_content_handling': True,
            'intelligent_method_selection': True
        }
        
        return result
    except Exception as e:
        logger.error(f"Error in enhanced page analysis {data.url}: {str(e)}")
        return {
            "success": False,
            "error": f"Enhanced analysis failed: {str(e)}",
            "url": data.url
        }

@mcp.tool()
async def scrape_form_fields(data: FormFieldsData) -> Dict[str, Any]:
    """Enhanced form field extraction with intelligent field detection and superior barrier handling. Automatically adapts to use the best method (HTTP or browser) based on page complexity."""
    try:
        scraper_instance = await get_scraper()
        result = await scraper_instance.extract_form_fields_enhanced(data.url, data.form_index)
        
        # Add enhanced metadata
        if result.get('success'):
            result['enhanced_features'] = {
                'intelligent_field_detection': True,
                'fuzzy_label_matching': True,
                'validation_rule_extraction': True,
                'method_used': result.get('method_used', 'unknown')
            }
        
        return result
    except Exception as e:
        logger.error(f"Error in enhanced form field extraction {data.url}: {str(e)}")
        return {
            "success": False,
            "error": f"Enhanced field extraction failed: {str(e)}",
            "url": data.url
        }

@mcp.tool()
async def validate_form_data(data: FormSubmissionData) -> Dict[str, Any]:
    """Enhanced form data validation with intelligent field matching and comprehensive error reporting. Provides suggestions for field name corrections and detailed validation insights."""
    try:
        submitter_instance = await get_submitter()
        result = await submitter_instance.validate_submission_enhanced(
            data.url, data.field_data, data.form_index
        )
        
        # Add enhanced validation metadata
        result['enhanced_features'] = {
            'fuzzy_field_matching': True,
            'intelligent_validation': True,
            'field_suggestions': len(result.get('suggestions', [])) > 0,
            'comprehensive_error_reporting': True
        }
        
        return result
    except Exception as e:
        logger.error(f"Error in enhanced form validation {data.url}: {str(e)}")
        return {
            "valid": False,
            "error": f"Enhanced validation failed: {str(e)}",
            "url": data.url
        }

@mcp.tool()
async def submit_form(data: FormSubmissionData) -> Dict[str, Any]:
    """Enhanced form submission with superior anti-detection, intelligent retry logic, and adaptive method selection. Automatically handles Cloudflare challenges, CAPTCHAs, and complex form interactions."""
    try:
        submitter_instance = await get_submitter()
        result = await submitter_instance.submit_form_enhanced(
            data.url, data.field_data, data.form_index
        )
        
        # Add enhanced submission metadata
        result['enhanced_features'] = {
            'cloudflare_bypass': True,
            'anti_detection': USE_STEALTH,
            'intelligent_retry_logic': True,
            'adaptive_method_selection': True,
            'human_like_interaction': True
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in enhanced form submission {data.url}: {str(e)}")
        return {
            "success": False,
            "error": f"Enhanced submission failed: {str(e)}",
            "url": data.url
        }

@mcp.tool()
async def test_form_access(data: URLTestData) -> Dict[str, Any]:
    """Enhanced URL accessibility testing with comprehensive barrier detection and Cloudflare challenge handling. Provides detailed success probability assessment and actionable recommendations."""
    try:
        scraper_instance = await get_scraper()
        result = await scraper_instance.test_url_accessibility_enhanced(data.url)
        
        # Add enhanced testing metadata
        result['enhanced_features'] = {
            'cloudflare_detection': True,
            'barrier_analysis': True,
            'success_probability_calculation': True,
            'intelligent_method_selection': True,
            'comprehensive_recommendations': True
        }
        
        return result
    except Exception as e:
        logger.error(f"Error in enhanced URL testing {data.url}: {str(e)}")
        return {
            "accessible": False,
            "error": f"Enhanced access test failed: {str(e)}",
            "url": data.url
        }

# Additional debugging and monitoring tools
@mcp.tool()
async def get_submission_history() -> Dict[str, Any]:
    """Get recent form submission history for debugging and monitoring purposes"""
    try:
        submitter_instance = await get_submitter()
        history = getattr(submitter_instance, 'submission_history', [])
        
        # Get recent submissions (last 10)
        recent_history = history[-10:] if len(history) > 10 else history
        
        # Calculate success rate
        if history:
            success_count = sum(1 for record in history if record.get('success'))
            success_rate = success_count / len(history)
        else:
            success_rate = 0.0
        
        return {
            "total_submissions": len(history),
            "recent_submissions": recent_history,
            "success_rate": success_rate,
            "enhanced_monitoring": True
        }
    except Exception as e:
        return {
            "error": f"Failed to get submission history: {str(e)}"
        }

@mcp.tool()
async def configure_stealth_mode(enable_stealth: bool = True, headless: bool = True) -> Dict[str, Any]:
    """Configure stealth and anti-detection settings for the automation components"""
    try:
        global USE_STEALTH, HEADLESS, scraper, submitter
        
        # Update global settings
        USE_STEALTH = enable_stealth
        HEADLESS = headless
        
        # Reset components to apply new settings
        if scraper:
            await scraper.close()
            scraper = None
        
        if submitter:
            await submitter.close()
            submitter = None
        
        return {
            "success": True,
            "stealth_mode": USE_STEALTH,
            "headless_mode": HEADLESS,
            "message": "Stealth configuration updated. Components will be reinitialized with new settings."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to configure stealth mode: {str(e)}"
        }

# Cleanup function
async def cleanup():
    """Enhanced cleanup with proper resource management"""
    try:
        global scraper, submitter
        
        if scraper:
            await scraper.close()
            scraper = None
        
        if submitter:
            await submitter.close()
            submitter = None
        
        logger.info("🔒 Enhanced cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during enhanced cleanup: {e}")

# Startup function
async def startup():
    """Initialize components on startup"""
    try:
        logger.info("🚀 Initializing Enhanced Form Automation Server...")
        
        # Pre-initialize components to test them
        await get_scraper()
        logger.info("✅ Enhanced scraper initialized")
        
        await get_submitter()
        logger.info("✅ Enhanced submitter initialized")
        
        logger.info("🎯 All enhanced components ready")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")

if __name__ == "__main__":
    print("🤖 Starting Enhanced Form Automation MCP Server with DrissionPage...")
    print("🛡️  Enhanced Features:")
    print("  - Superior Cloudflare bypass capabilities")
    print("  - Advanced anti-detection mechanisms")
    print("  - Intelligent method selection (HTTP/Browser)")
    print("  - Human-like interaction patterns")
    print("  - Comprehensive barrier handling")
    print("  - Fuzzy field matching and validation")
    print()
    print("📍 Available enhanced tools:")
    print("  - analyze_page: Enhanced page analysis with Cloudflare bypass")
    print("  - scrape_form_fields: Intelligent form field extraction") 
    print("  - validate_form_data: Smart validation with field suggestions")
    print("  - submit_form: Anti-detection form submission")
    print("  - test_form_access: Comprehensive accessibility testing")
    print("  - get_submission_history: Monitoring and debugging")
    print("  - configure_stealth_mode: Runtime configuration")
    print("  - health_check: Enhanced server health monitoring")
    print()
    print(f"⚙️  Configuration:")
    print(f"  - Stealth Mode: {USE_STEALTH}")
    print(f"  - Headless Mode: {HEADLESS}")
    print(f"  - Port: {PORT}")
    print(f"  - FastMCP Version: {getattr(mcp, '__version__', 'unknown')}")
    print()
    print(f"🌐 Server endpoints:")
    print(f"  - SSE mode: http://0.0.0.0:{PORT}/sse")
    print(f"  - HTTP mode: http://0.0.0.0:{PORT}/mcp")
    if hasattr(mcp, '_fastapi_app'):
        print(f"  - FastAPI docs: http://0.0.0.0:{PORT}/docs")
    print()
    
    # Detect deployment environment
    if os.getenv("RAILWAY_ENVIRONMENT"):
        print("🚂 Running on Railway with enhanced capabilities!")
        print(f"   Public URL will be available after deployment")
    elif os.getenv("HEROKU_APP_NAME"):
        print("🌐 Running on Heroku with enhanced capabilities!")
    else:
        print("💻 Running locally with enhanced capabilities!")
    
    try:
        # Run startup initialization
        asyncio.run(startup())
        
        # Start the server with compatibility check
        try:
            # Try newer FastMCP run method
            mcp.run(transport="sse")
        except TypeError:
            # Fall back to older method if needed
            mcp.run()
            
    except KeyboardInterrupt:
        print("\n🛑 Enhanced server shutting down...")
        asyncio.run(cleanup())
    except Exception as e:
        logger.error(f"Enhanced server error: {e}")
        asyncio.run(cleanup())
