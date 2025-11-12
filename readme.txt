RECOMENDACIONES DE SEGURIDAD
  1. NO usar este programa con fines comerciales o con intenciones que vayan en contra de las politicas de las plataformas de comercio web.
  2. REVISAR EL CONTENIDO de el archivo .conf antes de ejecutar el programa
  3. Para más privacidad y seguridad, usar una VPN antes de ejecutar el programa, aunque puede afectar en el tiempo de respuesta...

Antes de ejecutar el programa, asegurarse de instalar todas las librerias del archivo requirements.txt con el
siguiente comando: py -m pip install -r requirements.txt

Luego introducir en la terminal: py main.py

## Estructura general

La aplicación sigue una "adaptación" del patrón **Modelo-Vista-Controlador (MVC)** para organizar el código y facilitar el mantenimiento.

---

## Clases principales

### 1. **Requester** (`Modelo/requester.py`)
- **Función:**  
  Gestiona las peticiones HTTP a la API de Vinted.  
  Inicializa una sesión con cabeceras adecuadas, maneja cookies y proporciona métodos para realizar peticiones GET y POST.
- **Complemento:**  
  Es utilizada por la clase `VintedAPI` para obtener datos de la web de Vinted de forma robusta y centralizada.

---

### 2. **wanted_api** (`Modelo/vinted_api.py`)
- **Función:**  
  Encapsula la lógica de acceso a la API de Vinted.  
  Permite buscar artículos usando URLs de búsqueda y devuelve objetos `Item` con los datos relevantes.
- **Complemento:**  
  Utiliza la clase `Requester` para realizar las peticiones HTTP y procesar las respuestas.  
  Es llamada desde el modelo de hilos para obtener los resultados de búsqueda.

---

### 3. **wanted** (`Controlador/wanted.py`)
- **Función:**  
  Es el controlador principal de la aplicación.  
  Gestiona la configuración, el menú de usuario, la coordinación de hilos y la interacción entre modelo y vista.
- **Complemento:**  
  Llama a los métodos del modelo (`threads`, `wanted_api`) y de la vista (`UIface`) según las acciones del usuario.

---

### 4. **UIface** (`Vista/UIface.py`)
- **Función:**  
  Encargada de toda la interacción con el usuario por terminal: mostrar menús, mensajes, errores y recibir entradas.
- **Complemento:**  
  Es llamada por el controlador para mostrar información y recibir opciones del usuario.

---

### 5. **Hilos de búsqueda** (`Modelo/threads.py`)
- **Función:**  
  Gestiona la ejecución de búsquedas en segundo plano mediante hilos para poder seguir utilizando el programa.
- **Complemento:**  
  Es lanzado por el controlador y utiliza el modelo y la vista para notificar resultados y errores.
  Llama a `VintedAPI` para obtener artículos y procesa los resultados según los filtros definidos.

---

## ¿Cómo se complementan?

- **El usuario** interactúa con la **vista** (`UIface`), que muestra menús y recibe opciones.

- El **controlador** (`VinFinderApp`) interpreta las acciones del usuario, recive los datos de los objetos ya adaptados y los envia a la vista.

- El **modelo** (`VintedAPI`, `Requester`, `threads`) realiza las búsquedas y gestiona los datos.

- Toda la interacción y presentación se realiza a través de la **vista**, manteniendo la separación de responsabilidades.

---

## Diagrama simplificado

```
Usuario <-> Vista (UIface) <-> Controlador (VinFinderApp) <-> Modelo (VintedAPI, Requester, threads)
```

---
