from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import tempfile
import shutil
from dotenv import load_dotenv


load_dotenv()


from agents.judge_orchestrator import JudgeOrchestrator

app = FastAPI(
    title="Jurado IA - Sistema de Avaliação Inteligente",
    description="Sistema completo de avaliação de conteúdo usando IA especializada",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    # Adicione aqui os endereços do seu front-end
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


judge = JudgeOrchestrator()


class TextAnalysisRequest(BaseModel):
    text: str
    criteria: str = "Avaliação geral de qualidade"

class AnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    return {
        "message": "Jurado IA - Sistema de Avaliação Inteligente",
        "status": "Online",
        "version": "1.0.0"
    }

@app.get("/status", response_model=Dict[str, Any])
async def get_status():
    return judge.get_agent_status()

@app.post("/analyze/text", response_model=AnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    try:
        result = await judge.analyze_single_content(
            request.text, 
            'text', 
            request.criteria
        )
        if "erro" in result:
            return AnalysisResponse(success=False, error=result["erro"])
        return AnalysisResponse(success=True, data=result)
    except Exception as e:
        return AnalysisResponse(success=False, error=str(e))

@app.post("/analyze/image", response_model=AnalysisResponse)
async def analyze_image(file: UploadFile = File(...), criteria: str = Form("Avaliação geral")):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name
    
    try:
        result = judge.image_agent.analyze(temp_path, criteria)
        if "erro" in result:
             return AnalysisResponse(success=False, error=result["erro"])
        return AnalysisResponse(success=True, data=result)
    finally:
        os.unlink(temp_path)

@app.post("/analyze/audio", response_model=AnalysisResponse)
async def analyze_audio(file: UploadFile = File(...), criteria: str = Form("Avaliação geral")):
    if not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser de áudio")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name
        
    try:
        result = await judge.analyze_single_content(temp_path, 'audio', criteria)
        if "erro" in result:
             return AnalysisResponse(success=False, error=result["erro"])
        return AnalysisResponse(success=True, data=result)
    finally:
        os.unlink(temp_path)

@app.post("/analyze/video", response_model=AnalysisResponse)
async def analyze_video(file: UploadFile = File(...), criteria: str = Form("Avaliação geral")):
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser de vídeo")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name

    try:
        result = await judge.analyze_single_content(temp_path, 'video', criteria)
        if "erro" in result:
             return AnalysisResponse(success=False, error=result["erro"])
        return AnalysisResponse(success=True, data=result)
    finally:
        os.unlink(temp_path)

@app.post("/analyze/document", response_model=AnalysisResponse)
async def analyze_document(file: UploadFile = File(...), criteria: str = Form("Avaliação geral")):
    if file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail="Arquivo deve ser um PDF")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name
        
    try:
        result = judge.text_agent.analyze_document(temp_path, criteria)
        if "erro" in result:
             return AnalysisResponse(success=False, error=result["erro"])
        return AnalysisResponse(success=True, data=result)
    finally:
        os.unlink(temp_path)

@app.post("/analyze/multiple", response_model=AnalysisResponse)
async def analyze_multiple_files(
    files: List[UploadFile] = File(...),
    criteria: str = Form("Avaliação comparativa")
):
    temp_files = []
    try:
        contents = []
        for file in files:
            suffix = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                shutil.copyfileobj(file.file, temp_file)
                temp_path = temp_file.name
                temp_files.append(temp_path)
            
            contents.append({
                'path': temp_path,
                'name': file.filename
            })
        
        result = await judge.analyze_multiple_contents(contents, criteria)
        if "erro" in result.get("sintese_final", {}):
             return AnalysisResponse(success=False, error=result["sintese_final"]["erro"])
        return AnalysisResponse(success=True, data=result)
        
    except Exception as e:
        return AnalysisResponse(success=False, error=str(e))
    
    finally:
        for path in temp_files:
            if os.path.exists(path):
                os.unlink(path)

# --- Entrypoint para rodar o servidor ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)