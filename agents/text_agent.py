import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from typing import Dict, Any
import json
import PyPDF2

class TextAnalysisAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7,
            convert_system_message_to_human=True
        )
        
        self.prompt_template = PromptTemplate(
            input_variables=["text", "criteria"],
            template="""
            Você é um jurado especialista em análise textual. Analise o seguinte texto com base nos critérios fornecidos:
            TEXTO PARA ANÁLISE: {text}
            CRITÉRIOS DE AVALIAÇÃO: {criteria}
            Por favor, forneça uma análise detalhada retornando um JSON com:
            - pontuacao: (A nota numérica que você deu)
            - pontuacao_maxima: (O valor máximo da escala que você utilizou. Se os critérios pediram uma escala de 0-25, este valor deve ser 25. Se não, o padrão é 100.)
            - feedback: análise detalhada
            - pontos_fortes: lista de pontos positivos
            - pontos_melhoria: lista de sugestões de melhoria
            - veredicto: resumo da avaliação
            """
        )
        
        self.chain = self.prompt_template | self.llm
    
    def analyze(self, text: str, criteria: str = "Avaliação geral de qualidade") -> Dict[str, Any]:
        try:
            result = self.chain.invoke({"text": text, "criteria": criteria})
            content = result.content if hasattr(result, 'content') else str(result)
            
            try:
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx != -1 and end_idx != 0:
                    json_content = content[start_idx:end_idx]
                    analysis = json.loads(json_content)
                else:
                    analysis = {"pontuacao": 0, "feedback": content, "pontos_fortes": [], "pontos_melhoria": [], "veredicto": "Não foi possível extrair o JSON."}
            except json.JSONDecodeError:
                analysis = {"pontuacao": 0, "feedback": content, "pontos_fortes": [], "pontos_melhoria": [], "veredicto": "Erro ao decodificar o JSON."}
            
            analysis["tipo"] = "texto"
            analysis["agente"] = "TextAnalysisAgent"
            
            return analysis
            
        except Exception as e:
            return {"erro": str(e), "pontuacao": 0, "feedback": f"Erro na análise: {str(e)}", "tipo": "texto", "agente": "TextAnalysisAgent"}

    def analyze_document(self, file_path: str, criteria: str) -> Dict[str, Any]:
        try:
            _, extension = os.path.splitext(file_path)
            
            extracted_text = ""
            if extension.lower() == '.pdf':
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    if reader.is_encrypted:
                        return {"erro": "O arquivo PDF está criptografado e não pode ser lido."}
                    for page in reader.pages:
                        extracted_text += page.extract_text() or ""
            else:
                return {"erro": f"Tipo de documento '{extension}' não suportado."}

            if not extracted_text.strip():
                return {"erro": "Nenhum texto pôde ser extraído do documento."}
            
            return self.analyze(extracted_text, criteria)

        except Exception as e:
            return {"erro": f"Erro ao processar o documento: {str(e)}"}