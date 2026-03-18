from datetime import datetime
from pathlib import Path
import contextlib

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, Response
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from weasyprint import HTML

PUBLIC_BASE_URL = "https://agent-pdf-service.onrender.com"
OUTPUT_DIR = Path("/tmp/generated_pdfs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

transport_security = TransportSecuritySettings(
    allowed_hosts=[
        "127.0.0.1:*",
        "localhost:*",
        "[::1]:*",
        "agent-pdf-service.onrender.com",
        "agent-pdf-service.onrender.com:*",
    ]
)

mcp = FastMCP(
    "render-pdf-server",
    json_response=True,
    transport_security=transport_security,
)

# Faz o endpoint MCP responder diretamente em /mcp quando montado
mcp.settings.streamable_http_path = "/"


@mcp.tool()
def ping() -> str:
    """Simple connectivity test."""
    return "MCP server is connected and working."


@mcp.tool()
def generate_pdf(title: str, content: str) -> dict:
    """Generate a PDF from title and content and return a download URL."""
    safe_timestamp = str(datetime.now().timestamp()).replace(".", "_")
    file_name = f"document_{safe_timestamp}.pdf"
    file_path = OUTPUT_DIR / file_name

    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
            }}
            h1 {{
                color: #2c3e50;
                margin-bottom: 20px;
            }}
            p {{
                line-height: 1.6;
                white-space: pre-wrap;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <p>{content}</p>
    </body>
    </html>
    """

    HTML(string=html_content).write_pdf(str(file_path))

    return {
        "status": "success",
        "filename": file_name,
        "download_url": f"{PUBLIC_BASE_URL}/files/{file_name}",
    }


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def health():
    return {"message": "Server is running"}


# Permite que o Agent Builder faça probe por GET sem tomar 400
@app.get("/mcp")
async def mcp_probe_root():
    return Response(status_code=200)


@app.get("/mcp/")
async def mcp_probe():
    return Response(status_code=200)


@app.get("/files/{filename}")
async def serve_file(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=filename,
    )


app.mount("/mcp", mcp.streamable_http_app())
