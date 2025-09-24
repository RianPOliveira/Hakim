import os
from PIL import Image
from io import BytesIO
import google.generativeai as genai
from typing import Dict, Any
import json

class ImageAnalysisAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def _prepare_image(self, image_input) -> Image.Image:
        if isinstance(image_input, str):
            return Image.open(image_input)
        elif isinstance(image_input, bytes):
            return Image.open(BytesIO(image_input))
        elif isinstance(image_input, Image.Image):
            return image_input
        else:
            raise ValueError("Formato de imagem não suportado")
    
    def analyze(self, image_input, criteria: str = "Avaliação geral de qualidade visual") -> Dict[str, Any]:
        try:
            image = self._prepare_image(image_input)
            
            prompt = f"""
            Você é um jurado especialista em análise visual. Analise esta imagem com base nos seguintes critérios:
            CRITÉRIOS DE AVALIAÇÃO: {criteria}
            
            Por favor, forneça uma análise detalhada considerando composição, qualidade técnica, criatividade e impacto visual.
            
            Retorne sua análise em formato JSON com:
            - pontuacao: (A nota numérica que você deu)
            - pontuacao_maxima: (O valor máximo da escala que você utilizou. Se os critérios pediram uma escala de 0-25, este valor deve ser 25. Se não, o padrão é 100.)
            - feedback: análise detalhada
            - elementos_visuais: lista dos elementos principais identificados
            - qualidade_tecnica: avaliação técnica
            - criatividade: avaliação da criatividade
            - pontos_fortes: lista de pontos positivos
            - pontos_melhoria: lista de sugestões de melhoria
            - veredicto: resumo da avaliação
            """
            
            response = self.model.generate_content([prompt, image])
            result = response.text
            
            try:
                start_idx = result.find('{')
                end_idx = result.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_content = result[start_idx:end_idx]
                    analysis = json.loads(json_content)
                else:
                    analysis = {"pontuacao": 0, "feedback": result}
            except json.JSONDecodeError:
                analysis = {"pontuacao": 0, "feedback": result}
            
            analysis["tipo"] = "imagem"
            analysis["agente"] = "ImageAnalysisAgent"
            
            return analysis
            
        except Exception as e:
            return {"erro": str(e), "pontuacao": 0, "tipo": "imagem", "agente": "ImageAnalysisAgent"}