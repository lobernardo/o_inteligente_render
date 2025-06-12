# Usa uma imagem base leve com Python
FROM python:3.11-slim

# Define variáveis de ambiente para evitar perguntas durante a instalação
ENV DEBIAN_FRONTEND=noninteractive

# Instala as dependências do sistema necessárias para o Selenium e Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    # Dependências para o Chrome
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Baixa e instala o Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Cria um diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de dependências do Python para o contêiner
COPY requirements.txt .

# Instala as bibliotecas do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do seu código para o contêiner
COPY . .

# Expõe a porta que a aplicação vai usar
EXPOSE 10000

# Comando final para iniciar o servidor Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "app:app"]