from Modelo.wanted_api import WantedAPI
from requests.auth import HTTPProxyAuth
from Vista.UIface import imprimirDatos
from datetime import datetime
from time import sleep

import concurrent
import threading
import requests
import telegram
import asyncio
import random
import time
import io

# Credenciales del BOT de Telegram
TELEGRAM_BOT_TOKEN = "7858665096:AAGPlaGpjN5ZfmFvjG0g6oyHaVWj_uFXKoA"
TELEGRAM_CHAT_ID = "843250757"
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)


#------------------------#
# METODOS DEL HILO PROXY #
#------------------------#


# <-> Obtiene un proxy funcional revisado de una lista de proxies
#     Si no hay proxies en la lista, busca proxies gratuitos y los prueba.

def get_working_proxy(proxies= [], blackList_proxies= [], test_url="https://www.vinted.es", stop_event=None, proxy_lock=None, sleep_time=10):

    good_proxies_finded = 0

    while not stop_event.is_set():
        total_Proxies = get_free_proxies(stop_event)
        random.shuffle(total_Proxies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(test_proxy, proxy, test_url, stop_event): proxy for proxy in total_Proxies if proxy not in blackList_proxies}
            for future in concurrent.futures.as_completed(futures):
                proxy_result = future.result()
                if proxy_result and proxy_result not in proxies and proxy_result not in blackList_proxies:
                    good_proxies_finded+= 1
                    proxies.append(proxy_result)
                    print(f"\n[PROXY] Proxy funcional encontrado: {proxy_result}")
                    print("[PROXY] Tamaño de lista de proxies funcionales: ", len(proxies))
                    print("[PROXY] Tamaño de blacklist: ", len(blackList_proxies))

        print("[PROXY] Ha finalizado la busqueda de proxies.")
        sleep(sleep_time)


# <-> Obtiene proxies de varios sitios web sin comprobar su funcionalidad

def get_free_proxies(stop_event=None):
    all_proxies = set()

    sources = {
        "proxyscrape.com": "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=elite",
        "FreeProxyList.net": "https://free-proxy-list.net/",
    }

    for name, url in sources.items():
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                lines = resp.text.strip().splitlines()
                for line in lines:
                    line = line.strip()
                    # Simple heurística: IP:PUERTO
                    if line and ":" in line and all(c.isdigit() or c == "." or c == ":" for c in line):
                        all_proxies.add(f"http://{line}")
                #print(f"[PROXY] {name}: {len(lines)} líneas leídas.")
            else:
                print(f"[PROXY] Error {resp.status_code} desde {name}")
        except Exception as e:
            print(f"[PROXY] Falló conexión a {name}: {e}")

    print(f"\n[PROXY] Total únicos recogidos: {len(all_proxies)}")
    return list(all_proxies)


# <-> Prueba un proxy para ver si es funcional
#     Si el proxy es funcional, lo devuelve, si no, devuelve False

def test_proxy(proxy, test_url="https://www.vinted.es", stop_event=None):

    thread_name = threading.current_thread().name
    # print(f"[PROXY] [{thread_name}] Probando proxy: {proxy}")
    if stop_event.is_set():
        return None
    try:
        if not proxy.startswith("http://") and not proxy.startswith("https://"):
            proxy = "http://" + proxy

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Connection": "keep-alive"
        }

        test_url = "https://www.vinted.es"

        # Soporte para proxies con auth
        if "@" in proxy:
            creds, ip_port = proxy.split("@")
            proxy_url = "http://" + ip_port
            user, pwd = creds.split(":")
            auth = HTTPProxyAuth(user, pwd)
        else:
            proxy_url = proxy if proxy.startswith("http") else "http://" + proxy
            auth = None

        response = requests.get(
            test_url,
            proxies={"http": proxy_url, "https": proxy_url},
            headers=headers,
            timeout=15,
            auth=auth
        )

        #print(f"[{thread_name}] Probando proxy: {proxy} - Status: {response.status_code}")

        if response.status_code == 200:
            return proxy
        else:
            #print(f"\n[{thread_name}] ❌ Proxy inválido ({response.status_code}): {proxy}")
            return False

    except requests.exceptions.ProxyError:
        return False
    except requests.exceptions.ConnectTimeout:
        return False
    except requests.exceptions.ReadTimeout:
        return False
    except requests.exceptions.RequestException:
        return False

# <-> Helper para ejecutar corutinas desde threads sin usar asyncio.run repetidamente
#     Evita que se cuelgue el hilo

