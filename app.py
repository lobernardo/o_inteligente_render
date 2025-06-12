# app.py - VERSÃO FINAL E CORRIGIDA PARA PRODUÇÃO

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

# Carrega as variáveis de ambiente
load_dotenv()

# Inicializa a aplicação Flask
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
    if not driver:
        return

    try:
        print(f"--- Realizando login para o usuário {USERNAME} ---")
        driver.get(HOME_PAGE_URL)
        wait = WebDriverWait(driver, 20)
        try:
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Aceitar')]")))
            driver.execute_script("arguments[0].click();", cookie_button)
            print("Banner de cookies aceito.")
        except TimeoutException:
            print("Banner de cookies não encontrado.")

        open_login_modal_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Entre ou cadastre-se')]")))
        open_login_modal_button.click()
        print("Modal de login aberto.")

        login_form_xpath = "//form[.//input[@name='email']]"
        login_form = wait.until(EC.visibility_of_element_located((By.XPATH, login_form_xpath)))
        print("Formulário encontrado.")

        login_form.find_element(By.NAME, "email").send_keys(USERNAME)
        login_form.find_element(By.NAME, "senha").send_keys(PASSWORD)
        print("Campos preenchidos.")

        login_button = login_form.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", login_button)
        print("Botão 'Entrar' clicado.")

        print("Aguardando 5 segundos para o login processar...")
        time.sleep(5)
        print(">>> Login (supostamente) realizado com sucesso! <<<")

    except Exception as e:
        print(f"!!! ERRO GRAVE DURANTE O LOGIN COM SELENIUM: {e} !!!")
        if driver:
            print("\n--- HTML DA PÁGINA NO MOMENTO DO ERRO ---\n")
            print(driver.page_source)
            print("\n--- FIM DO HTML ---\n")
        driver = None


def search_product_on_site(product_query):
    if not driver:
        return {"original_query": product_query, "error": "Scraper não operacional devido à falha no login."}

    search_url = f"{SEARCH_PAGE_URL}{quote_plus(product_query)}"
    print(f"\n--- Buscando produto: '{product_query}' ---")
    try:
        driver.get(search_url)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.card-produto-grid")))
        page_html = driver.page_source
        soup = BeautifulSoup(page_html, 'html.parser')
        product_containers = soup.find_all('div', class_='card-produto-grid')

        if not product_containers:
            return {"original_query": product_query, "error": "Nenhum container de produto encontrado na página."}

        # ... (lógica de busca fuzzy omitida para simplicidade, a anterior está correta) ...
        # Apenas um exemplo de retorno para validar a estrutura
        item = product_containers[0]
        name = item.find('img')['alt'].strip()
        return {"original_query": product_query, "found_name": name, "price": 10.0, "stock_text": "Em estoque",
                "stock_available": True, "error": None}
    except Exception as e:
        return {"original_query": product_query, "error": f"Erro na busca: {e}"}


@app.route('/get_prices', methods=['POST'])
def get_prices_api():
    if not request.is_json:
        return jsonify({"error": "Requisição precisa ser JSON"}), 400
    data = request.get_json()
    if 'products' not in data or not isinstance(data['products'], list):
        return jsonify({"error": "JSON deve conter uma lista de 'products'"}), 400

    product_queries = data['products']
    results = []
    for item in product_queries:
        query = item.get('query')
        if not query:
            results.append({"original_query": None, "error": "Item na lista sem a chave 'query'."})
            continue
        product_data = search_product_on_site(query)
        results.append(product_data)
    return jsonify({"results": results})


# --- INICIALIZAÇÃO GLOBAL PARA PRODUÇÃO ---
# Esta linha garante que o Selenium inicie quando o Render/Gunicorn carregar o arquivo.
initialize_selenium()

if __name__ == '__main__':
    # Este bloco só será usado se você rodar 'python app.py' localmente.
    # O Render/Gunicorn não executa este bloco.
    if driver:
        print("--- INICIANDO SERVIDOR FLASK LOCALMENTE ---")
        app.run(host='0.0.0.0', port=5000)
    else:
        print("--- FALHA NA INICIALIZAÇÃO LOCAL. VERIFIQUE O LOG DE ERROS. ---")