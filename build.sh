#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Instala o FFmpeg usando o gerenciador de pacotes do sistema
apt-get update && apt-get install -y ffmpeg

# 2. Instala as dependências do Python (seu comando original)
pip install -r requirements.txt
