import os
from pydub import AudioSegment
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import Dict, Any
import json
import whisper

class AudioAnalysisAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7,
            convert_system_message_to_human=True
        )
        
        self.prompt_template = PromptTemplate(
            input_variables=["transcription", "criteria", "audio_info"],
            template="""
            Você é um jurado especialista em análise de áudio. Analise o seguinte conteúdo de áudio com base nos critérios fornecidos:
            
            TRANSCRIÇÃO DO ÁUDIO:
            {transcription}
            
            INFORMAÇÕES TÉCNICAS DO ÁUDIO:
            {audio_info}
            
            CRITÉRIOS DE AVALIAÇÃO:
            {criteria}
            
            Por favor, forneça uma análise detalhada considerando:
            1. Qualidade do conteúdo falado/musical
            2. Clareza e inteligibilidade
            3. Qualidade técnica do áudio
            4. Criatividade e originalidade
            5. Adequação aos critérios
            6. Aspectos de performance (se aplicável)
            
            Retorne sua análise em formato JSON com:
            - pontuacao: (0-100)
            - feedback: análise detalhada
            - qualidade_audio: avaliação técnica do áudio
            - conteudo: análise do conteúdo
            - performance: avaliação da performance
            - pontos_fortes: lista de pontos positivos
            - pontos_melhoria: lista de sugestões de melhoria
            - veredicto: resumo da avaliação
            """
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
    
    def _extract_audio_info(self, audio_path: str) -> Dict[str, Any]:
        try:
            audio = AudioSegment.from_file(audio_path)
            return {
                "duracao": len(audio) / 1000,  # em segundos
                "frame_rate": audio.frame_rate,
                "canais": audio.channels,
                "formato": audio_path.split('.')[-1],
                "tamanho_mb": os.path.getsize(audio_path) / (1024 * 1024)
            }
        except Exception as e:
            return {"erro": f"Erro ao extrair informações: {str(e)}"}
    
    def _transcribe_audio(self, audio_path: str) -> str:
        try:
            model = whisper.load_model("base")
            result = model.transcribe(audio_path, language="pt")
            
            transcription = result["text"]
            
            if not transcription.strip():
                 return "[Áudio não contém fala detectável]"

            return transcription
            
        except Exception as e:
            return f"[Erro na transcrição com Whisper: {str(e)}]"
    
    def analyze(self, audio_path: str, criteria: str = "Avaliação geral de qualidade de áudio") -> Dict[str, Any]:
        try:
            audio_info = self._extract_audio_info(audio_path)
            transcription = self._transcribe_audio(audio_path)
            
            result = self.chain.run(
                transcription=transcription,
                criteria=criteria,
                audio_info=json.dumps(audio_info, indent=2, ensure_ascii=False)
            )
            
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
                        "qualidade_audio": "Qualidade avaliada",
                        "conteudo": transcription[:200] + "..." if len(transcription) > 200 else transcription,
                        "performance": "Performance analisada",
                        "pontos_fortes": ["Áudio analisado"],
                        "pontos_melhoria": ["Verificar estrutura da resposta"],
                        "veredicto": "Análise concluída"
                    }
            except json.JSONDecodeError:
                analysis = {
                    "pontuacao": 70,
                    "feedback": result,
                    "qualidade_audio": "Avaliação técnica realizada",
                    "conteudo": transcription[:200] + "..." if len(transcription) > 200 else transcription,
                    "performance": "Performance avaliada",
                    "pontos_fortes": ["Conteúdo de áudio analisado"],
                    "pontos_melhoria": ["Melhorar formatação"],
                    "veredicto": "Análise realizada com formatação alternativa"
                }
            
            analysis["tipo"] = "audio"
            analysis["agente"] = "AudioAnalysisAgent"
            analysis["info_tecnica"] = audio_info
            analysis["transcricao"] = transcription
            
            return analysis
            
        except Exception as e:
            return {
                "erro": str(e),
                "pontuacao": 0,
                "feedback": f"Erro na análise do áudio: {str(e)}",
                "tipo": "audio",
                "agente": "AudioAnalysisAgent"
            }
    
    def analyze_music(self, audio_path: str) -> Dict[str, Any]:
        criteria = """
        Análise específica para conteúdo musical considerando:
        - Qualidade da composição, Harmonia e melodia, Ritmo e timing
        - Qualidade da gravação, Criatividade e originalidade, Técnica instrumental/vocal
        """
        return self.analyze(audio_path, criteria)
    
    def analyze_speech(self, audio_path: str) -> Dict[str, Any]:
        criteria = """
        Análise específica para fala e apresentação considerando:
        - Clareza da dicção, Fluência e ritmo da fala, Conteúdo da mensagem
        - Persuasão e engajamento, Qualidade técnica da gravação, Naturalidade da apresentação
        """
        return self.analyze(audio_path, criteria)