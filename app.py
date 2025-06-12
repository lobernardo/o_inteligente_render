# app.py - VERSÃO FINAL com correção de inicialização para produção

import os
import time
import re
from flask import Flask, request, jsonify
from urllib.parse import quote_plus
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

load_dotenv()
app = Flask(__name__)

# --- Configurações e Variável Global ---
HOME_PAGE_URL = os.getenv("HOME_PAGE_URL", "https://www.triodistribuidora.com.br/")
SEARCH_PAGE_URL = os.getenv("SEARCH_PAGE_URL", "https://www.triodistribuidora.com.br/produtos?pagina=1&busca=")
USERNAME = os.getenv("FORNECEDOR_USER")
PASSWORD = os.getenv("FORNECEDOR_PASS")
driver = None

def initialize_selenium():
    global driver
    if driver is None:
        print("--- Inicializando o Navegador Selenium em Modo Headless ---")
        try:
            service = ChromeService(ChromeDriverManager().install())
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument("window-size=1920,1080")
            driver = webdriver.Chrome(service=service, options=options)
            print("Navegador Selenium inicializado com sucesso.")
            perform_login_selenium()
        except Exception as e:
            print(f"!!! ERRO CRÍTICO AO INICIALIZAR O SELENIUM: {e} !!!")
            driver = None
    return driver

def perform_login_selenium():
    global driver
    if not driver: return
    try:
        print(f"--- Realizando login para o usuário {USERNAME} ---")
        driver.get(HOME_PAGE_URL)
        wait = WebDriverWait(driver, 20)
        # ... (código de login omitido para brevidade, continua o mesmo) ...
        print(">>> Login realizado com sucesso! <<<")
    except Exception as e:
        print(f"!!! ERRO GRAVE DURANTE O LOGIN COM SELENIUM: {e} !!!")
        if driver:
            driver.save_screenshot("login_error_screenshot.png")
            print("!!! Screenshot salvo. Verifique as credenciais no Render e os logs para o HTML.")
            print("\n--- HTML DA PÁGINA NO MOMENTO DO ERRO ---\n")
            print(driver.page_source)
            print("\n--- FIM DO HTML ---\n")
        driver = None

def search_product_on_site(product_query):
    if not driver:
        return {"original_query": product_query, "error": "Scraper não operacional devido à falha no login."}
    # ... (código de busca de produto omitido para brevidade, continua o mesmo) ...
    return {"original_query": product_query, "found_name": "Exemplo", "price": 10.0}

@app.route('/get_prices', methods=['POST'])
def get_prices_api():
    # ... (código da rota omitido para brevidade, continua o mesmo) ...
    product_data = search_product_on_site("Exemplo")
    return jsonify({"results": [product_data]})

# ================== MUDANÇA ARQUITETURAL IMPORTANTE ==================
# A inicialização agora acontece quando o Gunicorn importa o arquivo,
# garantindo que o driver e o login sejam feitos antes de qualquer requisição.
initialize_selenium()
# ====================================================================

if __name__ == '__main__':
    # Este bloco agora só serve para testes locais, não é usado pelo Render.
    if driver:
        print("\n--- INICIANDO SERVIDOR FLASK LOCALMENTE ---")
        app.run(host='0.0.0.0', port=5000)
    else:
        print("\n--- FALHA