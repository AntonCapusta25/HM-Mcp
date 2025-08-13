import logging
import os
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from form_scraper import UltraFormScraper
from form_submitter import UltraFormSubmitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Form Automation MCP Server",
    description="A server compliant with the Model Context Protocol for form automation.",
    version="1.0.0"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

scraper = UltraFormScraper()
submitter = UltraFormSubmitter()

# -- Define MCP Tool Schemas --
class Tool(BaseModel):
    name: str
    description: str
    params: Dict[str, Any]

class ServerInfo(BaseModel):
    name: str
    version: str
    tools: List[Tool]

class ToolRunRequest(BaseModel):
    tool: str
    params: Dict[str, Any]

# -- Tool Definitions --
# This dictionary holds the metadata and implementation for each tool.
TOOLS = {
    "analyze_page": {
        "description": "Analyzes a webpage to find forms and detect barriers like CAPTCHAs.",
        "params": {"url": {"type": "string", "description": "The URL of the page to analyze."}},
        "function": scraper.analyze_page_comprehensive,
    },
    "scrape_form_fields": {
        "description": "Extracts all input fields from a specific form on a page.",
        "params": {
            "url": {"type": "string", "description": "The URL of the page with the form."},
            "form_index": {"type": "integer", "description": "The 0-based index of the form.", "default": 0},
        },
        "function": scraper.extract_form_fields_ultra,
    },
    "submit_form": {
        "description": "Submits a form with the provided data.",
        "params": {
            "url": {"type": "string", "description": "The URL of the page with the form."},
            "form_index": {"type": "integer", "description": "The 0-based index of the form.", "default": 0},
            "field_data": {"type": "object", "description": "A dictionary of field names to values."},
        },
        "function": submitter.submit_form_ultra,
    },
}

# -- MCP Endpoints --

@app.get("/", response_model=ServerInfo, summary="MCP Server Discovery")
async def get_server_info():
    """
    This endpoint allows the AI client to discover the server's capabilities,
    as per the MCP specification.
    """
    tool_list = [
        Tool(name=name, description=data["description"], params=data["params"])
        for name, data in TOOLS.items()
    ]
    return ServerInfo(
        name="ultra_form_automation_server",
        version="1.0.0",
        tools=tool_list
    )

@app.post("/tool/run", summary="MCP Tool Execution")
async def run_tool(request: ToolRunRequest = Body(...)):
    """
    This endpoint executes a tool with the provided parameters,
    as per the MCP specification.
    """
    tool_name = request.tool
    params = request.params
    
    if tool_name not in TOOLS:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")
        
    logger.info(f"Executing tool '{tool_name}' with params: {params}")
    
    try:
        tool_function = TOOLS[tool_name]["function"]
        # The await is crucial as our tool functions are async
        result = await tool_function(**params)
        return result
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while running the tool: {e}")

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 MCP server started")

@app.on_event("shutdown") 
async def shutdown_event():
    await scraper.close()
    await submitter.close()
    logger.info("✅ Cleaned up resources.")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=port, reload=True)
