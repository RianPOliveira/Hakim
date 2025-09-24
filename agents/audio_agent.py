import os
from pydub import AudioSegment
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
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
            TRANSCRIÇÃO DO ÁUDIO: {transcription}
            INFORMAÇÕES TÉCNICAS DO ÁUDIO: {audio_info}
            CRITÉRIOS DE AVALIAÇÃO: {criteria}
            Por favor, forneça uma análise detalhada retornando um JSON com:
            - pontuacao: (A nota numérica que você deu)
            - pontuacao_maxima: (O valor máximo da escala que você utilizou. Se os critérios pediram uma escala de 0-25, este valor deve ser 25. Se não, o padrão é 100.)
            - feedback: análise detalhada
            - qualidade_audio: avaliação técnica do áudio
            - conteudo: análise do conteúdo
            - performance: avaliação da performance
            - pontos_fortes: lista de pontos positivos
            - pontos_melhoria: lista de sugestões de melhoria
            - veredicto: resumo da avaliação
            """
        )
        
        self.chain = self.prompt_template | self.llm
    
    def _extract_audio_info(self, audio_path: str) -> Dict[str, Any]:
        try:
            audio = AudioSegment.from_file(audio_path)
            return {
                "duracao": len(audio) / 1000,
                "frame_rate": audio.frame_rate,
                "canais": audio.channels,
                "formato": os.path.splitext(audio_path)[1],
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
            
            result = self.chain.invoke({
                "transcription": transcription,
                "criteria": criteria,
                "audio_info": json.dumps(audio_info, indent=2, ensure_ascii=False)
            })
            content = result.content if hasattr(result, 'content') else str(result)
            
            try:
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_content = content[start_idx:end_idx]
                    analysis = json.loads(json_content)
                else:
                    analysis = {"pontuacao": 0, "feedback": content}
            except json.JSONDecodeError:
                analysis = {"pontuacao": 0, "feedback": content}

            analysis["tipo"] = "audio"
            analysis["agente"] = "AudioAnalysisAgent"
            analysis["info_tecnica"] = audio_info
            analysis["transcricao"] = transcription
            
            return analysis
            
        except Exception as e:
            return {"erro": str(e), "pontuacao": 0, "tipo": "audio", "agente": "AudioAnalysisAgent"}