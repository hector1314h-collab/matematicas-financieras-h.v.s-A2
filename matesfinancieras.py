"""
Autor: Héctor Velázquez  A2
v5      20/10/26
PROGRAMA: Consulta BANXICO + Inversión + Envío por correo
Este programa ofrece un menú interactivo en consola que permite:
1) Consultar el dato más reciente de cualquier serie del SIE de BANXICO.
2) Calcular el valor acumulado de una inversión (interés simple o compuesto).
3) Calcular el rendimiento de una inversión en CETES a 28 días usando
   la tasa actual publicada por BANXICO.
4) Enviar por correo (Gmail) el último resultado generado.
 
Requisitos:
- Librerías: requests, python-dotenv  (pip install requests python-dotenv)
- Un archivo .env con las variables:
    BANXICO_TOKEN   -> token personal de la API SIE de BANXICO
    CORREO_EMISOR   -> correo Gmail desde el que se envía
    CLAVE_CORREO    -> contraseña de aplicación de Gmail (16 caracteres)
"""
 
# IMPORTACIÓN DE LIBRERÍAS
 
import time                            # para pausar la ejecución (time.sleep)
import os                              # para leer variables de entorno
import requests                        # para consultar la API de BANXICO (HTTP)
import smtplib                         # para enviar correos mediante SMTP
from email.mime.text import MIMEText   # para armar el cuerpo del correo
from dotenv import load_dotenv         # para leer el archivo .env
 
# 1) CARGAR VARIABLES DE ENTORNO (.env)
 
RUTA_ENV = r"C:\Users\ALUMNO-F18\Documents\progra\.env"
load_dotenv(RUTA_ENV)  # carga las variables del archivo al entorno del programa
 
# Primero se leen las variables tal cual (si no existen, valen None)
BANXICO_TOKEN = os.getenv("BANXICO_TOKEN")
CORREO_EMISOR = os.getenv("CORREO_EMISOR")
CLAVE_CORREO = os.getenv("CLAVE_CORREO")
SERIE_CETES_28 = "SF43939"
 
# Luego se limpian, pero solo si existen 
if BANXICO_TOKEN is not None:
    BANXICO_TOKEN = BANXICO_TOKEN.strip()
if CORREO_EMISOR is not None:
    CORREO_EMISOR = CORREO_EMISOR.strip()
if CLAVE_CORREO is not None:
    CLAVE_CORREO = CLAVE_CORREO.replace(" ", "").strip()
 
# Aviso al iniciar si falta alguna variable (el programa sigue funcionando en lo que no dependa de ella)
if BANXICO_TOKEN is None or CORREO_EMISOR is None or CLAVE_CORREO is None:
    print("AVISO: no se encontraron todas las variables del archivo .env.")
    print("Revisa la ruta RUTA_ENV y que existan BANXICO_TOKEN, CORREO_EMISOR y CLAVE_CORREO.")
 
# 2) FUNCIÓN: ENVIAR CORREO
 
def enviar_correo(texto, destinatario=""):
    """
    Envía por correo (vía Gmail) el texto recibido.
 
    Parámetros:
        texto (str): contenido del correo; si es None no se envía nada.
        destinatario (str): correo destino; si viene vacío se le pide al usuario.
    """
    # Si no hay nada que enviar, avisamos y salimos
    if texto is None:
        print("Primero realiza una operación (opción 1, 2 o 3).")
        return
 
    # Sin correo emisor no se puede iniciar sesión en Gmail
    if CORREO_EMISOR is None or CLAVE_CORREO is None:
        print("Faltan CORREO_EMISOR o CLAVE_CORREO en el .env. No se puede enviar.")
        return
 
    # Si no nos dieron destinatario, se lo pedimos al usuario
    if destinatario == "":
        destinatario = input("¿A qué correo quieres enviar la información? ").strip()
 
    # Si sigue vacío, se cancela el envío
    if destinatario == "":
        print("No escribiste ningún correo. Se cancela el envío.")
        return
 
    # Armamos el correo: cuerpo + encabezados (asunto, remitente, destinatario)
    mensaje = MIMEText(texto)
    mensaje["Subject"] = "Información financiera"
    mensaje["From"] = CORREO_EMISOR
    mensaje["To"] = destinatario
 
    # Nos conectamos al servidor de Gmail y enviamos
    try:
        servidor = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)  # puerto 587 = TLS
        servidor.set_debuglevel(0)      # 0 = silencioso (pon 1 para ver la conversación)
        servidor.starttls()             # activa el cifrado de la conexión
        servidor.login(CORREO_EMISOR, CLAVE_CORREO)
        servidor.sendmail(CORREO_EMISOR, destinatario, mensaje.as_string())
        servidor.quit()                 # cierra la conexión
        time.sleep(3)
        print("Correo enviado correctamente.")
    except Exception as error:
        # Si algo falla se muestra el motivo
        time.sleep(3)
        print("No se pudo enviar el correo:", error)
 
