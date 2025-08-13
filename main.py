#!/usr/bin/env python3
"""
Ultra-Robust Form Automation MCP Server - Simple Railway Version
No FastAPI complications, just pure MCP functionality
"""

import asyncio
import logging
import os
import time
from typing import Dict, Any
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

# Import your existing classes
from form_scraper import UltraFormScraper
from form_submitter import UltraFormSubmitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get port from environment variable (Railway sets this)
PORT = int(os.getenv("PORT", 8083))

# Initialize the MCP server
mcp = FastMCP(
    name="Ultra Form Automation Server",
    host="0.0.0.0", 
    port=PORT
)

# Initialize components globally
scraper = UltraFormScraper()
submitter = UltraFormSubmitter()

# Pydantic models for type validation
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

# Health check tool for Railway monitoring
@mcp.tool(
    name="health_check",
    description="Health check endpoint for Railway deployment monitoring"
)
async def health_check() -> Dict[str, Any]:
    """Health check for Railway"""
    return {
        "status": "healthy",
        "server": "ultra-form-automation-mcp",
        "version": "1.0.0",
        "timestamp": time.time(),
        "uptime": "running",
        "tools": [
            "analyze_page",
            "scrape_form_fields", 
            "validate_form_data",
            "submit_form",
            "test_form_access",
            "health_check"
        ]
    }

# MCP Tool definitions using decorators
@mcp.tool(
    name="analyze_page",
    description="Analyzes a webpage to find forms and detect barriers like CAPTCHAs, login requirements, etc."
)
async def analyze_page(data: FormAnalysisData) -> Dict[str, Any]:
    """Comprehensive page analysis including barriers and content"""
    try:
        result = await scraper.analyze_page_comprehensive(data.url)
        return result
    except Exception as e:
        logger.error(f"Error analyzing page {data.url}: {str(e)}")
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }

@mcp.tool(
    name="scrape_form_fields", 
    description="Extracts all input fields from a specific form on a page with detailed field information."
)
async def scrape_form_fields(data: FormFieldsData) -> Dict[str, Any]:
    """Extract form fields with maximum detail and intelligence"""
    try:
        result = await scraper.extract_form_fields_ultra(data.url, data.form_index)
        return result
    except Exception as e:
        logger.error(f"Error extracting form fields from {data.url}: {str(e)}")
        return {
            "success": False,
            "error": f"Field extraction failed: {str(e)}"
        }

@mcp.tool(
    name="validate_form_data",
    description="Validates form data against the form structure before submission."
)
async def validate_form_data(data: FormSubmissionData) -> Dict[str, Any]:
    """Validate form data before submission"""
    try:
        result = await submitter.validate_submission(data.url, data.field_data, data.form_index)
        return result
    except Exception as e:
        logger.error(f"Error validating form data for {data.url}: {str(e)}")
        return {
            "valid": False,
            "error": f"Validation failed: {str(e)}"
        }

@mcp.tool(
    name="submit_form",
    description="Submits a form with the provided data, handles retries and various submission methods."
)
async def submit_form(data: FormSubmissionData) -> Dict[str, Any]:
    """Submit form with ultra-robust error handling and retry logic"""
    try:
        # First validate the data
        validation = await submitter.validate_submission(data.url, data.field_data, data.form_index)
        
        if not validation.get('valid', False):
            return {
                "success": False,
                "error": "Form validation failed",
                "validation_issues": validation.get('issues', []),
                "warnings": validation.get('warnings', [])
            }
        
        # Submit the form
        result = await submitter.submit_form_ultra(data.url, data.field_data, data.form_index)
        
        # Add validation info to result
        result['validation'] = validation
        return result
        
    except Exception as e:
        logger.error(f"Error submitting form to {data.url}: {str(e)}")
        return {
            "success": False,
            "error": f"Submission failed: {str(e)}"
        }

@mcp.tool(
    name="test_form_access",
    description="Tests if a form URL is accessible and identifies potential barriers like login walls, CAPTCHAs, etc."
)
async def test_form_access(data: URLTestData) -> Dict[str, Any]:
    """Test if URL is accessible and detect potential barriers"""
    try:
        result = await scraper.test_url_accessibility(data.url)
        return result
    except Exception as e:
        logger.error(f"Error testing URL accessibility {data.url}: {str(e)}")
        return {
            "accessible": False,
            "error": f"Access test failed: {str(e)}"
        }

# Cleanup function
async def cleanup():
    """Clean up resources on shutdown"""
    try:
        await scraper.close()
        await submitter.close()
        logger.info("🔒 Cleaned up resources")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    print("🤖 Starting Ultra Form Automation MCP Server...")
    print("📍 Available tools:")
    print("  - analyze_page: Analyze webpage for forms and barriers")
    print("  - scrape_form_fields: Extract detailed form field information")
    print("  - validate_form_data: Validate form data before submission")
    print("  - submit_form: Submit forms with robust error handling")
    print("  - test_form_access: Test URL accessibility and detect barriers")
    print("  - health_check: Server health monitoring")
    print()
    print(f"🌐 Server will be available on port {PORT}:")
    print(f"  - SSE mode: http://0.0.0.0:{PORT}/sse")
    print(f"  - Streamable HTTP mode: http://0.0.0.0:{PORT}/mcp")
    print()
    
    # Detect if running on Railway
    if os.getenv("RAILWAY_ENVIRONMENT"):
        print("🚂 Running on Railway!")
        print(f"   Public URL will be available after deployment")
    
    try:
        # Use SSE transport by default
        mcp.run(transport="sse")
    except KeyboardInterrupt:
        print("\n🛑 Server shutting down...")
        asyncio.run(cleanup())
    except Exception as e:
        logger.error(f"Server error: {e}")
        asyncio.run(cleanup())
