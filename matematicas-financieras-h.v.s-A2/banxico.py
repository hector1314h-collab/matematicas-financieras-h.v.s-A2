# ============================================================
# PROGRAMA: Consulta BANXICO + Inversión + Envío por correo
# ============================================================
import time
import os                      # para leer variables de entorno
import requests                # para consultar la API de BANXICO
import smtplib                 # para enviar correos
from email.mime.text import MIMEText   # para armar el correo
from dotenv import load_dotenv         # para leer el archivo .env

# 1) CARGAR VARIABLES DE ENTORNO (.env)
RUTA_ENV = r"C:\Users\User\OneDrive\Documents\Programación\.vscode\mates financieras\.env"
load_dotenv(RUTA_ENV)
BANXICO_TOKEN = os.getenv("BANXICO_TOKEN")       
CORREO_EMISOR = os.getenv("CORREO_EMISOR").strip()
CLAVE_CORREO = os.getenv("CLAVE_CORREO").replace(" ", "").strip()
SERIE_CETES_28 = "SF43939"

def consultar_cetes():
    """
    Consulta la tasa de CETES a 28 días en tiempo real desde Banxico.
    Comprueba conectividad, estatus HTTP y extrae el porcentaje de rendimiento.
    """
    url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{SERIE_CETES_28}/datos/oportuno"
    headers = {"Bmx-Token": BANXICO_TOKEN}

    try:
        print(f"\nConectando con Banxico para consultar CETES a 28 días...")
        respuesta = requests.get(url, headers=headers, timeout=5)
        
        if respuesta.status_code == 200:
            datos = respuesta.json()
            info_serie = datos['bmx']['series'][0]['datos'][0]
            tasa_porcentaje = float(info_serie['dato'])
            fecha = info_serie['fecha']
            
            print(f"Conexión exitosa con Banxico")
            print(f"CETES 28 días | Fecha: {fecha} | Tasa Anual: {tasa_porcentaje}%")
            return tasa_porcentaje
        else:
            print(f"Error: El servidor de Banxico respondió con el estatus {respuesta.status_code}")
            return None

    except requests.exceptions.RequestException as error:
        print(f"Error de red o conectividad: {error}")
        return None
    except (KeyError, IndexError, ValueError) as error:
        print(f"Error al procesar los datos de la respuesta: {error}")
        return None

def calcular_inversion_cetes():
    """
    Pide la cantidad a invertir, consulta la tasa de CETES, 
    calcula la ganancia esperada, genera el reporte, aplica delay y envía el email.
    """
    print("\nCALCULAR INVERSIÓN CETES")
    tasa_anual = consultar_cetes()

    if tasa_anual is not None:
        try:
            capital_inicial = float(input("¿Qué cantidad de dinero deseas invertir? (Ej. 10000): "))
            
            if capital_inicial <= 0:
                print("La cantidad debe ser mayor a cero.")
                return
            ganancia_estimada = capital_inicial * (tasa_anual / 100) * (28 / 365)
            monto_total = capital_inicial + ganancia_estimada

            reporte = (
                f"ANÁLISIS DE INVERSIÓN CETES 28 DÍAS\n"
                f"Capital Invertido: ${capital_inicial:,.2f} MXN\n"
                f"Tasa Anual de Referencia (Banxico): {tasa_anual}%\n"
                f"Plazo: 28 días\n"
                f"Ganancia Estimada: ${ganancia_estimada:,.2f} MXN\n"
                f"Monto Total al Vencimiento: ${monto_total:,.2f} MXN\n"
            )
            
            print("\n" + reporte)
            print("\nProcesando datos y aplicando delay...")
            time.sleep(2)
            destino = input("Ingresa el correo electrónico donde quieres recibir este análisis: ").strip()
            if destino:
                enviar_email(destino, reporte)
            else:
                print("No ingresaste ningún correo. Se omite el envío.")

        except ValueError:
            print("Error: Debes ingresar un valor numérico válido para la inversión.")
    else:
        print("No se pudo obtener la tasa de Banxico, por lo que no se puede calcular la inversión.")