# 3) FUNCIÓN: CONSULTAR TASA DE CETES A 28 DÍAS
 
def consultar_cetes():
    """
    Consulta la tasa de CETES a 28 días en tiempo real desde Banxico.
 
    Regresa:
        float -> tasa anual en porcentaje (ej. 7.25)
        None  -> si hubo cualquier error (token, red, servidor o formato)
    """
    # Sin token, BANXICO rechazaría la consulta, mejor avisamos desde aquí
    if BANXICO_TOKEN is None:
        print("No se encontró BANXICO_TOKEN en el .env.")
        return None
 
    # Se arma la URL con la serie de CETES; "oportuno" devuelve el dato más reciente
    url = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/" + SERIE_CETES_28 + "/datos/oportuno"
 
    # BANXICO pide el token en el encabezado (header) de la petición
    headers = {"Bmx-Token": BANXICO_TOKEN}
 
    try:
        print("\nConectando con Banxico para consultar CETES a 28 días...")
 
        # timeout=5 evita que el programa se quede esperando indefinidamente
        respuesta = requests.get(url, headers=headers, timeout=5)
 
        # Código 200 = la consulta fue exitosa
        if respuesta.status_code == 200:
            datos = respuesta.json()  # convierte la respuesta JSON a diccionario
 
            # Estructura de la respuesta: bmx -> series -> [0] -> datos -> [0]
            info_serie = datos["bmx"]["series"][0]["datos"][0]
            tasa_porcentaje = float(info_serie["dato"])  # el dato llega como texto
            fecha = info_serie["fecha"]
 
            print("Conexión exitosa con Banxico")
            print("CETES 28 días | Fecha: " + fecha + " | Tasa Anual: " + str(tasa_porcentaje) + "%")
            return tasa_porcentaje
        else:
            # Cualquier otro código (401, 404, 500...) indica un problema
            print("Error: El servidor de Banxico respondió con el estatus", respuesta.status_code)
            return None
 
    except requests.exceptions.RequestException as error:
        # Captura fallos de conexión
        print("Error de red o conectividad:", error)
        return None
    except (KeyError, IndexError, ValueError) as error:
        # Captura respuestas con formato inesperado o un dato que no es número
        print("Error al procesar los datos de la respuesta:", error)
        return None
 
# 4) FUNCIÓN: CALCULAR INVERSIÓN EN CETES (CON TASA ACTUAL)
 
def calcular_inversion_cetes():
    """
    Pide la cantidad a invertir, consulta la tasa de CETES, calcula la
    ganancia esperada, genera el reporte y ofrece enviarlo por correo.
 
    Regresa:
        str  -> el reporte (para poder reenviarlo con la opción 4)
        None -> si algo falló
    """
    print("\nCALCULAR INVERSIÓN CETES")
 
    # Se obtiene la tasa vigente; si falla, tasa_anual será None
    tasa_anual = consultar_cetes()
 
    if tasa_anual is None:
        print("No se pudo obtener la tasa de Banxico, por lo que no se puede calcular la inversión.")
        return None
 
    # Pedimos el capital; si escribe letras, float() lanza ValueError
    try:
        capital_inicial = float(input("¿Qué cantidad de dinero deseas invertir? (Ej. 10000): "))
    except ValueError:
        print("Error: Debes ingresar un valor numérico válido para la inversión.")
        return None
 
    # Validación: no tiene sentido invertir cero o una cantidad negativa
    if capital_inicial <= 0:
        print("La cantidad debe ser mayor a cero.")
        return None
 
    # Fórmula de interés simple con tasa anual proporcional al plazo:
    #   ganancia = capital * (tasa/100) * (días/365)
    # Se divide entre 100 porque la tasa viene en porcentaje, y
    # 28/365 convierte la tasa anual al plazo de 28 días.
    ganancia_estimada = capital_inicial * (tasa_anual / 100) * (28 / 365)
    monto_total = capital_inicial + ganancia_estimada
 
    # Se arma el reporte; "{:,.2f}".format(x) da miles con coma y 2 decimales
    reporte = "ANÁLISIS DE INVERSIÓN CETES 28 DÍAS\n"
    reporte = reporte + "Capital Invertido: $" + "{:,.2f}".format(capital_inicial) + " MXN\n"
    reporte = reporte + "Tasa Anual de Referencia (Banxico): " + str(tasa_anual) + "%\n"
    reporte = reporte + "Plazo: 28 días\n"
    reporte = reporte + "Ganancia Estimada: $" + "{:,.2f}".format(ganancia_estimada) + " MXN\n"
    reporte = reporte + "Monto Total al Vencimiento: $" + "{:,.2f}".format(monto_total) + " MXN\n"
 
    print("\n" + reporte)
    print("\nProcesando datos y aplicando delay...")
    time.sleep(2)  # pausa de 2 segundos
 
    # Se ofrece enviar el reporte por correo
    destino = input("Correo donde quieres recibir este análisis (Enter para omitir): ").strip()
    if destino != "":
        enviar_correo(reporte, destino)
    else:
        print("No ingresaste ningún correo. Se omite el envío.")
 
    return reporte
 
