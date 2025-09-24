import os
import cv2
from PIL import Image
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from typing import Dict, Any, List
import json
import numpy as np

class VideoAnalysisAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7,
            convert_system_message_to_human=True
        )
        
        self.prompt_template = PromptTemplate(
            input_variables=["frame_analysis", "video_info", "criteria"],
            template="""
            Você é um jurado especialista em análise audiovisual. Analise o seguinte conteúdo de vídeo.
            ANÁLISE DOS FRAMES PRINCIPAIS: {frame_analysis}
            INFORMAÇÕES TÉCNICAS DO VÍDEO: {video_info}
            CRITÉRIOS DE AVALIAÇÃO: {criteria}
            
            Com base em tudo, forneça uma análise detalhada em JSON com:
            - pontuacao: (A nota numérica que você deu)
            - pontuacao_maxima: (O valor máximo da escala que você utilizou. Se os critérios pediram uma escala de 0-25, este valor deve ser 25. Se não, o padrão é 100.)
            - feedback: análise detalhada
            - qualidade_tecnica: avaliação técnica do vídeo
            - cinematografia: análise da composição visual
            - narrativa: avaliação do conteúdo/história
            - pontos_fortes: lista de pontos positivos
            - pontos_melhoria: lista de sugestões de melhoria
            - veredicto: resumo da avaliação
            """
        )
        
        self.chain = self.prompt_template | self.llm
    
    def _extract_video_info(self, video_path: str) -> Dict[str, Any]:
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened(): raise IOError("Não foi possível abrir o vídeo")
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            info = { "duracao": duration, "fps": fps, "resolucao": f"{width}x{height}" }
            cap.release()
            return info
        except Exception as e:
            return {"erro": f"Erro ao extrair informações: {str(e)}"}
    
    def _extract_key_frames(self, video_path: str, num_frames: int = 3) -> List[Image.Image]:
        frames = []
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened(): raise IOError("Não foi possível abrir o vídeo para extrair frames")
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames == 0: return []
            frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
            for index in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, index)
                ret, frame = cap.read()
                if ret:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(rgb_frame)
                    frames.append(pil_image)
            cap.release()
            return frames
        except Exception as e:
            if 'cap' in locals() and cap.isOpened(): cap.release()
            return frames
    
    def _analyze_frame(self, frame: Image.Image, frame_number: int) -> str:
        try:
            prompt = "Analise este frame de um vídeo. Descreva concisamente os elementos visuais principais e a composição."
            response = self.vision_model.generate_content([prompt, frame])
            return f"Frame {frame_number}: {response.text}"
        except Exception as e:
            return f"Frame {frame_number}: Erro na análise - {str(e)}"
    
    def analyze(self, video_path: str, criteria: str = "Avaliação geral") -> Dict[str, Any]:
        try:
            video_info = self._extract_video_info(video_path)
            frames = self._extract_key_frames(video_path)
            frame_analyses = [self._analyze_frame(frame, i) for i, frame in enumerate(frames, 1)]
            frame_analysis_text = "\n\n".join(frame_analyses)
            
            result = self.chain.invoke({
                "frame_analysis": frame_analysis_text,
                "video_info": json.dumps(video_info, indent=2, ensure_ascii=False),
                "criteria": criteria
            })
            content = result.content if hasattr(result, 'content') else str(result)
            
            try:
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    analysis = json.loads(content[start_idx:end_idx])
                else:
                    analysis = {"pontuacao": 0, "feedback": content}
            except json.JSONDecodeError:
                analysis = {"pontuacao": 0, "feedback": content}

            analysis["tipo"] = "video"
            analysis["agente"] = "VideoAnalysisAgent"
            analysis["info_tecnica"] = video_info
            
            return analysis
        except Exception as e:
            return {"erro": str(e), "pontuacao": 0, "tipo": "video", "agente": "VideoAnalysisAgent"}