# Usa uma imagem Python oficial.
FROM python:3.10-slim

# Define o diretório de trabalho no container.
WORKDIR /app

# ---- ADICIONE ESTA LINHA ----
# Adiciona o diretório de trabalho ao PYTHONPATH para resolver importações.
ENV PYTHONPATH="${PYTHONPATH}:/app"
# ---- FIM DA MUDANÇA ----

# Copia o arquivo de dependências e instala as dependências.
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código da aplicação para o diretório de trabalho.
COPY . .

# Expõe a porta que o Uvicorn irá usar.
EXPOSE 8000

# Comando para rodar a aplicação quando o container iniciar.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]