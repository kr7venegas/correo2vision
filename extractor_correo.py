import os
import time
import ast
import csv
import pyautogui
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==================================================
# CONFIGURACIÓN GENERAL
# ==================================================
HACE_CUANTOS_DIAS = 0 

# ==================================================
# CONFIGURACIÓN DE COORDENADAS
# ==================================================
COORD_BOTON_AÑADIR     = (532, 288)    
COORD_CAMPO_TIPO       = (972, 455)      
COORD_SOLICITADO       = (1079, 303)
COORD_CALLE            = (1110, 358)
COORD_NUMERO           = (1212, 354)
COORD_SCROLL_ENSERES   = (842, 594)  
COORD_ENSERES          = (741, 532)  
COORD_OBSERVACIONES    = (750, 680)
COORD_BOTON_GUARDAR    = (1202, 214)

# ==================================================
# SEGURIDAD Y CREDENCIALES
# ==================================================
pyautogui.FAILSAFE = True  
USER_EMAIL = os.getenv("WEBMAIL_USER", "info@cuidamosgranada.com")
USER_PASS  = os.getenv("WEBMAIL_PASS", "FCC_cuidamos_granada_2026")
FCCMA_USER = os.getenv("FCCMA_USER",  "gonzaled1014")
FCCMA_PASS = os.getenv("FCCMA_PASS",  "UPl()adingkr7")

# --- PERSISTENCIA DE DATOS ---

def cargar_datos_locales(dias_atras):
    nombre_archivo = "registro_correos.txt"
    if not os.path.exists(nombre_archivo): return None
    
    fecha_objetivo = (datetime.now() - timedelta(days=dias_atras)).strftime('%Y-%m-%d')
    try:
        with open(nombre_archivo, "r", encoding="utf-8") as f:
            lineas = f.readlines()
            if lineas and lineas[0].strip() == fecha_objetivo:
                print(f"[SISTEMA] Usando datos guardados de la fecha: {fecha_objetivo}")
                return ast.literal_eval("".join(lineas[1:]))
    except: return None
    return None

def guardar_datos_locales(data, dias_atras):
    fecha_archivo = (datetime.now() - timedelta(days=dias_atras)).strftime('%Y-%m-%d')
    try:
        with open("registro_correos.txt", "w", encoding="utf-8") as f:
            f.write(f"{fecha_archivo}\n{str(data)}")
    except Exception as e:
        print(f"Error guardando TXT: {e}")

def construir_descripcion(item):
    """Construye el texto de descripción/observaciones uniendo las categorías de enseres."""
    detalles = []
    for clave in ["Mobiliario y Descanso", "Aparatos Electrónicos (RAEE)", "Línea Blanca (Electrodomésticos)"]:
        valor = item.get(clave, "").strip()
        if valor:
            detalles.append(valor)
    return " | ".join(detalles) if detalles else "Recogida de muebles/enseres"