# 2) FUNCIÓN: CONSULTAR UNA SERIE DE BANXICO
def consultar_banxico():
    # Pedir al usuario el id de la serie
    id_serie = input("Escribe el id de la serie de BANXICO (ej. SF43718): ")
    id_serie = id_serie.strip().upper()

    # Armar la dirección (URL) de la consulta
    url = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/" + id_serie + "/datos/oportuno"

    # BANXICO pide el token en el encabezado (header)
    encabezados = {"Bmx-Token": BANXICO_TOKEN}
    respuesta = requests.get(url, headers=encabezados)

    # Si el código de estado no es 200, algo salió mal
    if respuesta.status_code != 200:
        print("Error en la consulta. Código:", respuesta.status_code)
        print("Mensaje de BANXICO:", respuesta.text)
        print("Token cargado:", BANXICO_TOKEN is not None)
        return None

    # Convertir la respuesta a un diccionario de Python
    datos = respuesta.json()

    # Entrar a la parte del diccionario donde está la información
    serie = datos["bmx"]["series"][0]
    titulo = serie["titulo"]
    fecha = serie["datos"][0]["fecha"]
    valor = serie["datos"][0]["dato"]

    # Armar un texto ya procesado
    texto = "CONSULTA BANXICO\n"
    texto = texto + "----------------\n"
    texto = texto + "Serie: " + id_serie + "\n"
    texto = texto + "Título: " + titulo + "\n"
    texto = texto + "Fecha: " + fecha + "\n"
    texto = texto + "Valor: " + valor + "\n"

    print()
    print(texto)
    time.sleep(3)
    return texto


# 3) FUNCIÓN: CALCULAR VALOR ACUMULADO DE UNA INVERSIÓN
def calcular_inversion():
    # Pedimos los datos al usuario
    capital = float(input("Capital inicial: "))
    print("Tipo de interés:")
    print("  1) Simple")
    print("  2) Compuesto")
    tipo = input("Elige 1 o 2: ")
    tasa = float(input("Tasa de interés anual (en %, ej. 8): "))
    anios = int(input("Número de años: "))

    # Convertimos el porcentaje a decimal (8% -> 0.08)
    tasa_decimal = tasa / 100

    if tipo == "1":
        # Interés simple: M = C * (1 + i * n)
        monto = capital * (1 + tasa_decimal * anios)
        nombre_tipo = "Simple"
    elif tipo == "2":
        # Interés compuesto: M = C * (1 + i) ^ n
        monto = capital * (1 + tasa_decimal) ** anios
        nombre_tipo = "Compuesto"
    else:
        print("Opción no válida.")
        return None

    ganancia = monto - capital

    # Armar el texto del resultado
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


# 4) FUNCIÓN: ENVIAR CORREO
def enviar_correo(texto):
    # Si no hay nada que enviar, avisamos y salimos
    if texto is None:
        print("Primero realiza una operación (opción 1 o 2).")
        return

    destinatario = input("¿A qué correo quieres enviar la información? ")

    # Armamos el correo
    mensaje = MIMEText(texto)
    mensaje["Subject"] = "Información financiera"
    mensaje["From"] = CORREO_EMISOR
    mensaje["To"] = destinatario

    # Nos conectamos al servidor de Gmail y enviamos
    print("Correo emisor cargado:", CORREO_EMISOR is not None)
    print("Clave cargada:", CLAVE_CORREO is not None)
    try:
        servidor = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        servidor.set_debuglevel(1)      # muestra la conversación con el servidor
        servidor.starttls()
        servidor.login(CORREO_EMISOR, CLAVE_CORREO)
        servidor.sendmail(CORREO_EMISOR, destinatario, mensaje.as_string())
        servidor.quit()
        time.sleep(3)
        print("Correo enviado correctamente.")
    except Exception as error:
        time.sleep(3)
        print("No se pudo enviar el correo:", error)

# 5) MENÚ PRINCIPAL

ultimo_resultado = None   

while True:
    print()
    print("========== MENÚ ==========")
    print("1) Consultar serie de BANXICO")
    print("2) Calcular valor acumulado de una inversión")
    print("3) Calcular valor acumulado de una inversión con tasa actual de cetes")
    print("4) Enviar último resultado por correo")
    print("5) Salir")
    opcion = input("Elige una opción: ")

    if opcion == "1":
        ultimo_resultado = consultar_banxico()
        respuesta_menu2=input("¿Desea realizar alguna otra operación? s/n:").strip().lower()
        if respuesta_menu2 != "s":
            print("Finalizando ciclo...\n")
            break
    elif opcion == "2":
        ultimo_resultado = calcular_inversion()
        respuesta_menu2=input("¿Desea realizar alguna otra operación? s/n:").strip().lower()
        if respuesta_menu2 != "s":
            print("Finalizando ciclo...\n")
            break
    elif opcion == "3":
        consultar_cetes()
        calcular_inversion_cetes()
        respuesta_menu2=input("¿Desea realizar alguna otra operación? s/n:").strip().lower()
        if respuesta_menu2 != "s":
            print("Finalizando ciclo...\n")
            break
    elif opcion == "4":
        enviar_correo(ultimo_resultado)
        respuesta_menu2=input("¿Desea realizar alguna otra operación? s/n:").strip().lower()
        if respuesta_menu2 != "s":
            print("Finalizando ciclo...\n")
            break
    elif opcion == "5":
        print("Hasta luego.")
        break
    else:
        print("Opción no válida, intenta de nuevo.")