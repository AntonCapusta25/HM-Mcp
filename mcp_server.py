#!/usr/bin/env python3
"""
Standalone Ultra-Robust Form Automation Server
Works without MCP package - uses FastAPI for HTTP endpoints
Can be connected to ChatGPT via Custom GPT Actions instead of MCP
"""

import asyncio
import json
import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Web Framework
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our components
from form_scraper import UltraFormScraper
from form_submitter import UltraFormSubmitter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Ultra Form Automation API",
    description="Ultra-robust form automation with barrier bypass capabilities",
    version="2.0.0"
)

# Add CORS middleware for ChatGPT integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
scraper = UltraFormScraper()
submitter = UltraFormSubmitter()

# Pydantic models for request/response
class AnalyzePageRequest(BaseModel):
    url: str

class ScrapeFormRequest(BaseModel):
    url: str
    form_index: int = 0

class SubmitFormRequest(BaseModel):
    url: str
    field_data: Dict[str, str]
    form_index: int = 0
    dry_run: bool = False

class ScrapeAndSubmitRequest(BaseModel):
    url: str
    field_data: Dict[str, str]
    form_index: int = 0
    dry_run: bool = False

class FieldSuggestionRequest(BaseModel):
    field_info: Dict[str, Any]

# API Endpoints (ChatGPT can call these)

@app.post("/analyze-page")
async def analyze_page(request: AnalyzePageRequest) -> Dict[str, Any]:
    """
    Analyze a webpage for forms and potential barriers.
    Returns page analysis without filling anything.
    """
    logger.info(f"Analyzing page: {request.url}")
    
    try:
        analysis = await scraper.analyze_page_comprehensive(request.url)
        
        if analysis.get('error'):
            return {
                "success": False,
                "error": analysis['error'],
                "url": request.url
            }
        
        return {
            "success": True,
            "url": request.url,
            "page_title": analysis.get('title', 'Unknown'),
            "forms_found": analysis.get('forms_count', 0),
            "barriers_detected": analysis.get('barriers', []),
            "page_type": analysis.get('page_type', 'unknown'),
            "is_accessible": analysis.get('accessible', True),
            "warnings": analysis.get('warnings', []),
            "recommendations": analysis.get('recommendations', [])
        }
        
    except Exception as e:
        logger.error(f"Error analyzing page {request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/scrape-form")
