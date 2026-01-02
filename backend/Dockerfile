FROM python:3.10-slim

WORKDIR /app

# --- CORREÇÃO AQUI ---
# 'libgl1-mesa-glx' foi trocado por 'libgl1' que é a versão moderna
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
# ---------------------

# Configura o caminho para imports absolutos funcionarem
ENV PYTHONPATH="/app"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]