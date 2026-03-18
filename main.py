from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
import os
from datetime import datetime
from weasyprint import HTML

app = FastAPI()

class RequestData(BaseModel):
    title: str
    content: str

@app.get("/")
def home():
    return {"message": "API is running"}

@app.post("/generate-pdf")
def generate_pdf(data: RequestData):
    try:
        # Create HTML content
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

        # File name
        file_name = f"document_{datetime.now().timestamp()}.pdf"

        # Generate PDF
        HTML(string=html_content).write_pdf(file_name)

        return FileResponse(file_name, media_type='application/pdf', filename=file_name)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
