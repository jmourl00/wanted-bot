from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from Modelo.parser import Parser
from selenium import webdriver

from Modelo.requester import Requester
from httpcore import ProxyError
from asyncio import subprocess
from httpx import ReadTimeout
from bs4 import BeautifulSoup
from Modelo.item import Item
from typing import List

import subprocess
import requests
import time
import sys

class WantedAPI:

    def __init__(self, locale: str = "www.vinted.es", type_search: str = "API", proxy: str = None, email: str =  None, password: str =  None):
        self.api_endpoint = f"http://www.vinted.es/api/v2/catalog/items" 
        self.base_url = f"{locale}" #self.base_url = f"https://{locale}"
        self.locale = locale
        self.search_number = 0
        self.proxy = proxy 
        self.email = email
        self.password = password
        self.chromedriver_path = None
        self.service = None


        if type_search == "API":
            self.client = Requester(self.locale)
        else:
            
            # Instanciamos el driver
            self.driver = None
            
            # "nul" solo existe en Windows, usa "/dev/null" en Linux
            log_path = "nul" if sys.platform == "win32" else "/dev/null"

            # Determinar flags de creación (solo en Windows)
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

            # Crear el servicio correctamente
            self.service = Service(executable_path=self.chromedriver_path, log_path=log_path)

            # Si deseas aplicar los flags de creación (solo relevante en Windows)
            if sys.platform == "win32":
                self.service.creationflags = creationflags

            self.configure_selenium(proxy)


    # <-> Configuracion de parametros para la busqueda de Selenium, mejora de rendimiento y errores
    #

    def configure_selenium(self, proxy: str = None):

        self.options = Options()
        self.options.add_argument("--headless=new")
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        #self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        #self.options.add_experimental_option('useAutomationExtension', False)
        #self.options.add_argument("--use-gl=swiftshader")
        self.options.add_argument("--enable-unsafe-swiftshader")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--disable-software-rasterizer")
        self.options.add_argument("--disable-webgl")

        self.options.add_argument("--log-level=3")
        #self.options.add_experimental_option('excludeSwitches', ['enable-logging'])

        print(f"[API] Proxy: {proxy}")
        if proxy:
            self.options.add_argument(f'--proxy-server={proxy}')

        if self.email:
            self.options.add_experimental_option('excludeSwitches', ['enable-logging'])


    # <-> Busca artículos usando la API de Vinted
    #     Devuelve una lista de objetos Item que contienen la información de los artículos.

    def search_items_api(self, search_text: str, page: int = 1, per_page: int = 20, proxy: str = None) -> List[Item]:

        #start_time = time.time()

        # FALTA, SI RECIBO UNA URL, EXTRAER PARAMETROS Y CREAR UNA REQUEST EN CONDICIONES, AÑADIR PARAMETROS SEGUN LA URL A LOS PARAMS
        params = {
            "search_text": "poster",
            "page": page,
            "per_page": per_page,
            "order": "newest_first",
        }

        try:
            # Actualizamos el proxy del cliente si se proporciona
            if self.proxy:
                proxies = {
                    "http": self.proxy,
                    "https": self.proxy
                }
                self.client.set_proxy(proxies=proxies)
            elif proxy:
                print("[API] El proxy elegido es:", proxy)
                proxies = {
                    "http": proxy,
                    "https": proxy
                }
                self.client.set_proxy(proxies=proxies)
            # Realizamos la solicitud a la API
            response = self.client.get(self.api_endpoint, params=params)

            #print(f"[API] Request URL: {response.url}")
            #print(f"[API] Response text: {response.text[:50000]}")

            if not response:
                print("[ERROR] No response received.")
                return []

            if "Enable JavaScript and cookies" in response.text:
                print("[ERROR] Cloudflare block detected.")
                return []
            
            if response.status_code != 200:
                print(f"[API] Error en la API: {response.status_code if response else 'No response'}")
                return []

            try:
                data = response.json()
                # Procesar data["items"] y convertir a objetos Item
            except Exception as e:
                print(f"[ERROR] Could not parse response as JSON: {e}")
                return []

        except ReadTimeout:
            print(f"[API] Timeout al acceder a {self.api_endpoint} con proxy: {proxy}")
            return []
        except ProxyError:
            print(f"[API] Error con el proxy: {proxy}")
            return []
        except requests.RequestException as e:
            print(f"[API] Error inesperado: {e}")
            return []
        except Exception as e:
            print(f"[API] Error desconocido: {e}")
            return []
    
        # Procesamos los items de la respuesta
        items = self.format_items_api(data, items=[])

        if len(items) > 0:
            self.search_number += 1

        #duration = time.time() - start_time
        #print(f"[API] search_items_vinted_api duró {duration:.2f} segundos")

        return items


    # <-> Devuelve los items procesados de la búsqueda HTML

    def format_items_api(self, data, items= []) -> List[Item]:
        for entry in data.get("items", []):
            items.append(Item(
                id=str(entry.get("id")),
                title=entry.get("title", ""),
                price=str(entry.get("price", {}).get("amount", "")),
                brand_title=entry.get("brand", {}).get("title", ""),
                photo=entry.get("photo", {}).get("url", ""),
                url=f"https://www.vinted.es/items/{entry.get('id')}",
                raw_timestamp=entry.get("created_at_ts", 0)
            ))
        return items


    # <-> FALTA COMPLETAR Obtiene los parámetros de la URL y los devuelve en un diccionario

    def url_to_params(self, url: str) -> dict:
        params = {}
        return params


    # <-> Busca artículos scrapeando la página HTML de Vinted, Wallapop, Ebay o Milanuncios
    #     Devuelve una lista de objetos Item que contienen la información de los artículos.

    def search_items_html(self, search_url: str, page: int = 1, proxy: str = None, typeApp: str = None) -> List[Item]:

        start_time = time.time()

        # Inicializar el driver de Selenium
        if self.driver is None:
            self.driver = webdriver.Chrome(service=self.service, options=self.options)
        
        #self.driver = uc.Chrome(service=self.service, options=self.options)
        # Elemento de espera para que la página cargue completamente
        self.wait = WebDriverWait(self.driver, 20)

        try:

            print(f"[API] Cargando página: {search_url}")
            # Obtener la página de búsqueda
            self.driver.get(search_url)

            # Esperar que carguen los items
            if typeApp == "vinted":
                self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.feed-grid__item")))
            elif typeApp == "wallapop":
                self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[class*='item-card_ItemCard--vertical']")))
            elif typeApp == "ebay":
                self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.srp-results > li.s-card")))
            elif typeApp == "milanuncios":
                #self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.ma-AdList > article.ma-AdCardV2")))
                #self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article")))

                #self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ma-AdList")))
                # Esperar hasta que los artículos individuales estén cargados
                #self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.ma-AdCardV2")))
                
                #self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='AD_LIST']")))
                try:
                    self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.ma-AdCardV2")))
                except Exception:
                    # Intentar de nuevo con selectores alternativos (por si cambia el DOM)
                    try:
                        self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article[class*='ma-AdCardV2']")))
                    except Exception:
                        print("[API] ⚠️ No se encontraron artículos de Milanuncios en el tiempo esperado.")
                        # Capturar HTML de depuración
                        html = self.driver.page_source
                        with open("milanuncios_debug.html", "w", encoding="utf-8") as f:
                            f.write(html)
                        raise

            # Extrae el contenido de la página obtenida
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

        except Exception as e:
            print(f"[API] Error al cargar la página: {type(e).__name__}: {e}")
            self.driver.quit()
            self.driver = None
            return []

        #self.driver.quit()

        try:
            # Procesar los items de la página HTML, se puede limitar el número de items procesados
            if typeApp == "vinted":
                items = Parser.parse_items_vinted_html(soup, items=[])
            elif typeApp == "wallapop":
                items = Parser.parse_items_wallapop_html(soup, items=[])
            elif typeApp == "ebay":
                items = Parser.parse_items_ebay_html(soup, items=[])
            elif typeApp == "milanuncios":
                items = Parser.parse_items_milanuncios_html(soup, items=[])

        except Exception as e:
            print(f"[API] Error el el parseo del html: {type(e).__name__}: {e}")
            self.driver.quit()
            self.driver = None
            return []

        # Esto es ambiguo, ya que puede no haber items pero la búsqueda fue exitosa
        if len(items) > 0:
            self.search_number += 1

        duration = time.time() - start_time
        print(f"[API] search_items_api duró {duration:.2f} segundos")
        return items