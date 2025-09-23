import os
import base64
from PIL import Image
from io import BytesIO
import google.generativeai as genai
from typing import Dict, Any
import json

class ImageAnalysisAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
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
            
            CRITÉRIOS DE AVALIAÇÃO:
            {criteria}
            
            Por favor, forneça uma análise detalhada considerando:
            1. Composição e enquadramento
            2. Qualidade técnica (nitidez, exposição, cores)
            3. Criatividade e originalidade
            4. Impacto visual e estético
            5. Adequação aos critérios específicos
            
            Retorne sua análise em formato JSON com:
            - pontuacao: (0-100)
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
                    analysis = {
                        "pontuacao": 75,
                        "feedback": result,
                        "elementos_visuais": ["Elementos identificados na imagem"],
                        "qualidade_tecnica": "Boa qualidade geral",
                        "criatividade": "Criatividade avaliada",
                        "pontos_fortes": ["Imagem analisada"],
                        "pontos_melhoria": ["Verificar estrutura da resposta"],
                        "veredicto": "Análise concluída"
                    }
            except json.JSONDecodeError:
                analysis = {
                    "pontuacao": 70,
                    "feedback": result,
                    "elementos_visuais": ["Análise visual realizada"],
                    "qualidade_tecnica": "Avaliação técnica concluída",
                    "criatividade": "Criatividade analisada",
                    "pontos_fortes": ["Conteúdo visual analisado"],
                    "pontos_melhoria": ["Melhorar formatação"],
                    "veredicto": "Análise realizada com formatação alternativa"
                }
            
            analysis["tipo"] = "imagem"
            analysis["agente"] = "ImageAnalysisAgent"
            
            return analysis
            
        except Exception as e:
            return {
                "erro": str(e),
                "pontuacao": 0,
                "feedback": f"Erro na análise da imagem: {str(e)}",
                "tipo": "imagem",
                "agente": "ImageAnalysisAgent"
            }
    
    def compare_images(self, images: list, criteria: str = "Comparação visual") -> list:
        results = []
        for i, image in enumerate(images):
            result = self.analyze(image, f"{criteria} - Imagem {i+1}")
            result["item_id"] = i + 1
            results.append(result)
        
        return results
    
    def analyze_composition(self, image_input) -> Dict[str, Any]:
        criteria = """
        Análise específica de composição fotográfica considerando:
        - Regra dos terços
        - Linhas de força
        - Simetria e equilíbrio
        - Profundidade de campo
        - Uso de luz e sombra
        - Cores e contraste
        """
        return self.analyze(image_input, criteria)