from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from fastapi.responses import FileResponse
import os
from datetime import datetime
from weasyprint import HTML

app = FastAPI()

API_KEY = os.getenv("API_KEY")

class RequestData(BaseModel):
    title: str
    content: str

@app.get("/")
def home():
    return {"message": "API is running"}

@app.post("/generate-pdf")
def generate_pdf(
    data: RequestData,
    authorization: str = Header(default=None)
):
    try:
        if not API_KEY:
            raise HTTPException(status_code=500, detail="API_KEY not configured on server")

        if not authorization:
            raise HTTPException(status_code=401, detail="Missing Authorization header")

        expected_value = f"Bearer {API_KEY}"
        if authorization != expected_value:
            raise HTTPException(status_code=401, detail="Invalid API key")

        html_content = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial;
                    margin: 40px;
                }}
                h1 {{
                    color: #2c3e50;
                }}
                p {{
                    line-height: 1.6;
                }}
            </style>
        </head>
        <body>
            <h1>{data.title}</h1>
            <p>{data.content}</p>
        </body>
        </html>
        """

        file_name = f"document_{datetime.now().timestamp()}.pdf"
        HTML(string=html_content).write_pdf(file_name)

        return FileResponse(
            file_name,
            media_type="application/pdf",
            filename=file_name
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