def guardar_csv(data, dias_atras):
    """Genera un CSV con el formato de wp_incidencias_BSRME a partir de los datos extraídos."""
    fecha_archivo = (datetime.now() - timedelta(days=dias_atras)).strftime('%Y-%m-%d')
    nombre_csv = f"incidencias_BSRME_{fecha_archivo}.csv"

    cabecera = [
        "CodAviso", "FechaHoraRegistro", "Prioridad", "localizacion", "barrio",
        "calle", "numcalle", "incidencia", "descripcion", "estado",
        "nombre_peticionario", "procedencia", "telefono", "movil", "email",
        "usuario_asignado", "solucion", "fecha_fin", "tipo_resolucion",
        "Foto1", "Foto2", "Foto3", "Foto4", "FotoR1", "FotoR2",
        "categoria", "canal", "incidencia_subtipo", "incidencia_detalle",
        "fecha_evento", "CT", "ampliacion_direccion", "fecha_inicio",
        "descripcion_iniciado", "matricula", "ID"
    ]

    fecha_hora_registro = datetime.now().strftime('%d/%m/%Y %H:%M')

    try:
        with open(nombre_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(cabecera)

            for i, item in enumerate(data, start=1):
                # Construir código de aviso: CC-aaaa-mm-dd-i
                cod_aviso = f"CC-{fecha_archivo}-{i}"

                # Extraer calle y número de la dirección de recogida
                dir_orig = item.get("Dirección de recogida", "")
                partes = dir_orig.split()
                if len(partes) > 1:
                    calle = " ".join(partes[1:])
                else:
                    calle = dir_orig
                numcalle = item.get("Número de la calle", "0")

                # Localización completa (dejamos la dirección original si existe)
                localizacion = dir_orig

                # Descripción igual que observaciones
                descripcion = construir_descripcion(item)

                fila = [
                    cod_aviso,           # CodAviso
                    fecha_hora_registro, # FechaHoraRegistro
                    "Baja",              # Prioridad
                    localizacion,        # localizacion
                    "",                  # barrio (vacío)
                    calle,               # calle
                    numcalle,            # numcalle
                    "solicitud de retirada de muebles y enseres",  # incidencia
                    descripcion,         # descripcion
                    "A revisar por el Área",  # estado
                    "",                  # nombre_peticionario
                    "",                  # procedencia
                    "",                  # telefono
                    "",                  # movil
                    "",                  # email
                    "SERVICIO_RECOGIDA_MUEBLES",  # usuario_asignado
                    "",                  # solucion
                    "",                  # fecha_fin
                    "",                  # tipo_resolucion
                    "",                  # Foto1
                    "",                  # Foto2
                    "",                  # Foto3
                    "",                  # Foto4
                    "",                  # FotoR1
                    "",                  # FotoR2
                    "",                  # categoria
                    "CALLCENTER",        # canal
                    "BSRME",             # incidencia_subtipo
                    "",                  # incidencia_detalle
                    "",                  # fecha_evento
                    "",                  # CT
                    "",                  # ampliacion_direccion
                    "",                  # fecha_inicio
                    "",                  # descripcion_iniciado
                    "",                  # matricula
                    "",                  # ID
                ]
                writer.writerow(fila)

        print(f"[CSV] Archivo guardado: {nombre_csv}")
    except Exception as e:
        print(f"Error guardando CSV: {e}")

# --- PROCESO 1: EXTRACCIÓN DINAHOSTING ---

def extraer_de_dinahosting(dias_atras):
    print(f"[DINAHOSTING] Buscando correos de hace {dias_atras} días...")
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)
    
    fecha_dt = datetime.now() - timedelta(days=dias_atras)
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    fecha_busqueda = f"{fecha_dt.day} {meses[fecha_dt.month - 1]}"

    try:
        driver.get("https://dinahosting.email/login")
        wait.until(EC.presence_of_element_located((By.ID, "user"))).send_keys(USER_EMAIL)
        driver.find_element(By.ID, "password").send_keys(USER_PASS)
        driver.find_element(By.ID, "password").submit()

        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.list-group-item")))
        asunto_target = "Se ha rellenado el formulario de recogida de muebles/enseres"
        
        mails_objetivo = []
        elementos = driver.find_elements(By.CSS_SELECTOR, "li.list-group-item")
        
        for em in elementos:
            asunto = em.find_element(By.CSS_SELECTOR, "div.small span.ng-binding").text.strip()
            fecha_texto = em.find_element(By.CSS_SELECTOR, "small.text-muted").text.strip().lower()
            
            es_fecha_correcta = (":" in fecha_texto) if dias_atras == 0 else (fecha_busqueda in fecha_texto)
            
            if asunto == asunto_target and es_fecha_correcta:
                mails_objetivo.append(em.get_attribute("id"))

        print(f"[DINAHOSTING] Encontrados {len(mails_objetivo)} correos para la fecha seleccionada.")

        resultados = []
        for mid in mails_objetivo:
            driver.find_element(By.ID, mid).click()
            time.sleep(2)
            body = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[ng-bind-html^='wmdc.mail.body']")))
            nombres = body.find_elements(By.CSS_SELECTOR, "td.field-name strong")
            valores = body.find_elements(By.CSS_SELECTOR, "td.field-value")
            
            dic = {"mail_id": mid}
            for n, v in zip(nombres, valores):
                dic[n.text.replace(':', '').strip()] = v.text.strip()
            resultados.append(dic)
            driver.back()
            time.sleep(1)
        
        if resultados:
            guardar_datos_locales(resultados, dias_atras)
            guardar_csv(resultados, dias_atras)  # <-- Genera el CSV junto al TXT
        
        driver.quit()
        return resultados
    except Exception as e:
        print(f"Error Dinahosting: {e}")
        driver.quit()
        return []

