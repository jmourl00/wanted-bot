from time import sleep

import Modelo.threads as threads
import Vista.UIface as UIface
import threading
import os
import re

class Wanted:

    def __init__(self):

        self.restartComponents()
        self.hilos_activos = {}
        self.blacklist_proxies = []
        self.proxy_lock = threading.Lock() 
        self.thread_limit = 30

    
    def restartComponents(self):
        self.url = None
        self.tags = []
        self.notTags = []
        self.timeUrlParams = []
        self.proxy = None
        self.proxies = []
        self.search = "HTML"
        self.typeApp = None
        self.email = None
        self.password = None

    # <-> Carga la configuración del archivo conf.txt que tiene que estar en la misma carpeta que el script

    def loadConf(self):

        # Buscar si existe algún archivo con "conf" en el nombre en el directorio actual
        if not any("conf" in f for f in os.listdir(".")):
            UIface.mostrar_error("No se pudo cargar la configuración."
                                 f"\nNo se encontró ningún archivo de" 
                                 f"configuración que contenga 'conf' "
                                 f"en el nombre.\n Si no existe, crea "
                                 f"un archivo 'conf.txt' en la misma "
                                 f"carpeta donde ejecutaste el script.\n")
            sleep(3)
            return
        
        conf_files = [f for f in os.listdir(".") if "conf" in f]
        print("\nSe han encontrado estos archivos de configuración:\n")
        UIface.imprimirArchivos(conf_files)

        # Pedir al usuario que introduzca el numero correspondiente al archivo que quiere usar
        while True:
            user_input = input("Introduce el numero del archivo que quieres usar (Enter para salir): ").strip()
            
            if user_input == "":
                UIface.mostrar_error("No se seleccionó ningún archivo. Saliendo...")
                sleep(1)
                return
            
            if user_input.isdigit():
                index = int(user_input) - 1
                if 0 <= index < len(conf_files):
                    user_input = conf_files[index]
                    print(f"Has seleccionado: {user_input}")
                    break
                else:
                    UIface.mostrar_error("Número fuera de rango. Intenta de nuevo.\n")
            else:
                UIface.mostrar_error("Entrada no válida. Introduce un número.\n")

        self.restartComponents()
        section = ""

        # Leemos el archivo línea por línea
        try:
            with open(user_input, "r", encoding="utf-8") as archivo:
                for linea in archivo:
                    linea = linea.strip()

                    # Detectar secciones
                    if linea.startswith("http"):
                        self.url = linea
                        for sitio in ["wallapop", "vinted", "ebay", "milanuncios"]:
                            if sitio in linea:
                                self.typeApp = sitio
                                break
                        continue
                    elif linea.startswith("Tags:"):
                        section = "tags"
                        continue
                    elif linea.startswith("No Tags:"):
                        section = "not_tags"
                        continue
                    elif linea.startswith("Time Params:"):
                        section = "time_params"
                        continue
                    elif linea.startswith("Proxy:"):
                        section = "proxy"
                        continue
                    elif linea.startswith("Search:"):
                        section = "search"
                        continue
                    elif linea.startswith("Login:"):
                        section = "login"
                        continue
                    elif linea.startswith("Use type:"):
                        section = "use_type"
                        continue

                    # Ignorar líneas vacías que no aportan contenido
                    if not linea:
                        continue

                    # Cargar contenido según la sección actual
                    if section == "tags":
                        self.tags.append(linea)
                    elif section == "not_tags":
                        self.notTags.append(linea)
                    elif section == "time_params":
                        numeros = re.findall(r'\d+', linea)
                        self.timeUrlParams.extend([int(n) for n in numeros])
                        if len(self.timeUrlParams) > 2:
                            self.timeUrlParams = self.timeUrlParams[:2]
                    elif section == "proxy":
                        self.proxy = linea.strip()
                    elif section == "search":
                        self.search = linea.strip()
                    elif section == "login":
                        self.email = linea.strip()
                        self.password = linea.strip()
                        
        except PermissionError:
            UIface.mostrar_error("Error: No tienes permisos para leer el archivo.")
        except UnicodeDecodeError:
            UIface.mostrar_error("Error: El archivo contiene caracteres no reconocidos.")
        except OSError as e:
            UIface.mostrar_error(f"Error inesperado al leer el archivo: {e}")

        if self.incompatibilidades() is False:
            return False

        UIface.configuracionCargada(self.url, self.tags, self.notTags, self.timeUrlParams, self.proxy, self.search, self.typeApp, self.email, self.password)
        sleep(1)


    # <-> Comprueba incompatibilidades en la configuración cargada, o funciones no soportadas

    def incompatibilidades(self):

        if self.typeApp not in ["wallapop", "vinted", "ebay", "milanuncios"]:
            UIface.mostrar_error("La URL no corresponde a un sitio soportado (wallapop, vinted, ebay, milanuncios).")
            sleep(2)
            return False
        
        if self.search not in ["HTML", "API"]:
            UIface.mostrar_error("El término de búsqueda debe ser 'HTML' o 'API'.")
            sleep(2)
            return False
        
        if self.search == "API" and self.typeApp not in ["wallapop", "milanuncios", "ebay"]:
            UIface.mostrar_error(f"La búsqueda por API no está soportada para {self.typeApp}.")
            sleep(2)

        if self.typeApp == "milanuncios" and (self.email is None or self.password is None):
            UIface.mostrar_error("Para búsquedas en Milanuncios es necesario proporcionar email y password para login.")
            sleep(2)
            return False

        return True

    # <-> Detiene todos los hilos
    #

    def stop_all_threads(self, join_timeout=5):

        if not self.hilos_activos:
            return

        print("[MAIN] Señalando a todos los hilos para que se detengan...")

        # Paso 1: indicar stop a todos los hilos
        for name, info in list(self.hilos_activos.items()):
            try:
                info["stop"].set()
            except Exception as e:
                print(f"[MAIN] Error al señalizar el hilo {name}: {e}")

        # Paso 2: esperar (join) a que terminen
        still_alive = {}
        for name, info in list(self.hilos_activos.items()):
            hilo = info["thread"]
            print(f"[MAIN] Esperando a que {name} termine...")
            hilo.join(timeout=join_timeout)

            if hilo.is_alive():
                print(f"[MAIN] ⚠️ El hilo {name} sigue activo.")
                still_alive[name] = info
            else:
                print(f"[MAIN] ✅ {name} detenido correctamente.")
                del self.hilos_activos[name]

        # Paso 3: si quedan vivos, esperar hasta que terminen
        if still_alive:
            print("[MAIN] Algunos hilos siguen activos. Esperando a que finalicen...")
            while still_alive:
                for name, info in list(still_alive.items()):
                    hilo = info["thread"]
                    if not hilo.is_alive():
                        print(f"[MAIN] ✅ {name} ha terminado.")
                        del still_alive[name]
                        if name in self.hilos_activos:
                            del self.hilos_activos[name]
                if still_alive:
                    print(f"[MAIN] Hilos aún activos: {', '.join(still_alive.keys())}. Esperando 1s...")
                    sleep(1)

        print("[MAIN] Todos los hilos detenidos correctamente.")




    # <-> Inicia la búsqueda de artículos
    #     Se encarga de iniciar el hilo de búsqueda, el hilo de búsqueda de proxies y el monitor de hilos,
    #     Además de gestionar el menú principal y las opciones del usuario

    def run(self):

        monitor_thread = threading.Thread(target=threads.monitor, daemon=True, args=(self.hilos_activos,))
        monitor_thread.start()

        UIface.checkParams()

        while True:
            #UIface.borrarPantalla()
            option = UIface.mostrar_menu(self.hilos_activos)

            if option == "1":
                UIface.borrarPantalla()
                UIface.checkParams(False)
            elif option == "2":
                if self.loadConf() is False:
                    UIface.mostrar_error("No se pudo cargar la configuración.")
            elif option == "3":
                if not self.url:
                    url_input = input("Introduce la URL de búsqueda (debe contener '?'): ").strip()
                    # Se puede mejorar
                    if not ("?" in url_input and ("http" in url_input or "https" in url_input)):
                        UIface.mostrar_error("La URL de búsqueda es incorrecta. Revisa la URL introducida.")
                        sleep(1)
                        continue
                    else:
                        self.url = url_input
                # Hilo de búsqueda
                hilo, stop_event = threads.searchThread(
                    [self.timeUrlParams[0], self.timeUrlParams[1], self.url],
                    self.tags,
                    self.notTags,
                    self.proxy,
                    len(self.hilos_activos),
                    self.proxies, 
                    self.blacklist_proxies,
                    self.proxy_lock,
                    self.thread_limit,
                    self.search,
                    self.typeApp,
                    self.email,
                    self.password
                )

                self.hilos_activos[hilo.name] = {"thread": hilo, "stop": stop_event}
                if(self.proxy == "AUTOMATIC"):
                    # Hilo de búsqueda de proxies
                    hilo_proxy, stop_event_proxy = threads.proxyfinder(self.proxies, 
                    self.blacklist_proxies,
                    self.proxy_lock)
                    self.hilos_activos[hilo_proxy.name] = {"thread": hilo_proxy, "stop": stop_event_proxy}

                self.restartComponents()

            elif option == "4":

                if self.hilos_activos == {}:
                    UIface.mostrar_error("No hay hilos activos para detener.")
                    sleep(1)
                    continue

                UIface.imprimirHilos(self.hilos_activos)
                nombre = input("Introduce el nombre del hilo a detener (por ejemplo, hilo_search -0-): ").strip()
                
                if nombre not in self.hilos_activos:
                    UIface.mostrar_error(f"No existe el hilo '{nombre}'.")
                    continue

                print(f"[SYS] Deteniendo {nombre}...")

                hilo_info = self.hilos_activos[nombre]
                hilo_info["stop"].set()
                hilo_info["thread"].join(timeout=5)

                if hilo_info["thread"].is_alive():
                    UIface.mostrar_error("[MAIN] ⚠️ El hilo no terminó a tiempo y sigue activo, reintentando 1 vez más...")
                    hilo_info["stop"].set()
                    hilo_info["thread"].join(timeout=15)

                    if hilo_info["thread"].is_alive():
                        UIface.mostrar_error("[MAIN] ❌ El hilo sigue activo después del segundo intento. Es posible que no se haya detenido correctamente.")
                        continue

                print(f"[SYS] {nombre} detenido.")
                del self.hilos_activos[nombre]

            elif option == "5":
                UIface.endProgram()

                self.stop_all_threads(join_timeout=5)
                print("[MAIN] Programa finalizado.")

                return
            
            else:
                UIface.mostrar_error("Opción no válida. Por favor, intente de nuevo.")
                sleep(1)
            #UIface.borrarPantalla()
            