#!/usr/bin/env bash
# exit on error
set -o errexit

# Instala todas as dependências do projeto
pip install --upgrade pip
pip install -r requirements.txt