# --- PROCESO 2: NAVEGACIÓN VISION ---

def preparar_vision():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    print("Iniciando sesión en Vision...")
    driver.get("https://portal.fccma.com/vision/#/areas")
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(FCCMA_USER)
    driver.find_element(By.ID, "password").send_keys(FCCMA_PASS)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    
    wait.until(EC.url_contains("/areas"))
    driver.get("https://portal.fccma.com/vision/#/ma_prc_609_300/INC/93545/d/1")
    time.sleep(10) 
    return driver

# --- PROCESO 3: RELLENADO POR PÍXELES ---

def ejecutar_rellenado_pixeles(datos):
    print(f"Comenzando rellenado de {len(datos)} registros. No muevas el ratón.")
    pyautogui.press('alt')
    time.sleep(0.5)

    for item in datos:
        texto_obs = construir_descripcion(item)

        # 1. Botón Añadir
        pyautogui.click(COORD_BOTON_AÑADIR)
        time.sleep(4)
        
        # 2. Tipo Incidencia
        pyautogui.click(COORD_CAMPO_TIPO)
        pyautogui.write("recogida de muebles y enseres", interval=0.03)
        time.sleep(3)
        pyautogui.press('down')
        pyautogui.press('enter')
        
        # 3. Solicitado
        pyautogui.click(COORD_SOLICITADO)
        pyautogui.write("BSRME")
        time.sleep(0.5)
        pyautogui.press('tab')

        # 4. Calle
        dir_orig = item.get("Dirección de recogida", "")
        calle = " ".join(dir_orig.split()[1:]) if len(dir_orig.split()) > 1 else dir_orig
        pyautogui.click(COORD_CALLE)
        pyautogui.write(calle, interval=0.04)
        time.sleep(4) 
        pyautogui.press('enter')
        time.sleep(1)

        # 5. Número
        pyautogui.click(COORD_NUMERO)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        pyautogui.write(str(item.get("Número de la calle", "1")))
        
        # 6. SCROLL DOBLE CLICK
        pyautogui.doubleClick(COORD_SCROLL_ENSERES)
        time.sleep(2)
        
        # 7. Número de enseres
        pyautogui.click(COORD_ENSERES)
        pyautogui.write(str(item.get("Número de enseres", "1")))
        
        # 8. Observaciones
        pyautogui.click(COORD_OBSERVACIONES)
        pyautogui.write(texto_obs.replace("\n", " "), interval=0.01)
        
        # 9. Guardar
        pyautogui.click(COORD_BOTON_GUARDAR)
        time.sleep(8) 

# --- FLUJO DE EJECUCIÓN ---

if __name__ == "__main__":
    datos = cargar_datos_locales(HACE_CUANTOS_DIAS)
    
    if not datos:
        datos = extraer_de_dinahosting(HACE_CUANTOS_DIAS)

    if datos:
        # Las dos líneas siguientes arrancan el rellenado automático en Vision.
        driver_v = preparar_vision()
        ejecutar_rellenado_pixeles(datos)
        print("Datos listos. Rellenado en Vision desactivado (modo prueba).")
    else:
        print(f"No hay datos disponibles para la fecha seleccionada ({HACE_CUANTOS_DIAS} días atrás).")