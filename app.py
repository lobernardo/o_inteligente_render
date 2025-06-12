# app.py - VERSÃO FINAL E PRODUÇÃO

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

# --- Configurações ---
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
        try:
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Aceitar')]")))
            driver.execute_script("arguments[0].click();", cookie_button)
            print("Banner de cookies aceito via JavaScript.")
        except TimeoutException:
            print("Banner de cookies não encontrado ou não foi necessário clicar.")
        open_login_modal_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Entre ou cadastre-se')]")))
        open_login_modal_button.click()
        print("Modal de login aberto.")
        print("Aguardando formulário e campos de login...")
        login_form_xpath = "//form[.//input[@name='email']]"
        login_form = wait.until(EC.visibility_of_element_located((By.XPATH, login_form_xpath)))
        print("Formulário de login encontrado com sucesso!")
        login_form.find_element(By.NAME, "email").send_keys(USERNAME)
        login_form.find_element(By.NAME, "senha").send_keys(PASSWORD)
        print("Campos de e-mail e senha preenchidos.")
        login_button = login_form.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", login_button)
        print("Botão 'Entrar' clicado.")
        print("Assumindo que o login foi bem-sucedido. Aguardando 5 segundos...")
        time.sleep(5)
        print(">>> Login realizado com sucesso! <<<")
    except Exception as e:
        print(f"!!! ERRO GRAVE DURANTE O LOGIN COM SELENIUM: {e} !!!")
        if driver:
            driver.save_screenshot("login_error_screenshot.png")
            print("!!! Screenshot 'login_error_screenshot.png' salvo.")
        driver = None


def search_product_on_site(product_query):
    if not driver:
        return {"original_query": product_query, "error": "Scraper não operacional devido à falha no login."}

    search_url = f"{SEARCH_PAGE_URL}{quote_plus(product_query)}"
    print(f"\n--- Buscando produto: '{product_query}' ---")

    try:
        SELETOR_CARD_PRODUTO = 'div.card-produto-grid'
        CLASSE_CARD_PRODUTO = 'card-produto-grid'

        driver.get(search_url)
        wait = WebDriverWait(driver, 15)
        # Espera Pacientemente pelo seletor correto
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELETOR_CARD_PRODUTO)))

        page_html = driver.page_source
        soup = BeautifulSoup(page_html, 'html.parser')

        product_containers = soup.find_all('div', class_=CLASSE_CARD_PRODUTO)

        if not product_containers:
            return {"original_query": product_query, "error": "Nenhum container de produto encontrado na página."}

        best_match_data = None
        highest_score = 0
        CONFIDENCE_THRESHOLD = 65  # Nível de confiança ajustado

        for item_soup in product_containers:
            found_name_element = item_soup.find('img', class_=re.compile(r'Produto_imagemProduto__\w+'))
            found_name = found_name_element['alt'].strip() if found_name_element else ""
            if not found_name: continue
            score = fuzz.ratio(product_query.lower(), found_name.lower())

            if score > highest_score:
                highest_score = score
                best_match_data = {"soup": item_soup, "name": found_name}

        if not best_match_data or highest_score < CONFIDENCE_THRESHOLD:
            error_msg = f"Nenhum resultado com confiança mínima de {CONFIDENCE_THRESHOLD}% encontrado."
            if best_match_data:
                error_msg += f" Melhor tentativa foi '{best_match_data['name']}' com pontuação {highest_score}."
            return {"original_query": product_query, "error": error_msg}

        item_soup = best_match_data["soup"]
        found_name = best_match_data["name"]
        price_span = item_soup.find('span', class_=re.compile(r'Produto_textoPrecos__\w+'))
        price_text = price_span.text.strip() if price_span else "0,00"
        price_value = 0.0
        try:
            cleaned_price = price_text.upper().replace("R$", "").replace(".", "").replace(",", ".").strip()
            price_value = float(cleaned_price)
        except (ValueError, AttributeError):
            price_value = 0.0
        stock_available = bool(item_soup.find('input', class_=re.compile(r'QuantidadeMaisMenos_input__\w+')))
        stock_text = "Em estoque" if stock_available else "Sem estoque"

        print(
            f">>> Produto encontrado: '{found_name}' (Pontuação: {highest_score}%) | Preço: R$ {price_value:.2f} | Estoque: {stock_text}")
        return {"original_query": product_query, "found_name": found_name, "price": price_value,
                "stock_text": stock_text, "stock_available": stock_available, "url_searched": search_url,
                "match_score": highest_score, "error": None}

    except Exception as e:
        print(f"!!! ERRO na busca por '{product_query}': {e}")
        driver.save_screenshot(f"search_error_{product_query[:20]}.png")
        return {"original_query": product_query, "error": f"Erro inesperado no Selenium: {e}"}


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


if __name__ == '__main__':
    initialize_selenium()
    if driver:
        print("\n--- INICIANDO API FLASK DE ORÇAMENTOS ---")
        print("API pronta para receber requisições na porta 5000.")
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    else:
        print("\n--- FALHA NA INICIALIZAÇÃO ---")
        print("Não foi possível iniciar a API Flask porque o Selenium/Login falhou ao inicializar.")