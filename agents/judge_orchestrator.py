from typing import Dict, Any, List
import asyncio
from .text_agent import TextAnalysisAgent
from .image_agent import ImageAnalysisAgent
from .audio_agent import AudioAnalysisAgent
from .video_agent import VideoAnalysisAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
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
            Você é o jurado principal que deve sintetizar as análises de múltiplos especialistas...
            ... (o resto do seu prompt continua igual)
            """
        )
        
        self.synthesis_chain = LLMChain(llm=self.llm, prompt=self.synthesis_template)
    
    # ... (O RESTO DO ARQUIVO CONTINUA EXATAMENTE IGUAL)
    # (nenhuma outra mudança é necessária neste arquivo)

    def detect_content_type(self, file_path: str) -> str:
        extension = file_path.lower().split('.')[-1]
        
        if extension in ['txt', 'md', 'docx', 'pdf']:
            return 'text'
        elif extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
            return 'image'
        elif extension in ['mp3', 'wav', 'ogg', 'flac', 'm4a']:
            return 'audio'
        elif extension in ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv']:
            return 'video'
        else:
            return 'unknown'
    
    async def analyze_single_content(self, content_input, content_type: str, criteria: str = "Avaliação geral") -> Dict[str, Any]:
        try:
            if content_type == 'text':
                if isinstance(content_input, str) and not os.path.exists(content_input):
                    text = content_input
                else:
                    with open(content_input, 'r', encoding='utf-8') as f:
                        text = f.read()
                return self.text_agent.analyze(text, criteria)
            
            elif content_type == 'image':
                return self.image_agent.analyze(content_input, criteria)
            
            elif content_type == 'audio':
                return self.audio_agent.analyze(content_input, criteria)
            
            elif content_type == 'video':
                return self.video_agent.analyze(content_input, criteria)
            
            else:
                return {
                    "erro": "Tipo de conteúdo não suportado", "tipo": content_type, "pontuacao": 0
                }
                
        except Exception as e:
            return {
                "erro": str(e), "tipo": content_type, "pontuacao": 0, "feedback": f"Erro na análise: {str(e)}"
            }
    
    async def analyze_multiple_contents(self, contents: List[Dict], criteria: str = "Avaliação comparativa") -> Dict[str, Any]:
        tasks = [
            self.analyze_single_content(
                content_info.get('path') or content_info.get('content'),
                content_info.get('type') or self.detect_content_type(str(content_info.get('path') or content_info.get('content'))),
                criteria
            )
            for content_info in contents
        ]
        
        individual_results = await asyncio.gather(*tasks)
        
        for i, result in enumerate(individual_results):
            result['item_id'] = i + 1
            result['content_name'] = contents[i].get('name', f"Item {i+1}")
        
        synthesis = await self._synthesize_analyses(individual_results, criteria)
        
        return {
            "analises_individuais": individual_results, "sintese_final": synthesis,
            "total_itens": len(individual_results), "criterios": criteria
        }
    
    async def _synthesize_analyses(self, analyses: List[Dict], criteria: str) -> Dict[str, Any]:
        try:
            analyses_text = []
            for analysis in analyses:
                text = f"""
                Item {analysis.get('item_id', '?')} - {analysis.get('content_name', 'Sem nome')}:
                Tipo: {analysis.get('tipo', 'unknown')}
                Pontuação: {analysis.get('pontuacao', 0)}
                Veredicto: {analysis.get('veredicto', 'N/A')}
                """
                analyses_text.append(text.strip())
            
            combined_analyses = "\n\n".join(analyses_text)
            
            result = self.synthesis_chain.run(
                analyses=combined_analyses,
                criteria=criteria
            )
            
            try:
                start_idx = result.find('{')
                end_idx = result.rfind('}') + 1
                
                if start_idx != -1 and end_idx != 0:
                    json_content = result[start_idx:end_idx]
                    synthesis = json.loads(json_content)
                else:
                    synthesis = {
                        "pontuacao_final": sum([a.get('pontuacao', 0) for a in analyses]) / len(analyses) if analyses else 0,
                        "veredicto_geral": result
                    }
            except json.JSONDecodeError:
                synthesis = {
                    "pontuacao_final": sum([a.get('pontuacao', 0) for a in analyses]) / len(analyses) if analyses else 0,
                    "veredicto_geral": result
                }
            
            return synthesis
            
        except Exception as e:
            return {"erro": str(e)}
    
    async def judge_competition(self, submissions: List[Dict], competition_criteria: str) -> Dict[str, Any]:
        analysis_result = await self.analyze_multiple_contents(submissions, competition_criteria)
        
        ranked_submissions = sorted(
            analysis_result["analises_individuais"], 
            key=lambda x: x.get('pontuacao', 0), 
            reverse=True
        )
        
        for i, submission in enumerate(ranked_submissions):
            submission['posicao'] = i + 1
            submission['medalha'] = self._get_medal(i + 1)
        
        return {
            "ranking": ranked_submissions,
            "sintese_competicao": analysis_result["sintese_final"],
            "criterios_competicao": competition_criteria,
            "total_participantes": len(submissions),
            "vencedor": ranked_submissions[0] if ranked_submissions else None
        }
    
    def _get_medal(self, position: int) -> str:
        if position == 1:
            return "🥇 Ouro"
        elif position == 2:
            return "🥈 Prata"
        elif position == 3:
            return "🥉 Bronze"
        else:
            return f"#{position}"
    
    def get_agent_status(self) -> Dict[str, Any]:
        return {
            "text_agent": "Ativo", "image_agent": "Ativo", "audio_agent": "Ativo",
            "video_agent": "Ativo", "orchestrator": "Ativo",
            "gemini_connection": "OK" if os.getenv("GOOGLE_API_KEY") else "API Key não configurada"
        }