from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from mcp.server.fastmcp import FastMCP
from weasyprint import HTML

# =========================
# CONFIG
# =========================

PUBLIC_BASE_URL = "https://agent-pdf-service.onrender.com"
OUTPUT_DIR = Path("/tmp/generated_pdfs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# MCP SETUP
# =========================

mcp = FastMCP("render-pdf-server")


@mcp.tool()
def ping() -> str:
    """Test connection."""
    return "MCP server is connected and working."


@mcp.tool()
def generate_pdf(title: str, content: str) -> dict:
    """Generate a PDF from text content."""

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


# =========================
# FASTAPI APP
# =========================

app = FastAPI()


@app.get("/")
def health():
    return {"message": "Server is running"}


# 🔥 CORREÇÃO IMPORTANTE (resolve seu erro atual)
@app.get("/mcp")
def redirect_mcp():
    return RedirectResponse(url="/mcp/")


# =========================
# FILE DOWNLOAD
# =========================

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


# =========================
# MCP MOUNT
# =========================

app.mount("/mcp", mcp.streamable_http_app())
