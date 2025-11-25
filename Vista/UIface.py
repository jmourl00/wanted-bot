from datetime import datetime, timezone
import platform
import requests
import psutil
import sys
import os


def mostrar_menu(hilos_activos=[]):

    print("""\n 
       ..-+**************************+-..
     .+**********************************+.
    :+*************************************:
    =**************++*********+::**********=.
    +***********.     -*****+.  +**********+.
    +***********      :*****:  :***********+.
    +***********.     :****=   -***********+.
    +***********.     .****   .+***********+.
    +***********-     .+**:   -************+.
    +***********=      +*+.   *************+.
    +***********+.     =*-   -*************+.
    +************:     -+.  .+*************+.
    +************+     ..  .=***************.
    +*************:        =****************.
    +**************:    :+*****************+.
    :**************************************:
     .+**********************************+.
       .:=****************************=:.""")

    if hilos_activos:
        imprimirHilos(hilos_activos)

    print(
        f"\n--- Menú de opciones ---\n"
        f"1. Ver información del Programa y del Sistema\n"
        f"2. Cargar configuración\n"
        f"3. Iniciar\n"
        f"4. Finalizar un proceso\n"
        f"5. Salir\n"
    )
    return input("Seleccione una opción: ")


def imprimirHilos(hilos_activos):
    printed = "[ "
    first = True
    print("\n")

    for info in hilos_activos.values():
        hilo = info["thread"]
        if hilo.is_alive():
            if not first:
                printed += " | "
            printed += hilo.name
            first = False

    print("\n" + printed + " ]\n")

def imprimirArchivos(conf_files):
    for i, f in enumerate(conf_files, start=1):
        print(f"{i}.- {f}")
    print()

def imprimirDatos(items):

    for item in items:
        print(
            f"Nombre: {item.title}\n"
            f"id: {item.id}\n"
            f"Hora Item: {datetime.fromtimestamp(item.raw_timestamp, tz=timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')}\n"
            f"Precio: {item.price}\n"
            f"Marca: {item.brand_title}\n"
            f"Foto: {item.photo}\n"
            f"Link: {item.url}\n"
            f"Descripcion: {item.description}\n"
        )    


def borrarPantalla():
    if platform.system() == "Windows":
        os.system('cls')
    elif platform.system() == "Linux":
        os.system('clear')
    else:
        print("\nSistema no reconocido, comando no ejecutado...\n")


def checkParams(idle=True, hilos_activos=[]):

    if platform.system() not in ["Windows", "Linux"]:
        print(f"Sistema {platform.system()} no compatible, puede que el programa no funcione correctamente...\n")

    if(idle): print("\n")

    print(f"Sistema operativo: {platform.system()}"
          f"\nVersión: {platform.version()}"
          f"\nDetalles del sistema: {platform.platform()}"
          f"\nVersion de Python: {sys.version}"
          #f"\n\nUsuario actual: {os.getlogin()}"
          f"\nNombre de la máquina: {platform.node()}"
          f"\n\nDirectorio actual: {os.getcwd()}"
          f"\nIPv4 Pública: {requests.get('https://api4.ipify.org?format=text').text}"
          f"\n\nID del proceso actual: {os.getpid()}"
          f"\nID del proceso padre: {os.getppid()}"
          f"\nUso de memoria: {psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024):.2f} MB"
    )

    if(idle):
        print(
            f" ______________________________________________\n"
            f"|                                              |\n"
            f"|          Pulse INTRO para iniciar...         |\n"
            f"|______________________________________________|\n"
        )
        input()
    else:
        print(f"\nPulse INTRO para salir...\n")
        input()

    borrarPantalla()
    return


def endProgram():
    borrarPantalla()


def mostrar_error(mensaje):
    print(f"\n[ERROR] {mensaje}\n")


def mostrar_config(url, tags, notTags):
    print("\nConfiguración cargada con éxito:")
    print(f"URL: {url}")
    print(f"Tags: {tags}")
    print(f"Tags a ignorar: {notTags}")

def configuracionCargada(url, tags, notTags, timeUrlParams, proxy, search, typeApp, email, password):
    print("\nConfiguración cargada con éxito:")
    print(f"URL: {url if url else 'No definida'}")
    print(f"Tags: {tags}")
    print(f"Tags a ignorar: {notTags}")
    print(f"Parámetros de tiempo en URL: {timeUrlParams}")
    print(f"Proxy: {proxy if proxy else 'No definido'}")
    print(f"Término de búsqueda: {search if search else 'No definido'}")
    print(f"Tipo de aplicación: {typeApp if typeApp else 'No definido'}")
    print(f"Email: {email if email else 'No definido'}")
    print(f"Password: {'*' * len(password) if password else 'No definido'}")