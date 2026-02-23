from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

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
    provider: str = Form("openai"), 
    model: str = Form(""),
):
    if provider not in ("openai", "anthropic"):
        raise HTTPException(status_code=400, detail="provider must be openai or anthropic")

    xml_bytes = await file.read()
    if not xml_bytes:
        raise HTTPException(status_code=400, detail="Empty file")
    
    # Convert bytes -> string
    try:
        xml_content = xml_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not valid UTF-8 text")

    llm_input = prompt.strip() + "\n\n +" xml_content

    # Call chosen provider
    if provider == "openai":
        text = run_openai(llm_input, model=model or "gpt-4o-mini")
    else:
        text = run_anthropic(llm_input, model=model or "claude-haiku-4-5")

    # Return as downloadable file
    filename = "result.csv"
    media_type = "text/csv"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return Response(content=text, media_type=media_type, headers=headers)