from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI()

class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any] = {}

@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest):
    
    if request.method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "pdf-generator",
                "version": "1.0"
            }
        }

    elif request.method == "tools/list":
        return {
            "tools": [
                {
                    "name": "generate_pdf",
                    "description": "Generate a PDF from text",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["title", "content"]
                    }
                }
            ]
        }

    elif request.method == "tools/call":
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})

        if tool_name == "generate_pdf":
            title = arguments.get("title")
            content = arguments.get("content")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"PDF generated with title: {title}"
                    }
                ]
            }

    return {"error": "Unknown method"}