# 5) FUNCIÓN: CONSULTAR UNA SERIE DE BANXICO
 
def consultar_banxico():
    """
    Consulta el dato más reciente de cualquier serie del SIE de BANXICO.
 
    Regresa:
        str  -> texto con el resultado (se guarda para poder enviarlo por correo)
        None -> si la consulta falló
    """
    # Sin token, BANXICO rechazaría la consulta
    if BANXICO_TOKEN is None:
        print("No se encontró BANXICO_TOKEN en el .env.")
        return None
 
    # Pedir al usuario el id de la serie
    id_serie = input("Escribe el id de la serie de BANXICO (ej. SF43718): ")
    id_serie = id_serie.strip().upper()  # quita espacios y pasa a mayúsculas
 
    # Si no escribió nada, no tiene caso consultar
    if id_serie == "":
        print("No escribiste ningún id de serie.")
        return None
 
    # Armar la dirección (URL) de la consulta
    url = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/" + id_serie + "/datos/oportuno"
 
    # BANXICO pide el token en el encabezado (header)
    encabezados = {"Bmx-Token": BANXICO_TOKEN}
 
    # Hacer la petición; si falla la red, se avisa y se sale
    try:
        respuesta = requests.get(url, headers=encabezados, timeout=5)
    except requests.exceptions.RequestException as error:
        print("Error de red o conectividad:", error)
        return None
 
    # Si el código de estado no es 200, algo salió mal
    if respuesta.status_code != 200:
        print("Error en la consulta. Código:", respuesta.status_code)
        print("Mensaje de BANXICO:", respuesta.text)
        return None
 
    # Convertir la respuesta y sacar los datos; si el formato no es el esperado (serie inexistente, sin datos, etc.) se avisa y se sale
    try:
        datos = respuesta.json()
        serie = datos["bmx"]["series"][0]
        titulo = serie["titulo"]
        fecha = serie["datos"][0]["fecha"]
        valor = serie["datos"][0]["dato"]
    except (KeyError, IndexError, ValueError) as error:
        print("Error al procesar los datos de la respuesta:", error)
        return None
 
    # Armar un texto ya procesado, concatenando línea por línea
    texto = "CONSULTA BANXICO\n"
    texto = texto + "----------------\n"
    texto = texto + "Serie: " + id_serie + "\n"
    texto = texto + "Título: " + titulo + "\n"
    texto = texto + "Fecha: " + fecha + "\n"
    texto = texto + "Valor: " + valor + "\n"
 
    print()
    print(texto)
    time.sleep(3)  # pausa para que el usuario alcance a leer el resultado
    return texto
 
# 6) FUNCIÓN: CALCULAR VALOR ACUMULADO DE UNA INVERSIÓN
 
