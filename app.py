# app.py - VERSÃO FINAL com depuração de login no servidor

import os
import time
import re
from flask import Flask, request, jsonify
# ... (todas as outras importações continuam iguais)
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By

# ... etc

load_dotenv()
app = Flask(__name__)
# ... (configurações continuam iguais)
driver = None


def initialize_selenium():
    # (função sem mudanças)
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
        # (todo o processo de login que já funcionou antes continua aqui, sem mudanças)
        print(f"--- Realizando login para o usuário {USERNAME} ---")
        driver.get(HOME_PAGE_URL)
        wait = WebDriverWait(driver, 20)
        # ... (clicar em cookie, abrir modal, preencher campos, etc.)
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", login_button)
        print("Botão 'Entrar' clicado.")
        print("Assumindo que o login foi bem-sucedido. Aguardando 5 segundos...")
        time.sleep(5)
        print(">>> Login realizado com sucesso! <<<")
    except Exception as e:
        print(f"!!! ERRO GRAVE DURANTE O LOGIN COM SELENIUM: {e} !!!")
        if driver:
            driver.save_screenshot("login_error_screenshot.png")
            print("!!! Screenshot 'login_error_screenshot.png' salvo no disco do servidor.")

            # ================== NOVA LINHA DE DEBUG ==================
            # Imprime o código HTML da página no momento do erro para vermos no log.
            print("\n--- HTML DA PÁGINA NO MOMENTO DO ERRO ---\n")
            print(driver.page_source)
            print("\n--- FIM DO HTML ---\n")
            # ========================================================

        driver = None


# ... (O resto do arquivo, search_product_on_site, get_prices_api, etc., continua exatamente igual)
def search_product_on_site(product_query):
    if not driver:
        return {"original_query": product_query, "error": "Scraper não operacional devido à falha no login."}
    # ... resto da função
# ... (código omitido para brevidade, use a versão anterior completa)