def run_async_sync(coro, timeout=None):
    """Ejecuta una coroutine en un event loop nuevo (ideal para llamar desde threads)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout) if timeout else loop.run_until_complete(coro))
    finally:
        loop.close()

# <-> Envia un mensaje a Telegram

async def send_message(message):

    # Enviar la notificación a Telegram
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"{message}\n\n")

    #await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text= "Funciona" + "\n\n")
    print("Notificación enviada a través de Telegram.")

# <-> Envia una notificación a Telegram con los datos del item encontrado
#     Se debe tener configurado el bot de Telegram y el chat ID

async def send_notification(item):

    #filename = f'Hora_envio_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}'

    # Enviar la notificación a Telegram
    if item.photo:
        await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=item.photo, caption=f"{item.title}\n\n{item.url}")
    else:
    # Enviar solo el mensaje si no hay foto
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"{item.title}\n\n{item.url}")

    #await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text= "Funciona" + "\n\n")
    print("Notificación enviada a través de Telegram.")


# <-> Envia una notificación a Telegram con un grupo de Items
# --- send_notification_group mejorado ---
async def send_notification_group(items, max_retries=3):
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    media = []

    for item in items:
        if not getattr(item, "photo", None):
            print(f"[WARNING] Item sin foto: {item.title}")
            continue

        # Intentamos descargar la imagen localmente y pasar los bytes a Telegram (evita que Telegram tenga que
        # hacer fetch de la url y reduce problemas de timeout)
        try:
            r = requests.get(item.photo, timeout=15)
            if r.status_code != 200:
                print(f"[WARNING] Imagen inaccesible (status {r.status_code}): {item.photo}")
                continue

            image_bytes = io.BytesIO(r.content)
            image_bytes.name = "image.jpg"
            image_bytes.seek(0)
        except Exception as e:
            print(f"[WARNING] Error descargando imagen: {e}")
            continue

        caption = f"{item.title}\n{getattr(item, 'price', '')}\n{item.url}"

        # Creamos InputMedia con el objeto BytesIO (subida directa)
        media.append(
            telegram.InputMediaPhoto(
                media=image_bytes,
                caption=caption
            )
        )

    if not media:
        print("[INFO] No hay imágenes válidas. Nada que enviar.")
        return

    # Dividir en bloques de 10 (límite de Telegram)
    for i in range(0, len(media), 10):
        chunk = media[i:i+10]
        # reintentos con backoff en caso de timeout / error transitorio
        attempt = 0
        while attempt < max_retries:
            try:
                await bot.send_media_group(chat_id=TELEGRAM_CHAT_ID, media=chunk)
                break
            except telegram.error.TimedOut as e:
                attempt += 1
                wait = 2 ** attempt
                print(f"[WARNING] TimedOut al enviar grupo (intento {attempt}/{max_retries}). Reintentando en {wait}s...")
                await asyncio.sleep(wait)
            except telegram.error.TelegramError as e:
                # error irrecuperable de Telegram  loguear y salir del intento actual
                print(f"[ERROR] TelegramError al enviar media_group: {e}")
                break
        else:
            print("[ERROR] Agotados reintentos para este bloque. Continuando con el siguiente bloque.")

    print("Grupo enviado con éxito.")


#-------------------------#
# METODOS DEL HILO FINDER #
#-------------------------#


# <-> Comprueba si un item cumple con los criterios establecidos
#     y envía una notificación si es así.

def comprobarItem(itemcheck, timeWait, timeLimit, urls, noTags, tags):

    name = str(itemcheck.title).lower()
    #description = str(itemcheck.description).lower()
    resultado = (datetime.now().replace(microsecond=0) - datetime.fromtimestamp(itemcheck.raw_timestamp)).total_seconds()

    # Parametros para tener en cuenta el articulo
    if (resultado < timeLimit
    and itemcheck.url not in urls
    and any(word in name for word in tags)
    and not any(worde in name for worde in noTags)
    ):
        #asyncio.run(send_notification(itemcheck))
        urls.append(itemcheck.url)
        return True
    return False
    #sleep(timeWait)


# <-> Inicia la búsqueda de artículos 
#     Se encarga de buscar artículos y comprobar si cumplen con los criterios establecidos.

def startBusqueda(linkName, timeLimit=15, timeWait=5, urls=[], noTags=[], tags=[], proxyType=None, proxies=None, blacklist_proxies=None, stop_event=None, typeSearch="API", time_proxy_wait=5, typeApp=None, email=None, password=None):

    wanted = WantedAPI(linkName, typeSearch)
    print(f"TIPO DE PROXY: {proxyType}")
    proxy_golden_list = []

    if proxyType and proxyType != "AUTOMATIC":
        wanted = WantedAPI(linkName, typeSearch, proxy=proxyType, email=email, password=password)

    proxy = None
    while not stop_event.is_set():

        # Asignar un proxy si es necesario
        #if(proxyType == "AUTOMATIC" and proxy == None):
        #    while True:
        #        print(f"\n[SEARCH] Buscando proxy...")
        #        if proxies:
        #            proxy = proxies.pop(0)
        #            print(f"\n[SEARCH] Proxy Obtenido de la lista: {proxy}")
        #            break
        #        if not proxy:
        #            sleep(time_proxy_wait)
        
        # Busqueda de artículos y comprobación de items
        #wanted.search_number = 0
        #errors = 0
        
        #for i in range(50):

        timer = time.time()
        if typeSearch == "API":
            print(f"\n[SEARCH] Buscando articulos en la API...")
            items = wanted.search_items_api()
        else:
            print(f"\n[SEARCH] Buscando articulos en el HTML...")
            items = wanted.search_items_html()

        #if len(items) == 0:
        #    errors += 1
        #    if errors >= 6:
        #        blacklist_proxies.append(proxy)
        #        print("[THREAD] No se encontraron artículos, cambiando de proxy...")
        #        break
        #else:
        #errors = 0

        print(f"[SEARCH] Artículos encontrados: {len(items)}")
        imprimirDatos(items)

        #for itemcheck in items:
            #if(!comprobarItem(item, timeWait, timeLimit, urls, noTags, tags)) 

        # Obtenemos una lista con los Items que cumplen los parametros
        items_filtrados = [item for item in items if comprobarItem(item, timeWait, timeLimit, urls, noTags, tags)]

        # Enviamos la notificación con los Items que cumplen los parámetros
        if items_filtrados:
            # Ejecutar la coroutine desde el thread de manera segura
            run_async_sync(send_notification_group(items_filtrados), timeout=120)

        duration = time.time() - timer
        print(f"[SEARCH] Iteracion duró {duration:.2f} segundos")
        
        # Dependiendo del tiempo que haya durado la iteración, esperar lo necesario
        if duration < timeWait:
            time.sleep(timeWait - duration)


#----------------------#
# INICIADORES DE HILOS #
#----------------------#


# ---> Hilo de búsqueda de artículos
#       Este hilo se encarga de buscar artículos en Vinted y comprobar si cumplen con los criterios establecidos.

def searchThread(params, tags, notTags, proxy, hilos_activos, proxies=None, blacklist_proxies=None, proxy_lock=None, thread_limit=3, search="API", typeApp=None, email=None, password=None):

    if hilos_activos >= thread_limit:
        print("\nLimite de hilos alcanzado, volviendo...\n")
        sleep(1)
        return None

    stop_event = threading.Event()
    hilo = threading.Thread(
        name="hilo_search -" + str(hilos_activos) + "-",
        target=startBusqueda,
        args=(params[2], params[0], params[1], [], notTags, tags, proxy, proxies, blacklist_proxies, stop_event, search, 5, typeApp, email, password)
    )
    hilo.start()

    return hilo, stop_event


# ---> Hilo de búsqueda de proxies
#       Este hilo se encarga de buscar proxies funcionales y añadirlos a la lista de proxies.

def proxyfinder(proxies=[], blacklist_proxies=[], linkName="https://www.vinted.es", proxy_lock=None):

    stop_event = threading.Event()
    hilo = threading.Thread(
        name="hilo_proxy",
        target=get_working_proxy,
        args=(proxies, blacklist_proxies, linkName, stop_event, proxy_lock)
    )
    hilo.start()

    return hilo, stop_event


# ---> Monitor de hilos activos
#       Este hilo se encarga de monitorizar los hilos activos y eliminar los que ya no están vivos.

def monitor(hilos_activos, check_interval=3):
    while True:
        hilos_a_eliminar = []

        for nombre, info in list(hilos_activos.items()):
            hilo = info["thread"]

            if not hilo.is_alive():
                mensaje = f"⚠️ ALERTA: {nombre} ha dejado de funcionar."
                print(mensaje)
                run_async_sync(send_message(mensaje))

                if info.get("relaunch"):
                    print(f"🔄 Reiniciando hilo {nombre}...")

                    # función creadora
                    creator = info["creator"]
                    # parámetros originales
                    args = info["args"]

                    # recrear hilo
                    new_thread, new_stop_event = creator(*args)

                    # actualizar registro
                    hilos_activos[nombre] = {
                        "thread": new_thread,
                        "stop": new_stop_event,
                        "relaunch": True,
                        "creator": creator,
                        "args": args,
                    }

                else:
                    hilos_a_eliminar.append(nombre)

        for nombre in hilos_a_eliminar:
            del hilos_activos[nombre]

        sleep(check_interval)