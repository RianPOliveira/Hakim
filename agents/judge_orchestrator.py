from typing import Dict, Any, List
import asyncio
from .text_agent import TextAnalysisAgent
from .image_agent import ImageAnalysisAgent
from .audio_agent import AudioAnalysisAgent
from .video_agent import VideoAnalysisAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
import json
import os

class JudgeOrchestrator:
    def __init__(self):
        self.text_agent = TextAnalysisAgent()
        self.image_agent = ImageAnalysisAgent()
        self.audio_agent = AudioAnalysisAgent()
        self.video_agent = VideoAnalysisAgent()
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3,
            convert_system_message_to_human=True
        )
        
        self.synthesis_template = PromptTemplate(
            input_variables=["analyses", "criteria"],
            template="""
            Você é o jurado principal que deve sintetizar as análises de múltiplos especialistas.
            ANÁLISES DOS ESPECIALISTAS (em formato JSON): {analyses}
            CRITÉRIOS GERAIS DE AVALIAÇÃO: {criteria}
            Com base nas análises individuais, forneça um veredicto final retornando um JSON com:
            - pontuacao_final: (Uma pontuação geral de 0 a 100, baseada na média ponderada das pontuações individuais)
            - veredicto_geral: Uma síntese de 2 a 3 frases sobre as submissões.
            - consenso_pontos_fortes: Uma lista de pontos fortes que apareceram em múltiplas análises.
            - areas_melhoria: Uma lista de sugestões de melhoria consolidadas.
            - recomendacao: Uma recomendação final (ex: "A proposta X é a mais promissora").
            """
        )
        self.synthesis_chain = self.synthesis_template | self.llm
    
    def detect_content_type(self, file_path: str) -> str:
        extension = os.path.splitext(file_path)[1].lower()
        if extension in ['.txt', '.md']: return 'text'
        if extension in ['.pdf']: return 'document'
        if extension in ['.jpg', '.jpeg', '.png', '.webp', '.gif']: return 'image'
        if extension in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']: return 'audio'
        if extension in ['.mp4', '.mov', '.avi', '.mkv']: return 'video'
        return 'unknown'
    
    async def analyze_single_content(self, content_input, content_type: str, criteria: str) -> Dict[str, Any]:
        try:
            if content_type == 'document':
                return self.text_agent.analyze_document(content_input, criteria)
            elif content_type == 'image':
                return self.image_agent.analyze(content_input, criteria)
            elif content_type == 'audio':
                return self.audio_agent.analyze(content_input, criteria)
            elif content_type == 'video':
                return self.video_agent.analyze(content_input, criteria)
            else:
                return {"erro": "Tipo de conteúdo não suportado"}
        except Exception as e:
            return {"erro": f"Erro na análise do agente: {str(e)}"}
    
    async def analyze_multiple_contents(self, contents: List[Dict], criteria: str) -> Dict[str, Any]:
        tasks = []
        for content_info in contents:
            path = content_info.get('path')
            content_type = self.detect_content_type(path)
            tasks.append(self.analyze_single_content(path, content_type, criteria))
        
        individual_results = await asyncio.gather(*tasks)
        
        for i, result in enumerate(individual_results):
            result['content_name'] = contents[i].get('name', f"Item {i+1}")
        
        synthesis_result = await self._synthesize_analyses(individual_results, criteria)
        
        return {
            "analises_individuais": individual_results,
            "sintese_final": synthesis_result
        }
    
    async def _synthesize_analyses(self, analyses: List[Dict], criteria: str) -> Dict[str, Any]:
        try:
            analyses_summary = []
            for analysis in analyses:
                summary_item = {
                    "content_name": analysis.get("content_name"),
                    "pontuacao": analysis.get("pontuacao"),
                    "pontuacao_maxima": analysis.get("pontuacao_maxima"),
                    "veredicto": analysis.get("veredicto")
                }
                analyses_summary.append(summary_item)

            analyses_text = json.dumps(analyses_summary, indent=2, ensure_ascii=False)
            
            result = self.synthesis_chain.invoke({"analyses": analyses_text, "criteria": criteria})
            content = result.content if hasattr(result, 'content') else str(result)
            
            try:
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    return json.loads(content[start_idx:end_idx])
                else:
                    return {"veredicto_geral": content}
            except json.JSONDecodeError:
                return {"veredicto_geral": content}
        except Exception as e:
            return {"erro": str(e)}