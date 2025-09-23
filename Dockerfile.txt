# 1. Comece com uma imagem base oficial do Python
FROM python:3.11-slim

# 2. Instala o FFmpeg e outras ferramentas úteis para compilação
RUN apt-get update && apt-get install -y ffmpeg gcc && rm -rf /var/lib/apt/lists/*

# 3. Define o diretório de trabalho dentro do container
WORKDIR /app

# 4. Copia o arquivo de dependências e instala os pacotes Python
#    Isso aproveita o cache em builds futuros se o requirements não mudar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copia todo o resto do seu código para dentro do container
COPY . .

# 6. Expõe a porta que o Render vai usar para se comunicar com o container
EXPOSE 10000

# 7. Define o comando para iniciar sua aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