async def scrape_form(request: ScrapeFormRequest) -> Dict[str, Any]:
    """
    Scrape form fields from a webpage.
    Returns structured field data for ChatGPT to generate responses.
    """
    logger.info(f"Scraping form from: {request.url}")
    
    try:
        # First analyze the page
        analysis = await scraper.analyze_page_comprehensive(request.url)
        
        if analysis.get('error'):
            return {
                "success": False,
                "error": analysis['error'],
                "url": request.url
            }
        
        if analysis.get('forms_count', 0) == 0:
            return {
                "success": False,
                "error": "No forms found on this page",
                "url": request.url,
                "page_type": analysis.get('page_type'),
                "barriers": analysis.get('barriers', [])
            }
        
        # Extract form fields
        form_data = await scraper.extract_form_fields_ultra(request.url, request.form_index)
        
        if not form_data.get('success'):
            return {
                "success": False,
                "error": form_data.get('error', 'Unknown scraping error'),
                "url": request.url
            }
        
        fields = form_data.get('fields', [])
        
        # Format fields for ChatGPT consumption
        formatted_fields = []
        for field in fields:
            field_info = {
                "id": field.get('identifier'),
                "name": field.get('name'),
                "label": field.get('label'),
                "type": field.get('type'),
                "required": field.get('required', False),
                "placeholder": field.get('placeholder'),
                "options": field.get('options', []),
                "max_length": field.get('max_length'),
                "pattern": field.get('pattern'),
                "description": field.get('description'),
                "validation_rules": field.get('validation_rules', [])
            }
            formatted_fields.append(field_info)
        
        return {
            "success": True,
            "url": request.url,
            "form_index": request.form_index,
            "fields": formatted_fields,
            "field_count": len(formatted_fields),
            "submit_info": form_data.get('submit_info', {}),
            "form_action": form_data.get('form_action'),
            "form_method": form_data.get('form_method', 'POST'),
            "warnings": analysis.get('warnings', []),
            "barriers_bypassed": analysis.get('barriers_bypassed', [])
        }
        
    except Exception as e:
        logger.error(f"Error scraping form from {request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.post("/submit-form")
async def submit_form(request: SubmitFormRequest) -> Dict[str, Any]:
    """
    Submit form with provided field data.
    field_data should be a dictionary: {"field_id": "value", ...}
    """
    logger.info(f"Submitting form to: {request.url} (dry_run: {request.dry_run})")
    
    try:
        if request.dry_run:
            # Just validate the data without submitting
            validation = await submitter.validate_submission(request.url, request.field_data, request.form_index)
            return {
                "success": True,
                "action": "validation",
                "url": request.url,
                "validation_result": validation,
                "would_submit": validation.get('valid', False),
                "issues": validation.get('issues', [])
            }
        
        # Actually submit the form
        result = await submitter.submit_form_ultra(request.url, request.field_data, request.form_index)
        
        return {
            "success": result.get('success', False),
            "action": "submission",
            "url": request.url,
            "status_code": result.get('status_code'),
            "response_url": result.get('response_url'),
            "confirmation": result.get('confirmation'),
            "message": result.get('message'),
            "error": result.get('error'),
            "redirect_chain": result.get('redirect_chain', []),
            "submission_evidence": result.get('evidence', {})
        }
        
    except Exception as e:
        logger.error(f"Error submitting form to {request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Submission failed: {str(e)}")

@app.post("/scrape-and-submit")
async def scrape_and_submit(request: ScrapeAndSubmitRequest) -> Dict[str, Any]:
    """
    Combined endpoint: Scrape form fields AND submit with provided data.
    Most convenient for single-step automation.
    """
    logger.info(f"Scrape and submit for: {request.url}")
    
    try:
        # First scrape to get form structure
        scrape_req = ScrapeFormRequest(url=request.url, form_index=request.form_index)
        scrape_result = await scrape_form(scrape_req)
        
        if not scrape_result.get('success'):
            return scrape_result  # Return the scraping error
        
        # Then submit with provided data
        submit_req = SubmitFormRequest(
            url=request.url, 
            field_data=request.field_data, 
            form_index=request.form_index,
            dry_run=request.dry_run
        )
        submit_result = await submit_form(submit_req)
        
        return {
            "success": submit_result.get('success', False),
            "url": request.url,
            "scraping": {
                "fields_found": scrape_result.get('field_count', 0),
                "warnings": scrape_result.get('warnings', [])
            },
            "submission": submit_result,
            "combined_action": True
        }
        
    except Exception as e:
        logger.error(f"Error in scrape_and_submit for {request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Combined operation failed: {str(e)}")

@app.post("/test-form-access")
async def test_form_access(request: AnalyzePageRequest) -> Dict[str, Any]:
    """
    Test if a form URL is accessible and what barriers might exist.
    Quick check before attempting full automation.
    """
    logger.info(f"Testing access to: {request.url}")
    
    try:
        test_result = await scraper.test_url_accessibility(request.url)
        
        return {
            "success": True,
            "url": request.url,
            "accessible": test_result.get('accessible', False),
            "status_code": test_result.get('status_code'),
            "content_type": test_result.get('content_type'),
            "final_url": test_result.get('final_url'),
            "redirect_count": test_result.get('redirect_count', 0),
            "barriers_detected": test_result.get('barriers', []),
            "estimated_success_rate": test_result.get('success_probability', 0.0),
            "recommendations": test_result.get('recommendations', []),
            "page_load_time": test_result.get('load_time', 0.0)
        }
        
    except Exception as e:
        logger.error(f"Error testing access to {request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Access test failed: {str(e)}")

@app.post("/field-suggestions")
async def get_field_suggestions(request: FieldSuggestionRequest) -> Dict[str, Any]:
    """
    Get suggestions for filling a specific field based on its properties.
    Helps ChatGPT understand what kind of content to generate.
    """
    try:
        field_info = request.field_info
        field_type = field_info.get('type', '').lower()
        field_name = field_info.get('name', '').lower()
        field_label = field_info.get('label', '').lower()
        
        suggestions = {
            "field_id": field_info.get('id'),
            "content_type": "unknown",
            "examples": [],
            "constraints": [],
            "best_practices": []
        }
        
        # Analyze field type and name to provide suggestions
        if field_type in ['email']:
            suggestions.update({
                "content_type": "email",
                "examples": ["john.doe@email.com"],
                "constraints": ["Must be valid email format"],
                "best_practices": ["Use professional email address"]
            })
        elif field_type in ['tel', 'phone'] or 'phone' in field_name:
            suggestions.update({
                "content_type": "phone",
                "examples": ["(555) 123-4567", "+1-555-123-4567"],
                "constraints": ["Include area code"],
                "best_practices": ["Use consistent format"]
            })
        elif field_type == 'textarea' and any(word in field_name for word in ['cover', 'letter', 'motivation', 'why']):
            suggestions.update({
                "content_type": "cover_letter",
                "examples": ["Dear Hiring Manager, I am excited to apply..."],
                "constraints": [f"Max length: {field_info.get('max_length', 'unlimited')}"],
                "best_practices": ["Personalize for the specific role", "Highlight relevant experience"]
            })
        elif field_type == 'select':
            suggestions.update({
                "content_type": "selection",
                "examples": field_info.get('options', []),
                "constraints": ["Must choose from available options"],
                "best_practices": ["Choose option that best matches profile"]
            })
        elif 'experience' in field_name or 'years' in field_name:
            suggestions.update({
                "content_type": "experience_years",
                "examples": ["3-5 years", "5+ years", "Entry level"],
                "constraints": ["Should match actual experience"],
                "best_practices": ["Be honest about experience level"]
            })
        elif 'salary' in field_name or 'compensation' in field_name:
            suggestions.update({
                "content_type": "salary",
                "examples": ["$80,000", "$70,000 - $90,000", "Negotiable"],
                "constraints": ["Research market rates"],
                "best_practices": ["Consider location and experience level"]
            })
        
        return {
            "success": True,
            "field_analysis": suggestions,
            "field_info": field_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Field suggestion analysis failed: {str(e)}")

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Simple health check to verify server is working"""
    return {
        "success": True,
        "status": "healthy",
        "server": "ultra-form-automation",
        "version": "2.0",
        "endpoints": [
            "/analyze-page",
            "/scrape-form", 
            "/submit-form",
            "/scrape-and-submit",
            "/test-form-access",
            "/field-suggestions",
            "/health"
        ]
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Ultra Form Automation API",
        "version": "2.0.0",
        "description": "Ultra-robust form automation with barrier bypass capabilities",
        "endpoints": {
            "POST /analyze-page": "Analyze webpage for forms and barriers",
            "POST /scrape-form": "Extract form field structure",
            "POST /submit-form": "Submit form with data",
            "POST /scrape-and-submit": "Combined scraping and submission",
            "POST /test-form-access": "Test URL accessibility",
            "POST /field-suggestions": "Get field filling suggestions",
            "GET /health": "Health check"
        },
        "integration": "Connect to ChatGPT via Custom GPT Actions"
    }

def main():
    """Main entry point for the server"""
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting Ultra Form Automation Server on {host}:{port}")
    logger.info("Available endpoints:")
    logger.info("  POST /analyze-page - Analyze webpage for forms and barriers")
    logger.info("  POST /scrape-form - Extract form fields structure")
    logger.info("  POST /submit-form - Submit form with provided data")
    logger.info("  POST /scrape-and-submit - Combined scraping and submission")
    logger.info("  POST /test-form-access - Test URL accessibility")
    logger.info("  POST /field-suggestions - Get field filling suggestions")
    logger.info("  GET /health - Server health status")
    logger.info("")
    logger.info("🤖 Connect to ChatGPT via Custom GPT Actions!")
    logger.info(f"📡 API Base URL: http://{host}:{port}")
    
    # Run the server
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()