def calcular_inversion():
    """
    Calcula el valor acumulado de una inversión con interés simple o compuesto,
    con una tasa anual y un número de años que el usuario indica.
 
    Regresa:
        str  -> texto con el resultado
        None -> si algún dato no es válido
    """
    # Capital: debe ser un número mayor a cero
    try:
        capital = float(input("Capital inicial: "))
    except ValueError:
        print("Error: el capital debe ser un número.")
        return None
 
    if capital <= 0:
        print("El capital debe ser mayor a cero.")
        return None
 
    # Tipo de interés: solo se aceptan "1" o "2"
    print("Tipo de interés:")
    print("  1) Simple")
    print("  2) Compuesto")
    tipo = input("Elige 1 o 2: ").strip()
 
    if tipo != "1" and tipo != "2":
        print("Opción no válida.")
        return None
 
    # Tasa y años: la tasa puede tener decimales, los años deben ser enteros
    try:
        tasa = float(input("Tasa de interés anual (en %, ej. 8): "))
        anios = int(input("Número de años: "))
    except ValueError:
        print("Error: la tasa debe ser un número y los años un número entero.")
        return None
 
    if tasa < 0 or anios <= 0:
        print("La tasa no puede ser negativa y los años deben ser mayores a cero.")
        return None
 
    # Convertimos el porcentaje a decimal (8% -> 0.08)
    tasa_decimal = tasa / 100
 
    if tipo == "1":
        # Interés simple: M = C * (1 + i * n)
        # Los intereses se calculan siempre sobre el capital inicial.
        monto = capital * (1 + tasa_decimal * anios)
        nombre_tipo = "Simple"
    else:
        # Interés compuesto (tipo == "2"): M = C * (1 + i) ^ n
        # Los intereses se reinvierten y generan nuevos intereses cada año.
        monto = capital * (1 + tasa_decimal) ** anios
        nombre_tipo = "Compuesto"
 
    # Ganancia = lo que se obtiene menos lo que se invirtió
    ganancia = monto - capital
 
    # Armar el texto del resultado (round limita a 2 decimales)
    texto = "CÁLCULO DE INVERSIÓN\n"
    texto = texto + "--------------------\n"
    texto = texto + "Capital inicial: $" + str(round(capital, 2)) + "\n"
    texto = texto + "Tipo de interés: " + nombre_tipo + "\n"
    texto = texto + "Tasa anual: " + str(tasa) + "%\n"
    texto = texto + "Años: " + str(anios) + "\n"
    texto = texto + "Valor acumulado: $" + str(round(monto, 2)) + "\n"
    texto = texto + "Ganancia: $" + str(round(ganancia, 2)) + "\n"
 
    print()
    print(texto)
    return texto
 
# 7) MENÚ PRINCIPAL
# Guarda el texto del último resultado (opciones 1, 2 o 3) para que la opción 4 pueda enviarlo por correo. Empieza vacío (None).
ultimo_resultado = None
 
# Ciclo infinito: el menú se repite hasta que el usuario decida salir
while True:
    print()
    print("========== MENÚ ==========")
    print("1) Consultar serie de BANXICO")
    print("2) Calcular valor acumulado de una inversión")
    print("3) Calcular valor acumulado de una inversión con tasa actual de cetes")
    print("4) Enviar último resultado por correo")
    print("5) Salir")
    opcion = input("Elige una opción: ").strip()
 
    if opcion == "1":
        # Consulta una serie; solo si salió bien se guarda para enviarlo después
        resultado = consultar_banxico()
        if resultado is not None:
            ultimo_resultado = resultado
        respuesta_menu2 = input("¿Desea realizar alguna otra operación? s/n:").strip().lower()
        if respuesta_menu2 != "s":
            print("Finalizando ciclo...\n")
            break  # sale del while y termina el programa
    elif opcion == "2":
        # Calcula una inversión manual (simple/compuesto)
        resultado = calcular_inversion()
        if resultado is not None:
            ultimo_resultado = resultado
        respuesta_menu2 = input("¿Desea realizar alguna otra operación? s/n:").strip().lower()
        if respuesta_menu2 != "s":
            print("Finalizando ciclo...\n")
            break
    elif opcion == "3":
        # Consulta la tasa de CETES (dentro de la función) y calcula la inversión
        resultado = calcular_inversion_cetes()
        if resultado is not None:
            ultimo_resultado = resultado
        respuesta_menu2 = input("¿Desea realizar alguna otra operación? s/n:").strip().lower()
        if respuesta_menu2 != "s":
            print("Finalizando ciclo...\n")
            break
    elif opcion == "4":
        # Envía por correo lo último que se guardó en ultimo_resultado
        enviar_correo(ultimo_resultado)
        respuesta_menu2 = input("¿Desea realizar alguna otra operación? s/n:").strip().lower()
        if respuesta_menu2 != "s":
            print("Finalizando ciclo...\n")
            break
    elif opcion == "5":
        print("Hasta luego.")
        break
    else:
        # Cualquier otra entrada vuelve a mostrar el menú
        print("Opción no válida, intenta de nuevo.")