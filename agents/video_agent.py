import os
import cv2  
from PIL import Image
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
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
            Você é um jurado especialista em análise audiovisual. Analise o seguinte conteúdo de vídeo com base nos critérios fornecidos:
            
            ANÁLISE DOS FRAMES PRINCIPAIS:
            {frame_analysis}
            
            INFORMAÇÕES TÉCNICAS DO VÍDEO:
            {video_info}
            
            CRITÉRIOS DE AVALIAÇÃO:
            {criteria}
            
            Por favor, forneça uma análise detalhada considerando:
            1. Qualidade visual e técnica
            2. Composição e cinematografia
            3. Narrativa e conteúdo
            4. Criatividade e originalidade
            5. Fluidez e montagem
            6. Adequação aos critérios
            
            Retorne sua análise em formato JSON com:
            - pontuacao: (0-100)
            - feedback: análise detalhada
            - qualidade_tecnica: avaliação técnica do vídeo
            - cinematografia: análise da composição visual
            - narrativa: avaliação do conteúdo/história
            - criatividade: avaliação da criatividade
            - pontos_fortes: lista de pontos positivos
            - pontos_melhoria: lista de sugestões de melhoria
            - veredicto: resumo da avaliação
            """
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
    
    def _extract_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Extrai informações técnicas do vídeo usando OpenCV
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise IOError("Não foi possível abrir o arquivo de vídeo")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            info = {
                "duracao": duration,
                "fps": fps,
                "resolucao": f"{width}x{height}",
                "formato": video_path.split('.')[-1],
                "tamanho_mb": os.path.getsize(video_path) / (1024 * 1024),
                "aspect_ratio": round(width / height, 2) if height > 0 else 0
            }
            cap.release()
            return info
        except Exception as e:
            return {"erro": f"Erro ao extrair informações com OpenCV: {str(e)}"}

    def _extract_key_frames(self, video_path: str, num_frames: int = 5) -> List[Image.Image]:
        """
        Extrai frames chave do vídeo para análise usando OpenCV
        """
        frames = []
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise IOError("Não foi possível abrir o arquivo de vídeo para extrair frames")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames == 0:
                return []

            frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
            
            for index in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, index)
                ret, frame = cap.read()
                if ret:
                    # Converte de BGR (formato do OpenCV) para RGB (formato do Pillow/PIL)
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(rgb_frame)
                    frames.append(pil_image)
            
            cap.release()
            return frames
        except Exception as e:
            print(f"Erro ao extrair frames com OpenCV: {str(e)}")
            if 'cap' in locals() and cap.isOpened():
                cap.release()
            return frames
    
    def _analyze_frame(self, frame: Image.Image, frame_number: int) -> str:
        try:
            prompt = f"""
            Analise este frame {frame_number} do vídeo. Descreva:
            1. Elementos visuais principais
            2. Qualidade da imagem
            3. Composição e enquadramento
            4. Cores e iluminação
            5. Qualquer elemento narrativo visível
            
            Seja conciso mas detalhado.
            """
            response = self.vision_model.generate_content([prompt, frame])
            return f"Frame {frame_number}: {response.text}"
        except Exception as e:
            return f"Frame {frame_number}: Erro na análise - {str(e)}"
    
    def analyze(self, video_path: str, criteria: str = "Avaliação geral de qualidade audiovisual") -> Dict[str, Any]:
        try:
            video_info = self._extract_video_info(video_path)
            if "erro" in video_info:
                return {**video_info, "tipo": "video", "agente": "VideoAnalysisAgent"}
                
            frames = self._extract_key_frames(video_path)
            
            frame_analyses = [self._analyze_frame(frame, i) for i, frame in enumerate(frames, 1)]
            frame_analysis_text = "\n\n".join(frame_analyses)
            
            result = self.chain.run(
                frame_analysis=frame_analysis_text,
                video_info=json.dumps(video_info, indent=2, ensure_ascii=False),
                criteria=criteria
            )
            
            try:
                start_idx = result.find('{')
                end_idx = result.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_content = result[start_idx:end_idx]
                    analysis = json.loads(json_content)
                else:
                    analysis = {"pontuacao": 75, "feedback": result}
            except json.JSONDecodeError:
                analysis = {"pontuacao": 70, "feedback": result}
            
            analysis["tipo"] = "video"
            analysis["agente"] = "VideoAnalysisAgent"
            analysis["info_tecnica"] = video_info
            analysis["frames_analisados"] = len(frames)
            
            return analysis
        except Exception as e:
            return {"erro": str(e), "pontuacao": 0, "tipo": "video", "agente": "VideoAnalysisAgent"}

    def analyze_short_form(self, video_path: str) -> Dict[str, Any]:
        criteria = """Análise para vídeo curto (TikTok, Shorts): Impacto visual, engajamento, criatividade, qualidade técnica e relevância."""
        return self.analyze(video_path, criteria)

    def analyze_cinematic(self, video_path: str) -> Dict[str, Any]:
        criteria = """Análise cinematográfica: Fotografia, iluminação, montagem, ritmo, direção de arte, som e narrativa."""
        return self.analyze(video_path, criteria)

    def compare_videos(self, video_paths: list, criteria: str = "Comparação audiovisual") -> list:
        results = []
        for i, video_path in enumerate(video_paths):
            result = self.analyze(video_path, f"{criteria} - Vídeo {i+1}")
            result["item_id"] = i + 1
            results.append(result)
        return results