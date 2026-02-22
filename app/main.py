from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.xml_tools import summarize_xml_for_llm
from app.llm import run_openai, run_anthropic

app = FastAPI()

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/analyze")
async def analyze(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    output_format: str = Form("csv"),          # "csv" or "xml"
    provider: str = Form("openai"),            # "openai" or "anthropic"
    model: str = Form(""),                     # optional override
):
    if output_format not in ("csv", "xml"):
        raise HTTPException(status_code=400, detail="output_format must be csv or xml")
    if provider not in ("openai", "anthropic"):
        raise HTTPException(status_code=400, detail="provider must be openai or anthropic")

    xml_bytes = await file.read()
    if not xml_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    # Summarize XML so we don't blindly dump huge XML into the LLM
    try:
        xml_summary = summarize_xml_for_llm(xml_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"XML parse failed: {e}")

    # Build instruction to force strict output format
    format_rules = (
        "Return ONLY valid CSV text (no markdown, no code fences). "
        "Include a header row. Escape quotes with double quotes.\n"
        if output_format == "csv"
        else
        "Return ONLY valid XML text (no markdown, no code fences). "
        "Wrap all results in a single root element <result>...</result>.\n"
    )

    llm_input = f"""
You are an assistant that transforms XML into structured outputs.
User request:
{prompt}

XML summary (structure + samples):
{xml_summary}

Output requirements:
{format_rules}

Important:
- Do not include explanations.
- Do not include ``` fences.
- Output ONLY the {output_format.upper()}.
""".strip()

    # Call chosen provider
    if provider == "openai":
        text = run_openai(llm_input, model=model or "gpt-4o-mini")
    else:
        text = run_anthropic(llm_input, model=model or "claude-sonnet-4-5-20250929")

    # Return as downloadable file
    filename = "result.csv" if output_format == "csv" else "result.xml"
    media_type = "text/csv" if output_format == "csv" else "application/xml"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return Response(content=text, media_type=media_type, headers=headers)