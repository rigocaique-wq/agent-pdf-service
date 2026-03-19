from datetime import datetime
from pathlib import Path
import contextlib
import html
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from weasyprint import HTML
import markdown

PUBLIC_BASE_URL = "https://agent-pdf-service.onrender.com"

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path("/tmp/generated_pdfs")
HEADER_IMAGE = BASE_DIR / "header-doc.png"

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

# Faz o endpoint MCP responder diretamente em /mcp/ quando montado em /mcp
mcp.settings.streamable_http_path = "/"


@mcp.tool()
def ping() -> str:
    """Simple connectivity test."""
    return "MCP server is connected and working."


def normalize_title(title: str) -> str:
    title = (title or "Project Documentation").strip()
    return html.escape(title)


def normalize_markdown(content: str) -> str:
    content = (content or "").strip()

    # Remove blocos ```markdown ... ``` se vierem do modelo
    content = re.sub(r"^```(?:markdown|md)?\s*", "", content, flags=re.IGNORECASE)
    content = re.sub(r"\s*```$", "", content)

    return content.strip()


def remove_duplicated_title_from_content(title: str, content: str) -> str:
    """
    Remove um H1 inicial duplicado do markdown quando ele repete o mesmo title.
    Exemplo:
    title = "My Doc"
    content começa com "# My Doc"
    """
    normalized_title = (title or "").strip().lower()
    lines = content.splitlines()

    if not lines:
        return content

    first_non_empty_idx = None
    for i, line in enumerate(lines):
        if line.strip():
            first_non_empty_idx = i
            break

    if first_non_empty_idx is None:
        return content

    first_line = lines[first_non_empty_idx].strip()

    if first_line.startswith("# "):
        heading_text = first_line[2:].strip().lower()
        if heading_text == normalized_title:
            del lines[first_non_empty_idx]

            # remove linhas vazias logo após o título removido
            while first_non_empty_idx < len(lines) and not lines[first_non_empty_idx].strip():
                del lines[first_non_empty_idx]

    return "\n".join(lines).strip()


def markdown_to_html(content: str) -> str:
    normalized = normalize_markdown(content)
    return markdown.markdown(
        normalized,
        extensions=["extra", "sane_lists", "nl2br"],
        output_format="html5",
    )


@mcp.tool()
def generate_pdf(title: str, content: str) -> dict:
    """Generate a styled PDF from markdown content and return a download URL."""
    safe_timestamp = str(datetime.now().timestamp()).replace(".", "_")
    file_name = f"document_{safe_timestamp}.pdf"
    file_path = OUTPUT_DIR / file_name

    safe_title = normalize_title(title)

    cleaned_content = normalize_markdown(content)
    cleaned_content = remove_duplicated_title_from_content(title, cleaned_content)

    body_html = markdown_to_html(cleaned_content)

    header_image_uri = HEADER_IMAGE.as_uri()

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <title>{safe_title}</title>
        <style>
            @page {{
                size: A4;
                margin: 75px 55px 85px 55px;

                @bottom-center {{
                    content: "3301 N University Drive, Suite 400, Coral Springs, FL 33065   |   www.datameaning.com   |   888.4BI.DATA";
                    font-size: 9pt;
                    color: #9aa9bf;
                }}
            }}

            :root {{
                --primary: #2f5faa;
                --primary-dark: #173a70;
                --text: #5f718b;
                --title: #2f5faa;
                --border: #d9e1ee;
                --link: #5b6fd6;
            }}

            html {{
                font-size: 11pt;
            }}

            body {{
                font-family: Arial, Helvetica, sans-serif;
                color: var(--text);
                margin: 0;
                padding: 0;
            }}

            .page-header {{
                 position: fixed;
                 top: -75px;
                 left: -55px;
                 right: -55px;
                 height: 52px;
            }}

            .header-image {{
                display: block;
                width: calc(100% + 110px);
                height: 52px;
            }}

            .content {{
                margin: 0;
                padding: 0;
            }}

            .doc-title {{
                color: var(--title);
                font-size: 24pt;
                font-weight: 700;
                margin: 0 0 26px 0;
                line-height: 1.2;
            }}

            h1 {{
                color: var(--title);
                font-size: 24pt;
                font-weight: 700;
                margin: 0 0 26px 0;
                line-height: 1.2;
            }}

            h2 {{
                color: var(--primary-dark);
                font-family: Georgia, "Times New Roman", serif;
                font-size: 16pt;
                font-weight: 700;
                margin: 28px 0 14px 0;
                line-height: 1.25;
                page-break-after: avoid;
            }}

            h3 {{
                color: var(--primary-dark);
                font-family: Georgia, "Times New Roman", serif;
                font-size: 13pt;
                font-weight: 700;
                margin: 18px 0 10px 0;
                line-height: 1.25;
                page-break-after: avoid;
            }}

            p {{
                margin: 0 0 12px 0;
                line-height: 1.6;
                text-align: left;
            }}

            ul, ol {{
                margin: 0 0 14px 24px;
                padding: 0;
            }}

            li {{
                margin: 0 0 6px 0;
                line-height: 1.5;
            }}

            strong {{
                color: #42536d;
                font-weight: 700;
            }}

            a {{
                color: var(--link);
                text-decoration: underline;
            }}

            hr {{
                border: none;
                border-top: 1px solid var(--border);
                margin: 20px 0;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 12px 0 16px 0;
                font-size: 10.5pt;
            }}

            th, td {{
                border: 1px solid var(--border);
                padding: 8px 10px;
                vertical-align: top;
            }}

            th {{
                background: #f4f7fc;
                color: var(--primary-dark);
                text-align: left;
            }}

            blockquote {{
                margin: 12px 0;
                padding: 10px 14px;
                border-left: 4px solid var(--primary);
                background: #f7faff;
                color: #51647f;
            }}

            code {{
                font-family: "Courier New", monospace;
                font-size: 9.5pt;
                background: #f2f4f8;
                padding: 1px 4px;
                border-radius: 3px;
            }}

            pre {{
                font-family: "Courier New", monospace;
                font-size: 9.5pt;
                background: #f2f4f8;
                padding: 10px 12px;
                border-radius: 4px;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
        </style>
    </head>
    <body>
        <div class="page-header">
            <img src="{header_image_uri}" alt="Document Header" class="header-image">
        </div>

        <main class="content">
            <h1 class="doc-title">{safe_title}</h1>
            {body_html}
        </main>
    </body>
    </html>
    """

    HTML(
        string=html_content,
        base_url=BASE_DIR.as_uri()
    ).write_pdf(str(file_path))

    download_url = f"{PUBLIC_BASE_URL}/files/{file_name}"

    return {
        "content": [
            {
                "type": "text",
                "text": f"PDF generated successfully.\nDownload it here: {download_url}"
            }
        ],
        "structuredContent": {
            "status": "success",
            "filename": file_name,
            "download_url": download_url
        }
    }


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def health():
    return {"message": "Server is running"}


# Redireciona /mcp -> /mcp/ preservando o método HTTP
@app.api_route("/mcp", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def mcp_redirect():
    return RedirectResponse(url="/mcp/", status_code=307)


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
