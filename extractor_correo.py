import os
import time
import ast
import csv
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Intentar importar openpyxl para el archivo Excel nativo
try:
    import openpyxl
    OPENPYXL_DISPONIBLE = True
except ImportError:
    OPENPYXL_DISPONIBLE = False

# ==================================================
# CONFIGURACIÓN GENERAL
# ==================================================
HACE_CUANTOS_DIAS = 1  # Configurado a 0 para buscar los correos de hoy

# ==================================================
# SEGURIDAD Y CREDENCIALES
# ==================================================
USER_EMAIL = os.getenv("WEBMAIL_USER", "info@cuidamosgranada.com")
USER_PASS  = os.getenv("WEBMAIL_PASS", "FCC_cuidamos_granada_2026")

def guardar_datos_locales(data, dias_atras):
    fecha_archivo = (datetime.now() - timedelta(days=dias_atras)).strftime('%Y-%m-%d')
    try:
        with open("registro_correos.txt", "w", encoding="utf-8") as f:
            f.write(f"{fecha_archivo}\n{str(data)}")
    except Exception as e:
        print(f"Error guardando TXT: {e}")

def construir_descripcion(item):
    detalles = []
    for clave in ["Mobiliario y Descanso", "Aparatos Electrónicos (RAEE)", "Línea Blanca (Electrodomésticos)"]:
        valor = item.get(clave, "").strip()
        if valor:
            detalles.append(valor)
    return " | ".join(detalles) if detalles else "Recogida de muebles/enseres"

def generar_filas_datos(data, dias_atras):
    """Estructura las filas exactamente con el orden y campos requeridos."""
    fecha_archivo = (datetime.now() - timedelta(days=dias_atras)).strftime('%Y-%m-%d')
    fecha_hora_registro = datetime.now().strftime('%d/%m/%Y %H:%M')
    filas = []

    for i, item in enumerate(data, start=1):
        cod_aviso = f"CC-{fecha_archivo}-{i}"
        dir_orig = item.get("Dirección de recogida", "")
        partes = dir_orig.split()
        calle = " ".join(partes[1:]) if len(partes) > 1 else dir_orig
        numcalle = item.get("Número de la calle", "0")
        descripcion = construir_descripcion(item)

        fila = [
            cod_aviso,           # CodAviso
            fecha_hora_registro, # FechaHoraRegistro
            "Alta",              # Prioridad
            dir_orig,            # localizacion
            "",                  # barrio
            calle,               # calle
            numcalle,            # numcalle
            "solicitud de retirada de muebles y enseres", # incidencia
            descripcion,         # descripcion
            "A revisar por el Área", # estado
            "", "", "", "", "",  # Datos personales vacíos
            "SERVICIO_RECOGIDA_MUEBLES", # usuario_asignado
            "", "", "", "", "", "", "", "", "", # Fotos vacías
            "CALLCENTER",        # categoria
            "BSRME",             # canal
            "",                  # incidencia_subtipo
            "", "", "", "", "", "", "", "" # Resto de campos vacíos
        ]
        filas.append(fila)
    return filas

def guardar_csv(cabecera, filas, dias_atras):
    """Genera el archivo CSV delimitado por punto y coma."""
    fecha_archivo = (datetime.now() - timedelta(days=dias_atras)).strftime('%Y-%m-%d')
    nombre_csv = f"incidencias_BSRME_{fecha_archivo}.csv"
    try:
        with open(nombre_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(cabecera)
            writer.writerows(filas)
        print(f"[CSV] Archivo guardado correctamente: {nombre_csv}")
    except Exception as e:
        print(f"Error guardando CSV: {e}")

def guardar_xlsx(cabecera, filas, dias_atras):
    """Genera el archivo Excel nativo en formato .xlsx."""
    if not OPENPYXL_DISPONIBLE:
        print("[ALERTA XLSX] No se pudo crear el .xlsx porque 'openpyxl' no está instalado. Ejecuta: pip install openpyxl")
        return

    fecha_archivo = (datetime.now() - timedelta(days=dias_atras)).strftime('%Y-%m-%d')
    nombre_xlsx = f"incidencias_BSRME_{fecha_archivo}.xlsx"
    
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Incidencias"
        
        # Escribir la cabecera
        ws.append(cabecera)
        
        # Escribir todas las filas de datos
        for fila in filas:
            ws.append(fila)
            
        wb.save(nombre_xlsx)
        print(f"[XLSX] Archivo Excel guardado correctamente: {nombre_xlsx}")
    except Exception as e:
        print(f"Error guardando XLSX: {e}")

def extraer_de_dinahosting(dias_atras):
    print(f"[DINAHOSTING] Buscando correos de hace {dias_atras} días...")
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)
    
    fecha_dt = datetime.now() - timedelta(days=dias_atras)
    meses = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
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
            
            if dias_atras == 0:
                es_fecha_correcta = (":" in fecha_texto)
            else:
                es_fecha_correcta = (fecha_busqueda in fecha_texto or fecha_busqueda.replace(" ", "") in fecha_texto.replace(" ", ""))
            
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
            
            # Definición de columnas comunes
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
            filas_procesadas = generar_filas_datos(resultados, dias_atras)
            
            # Exportaciones masivas
            guardar_csv(cabecera, filas_procesadas, dias_atras)
            guardar_xlsx(cabecera, filas_procesadas, dias_atras)
        
        driver.quit()
        return resultados
    except Exception as e:
        print(f"Error Dinahosting: {e}")
        driver.quit()
        return []

if __name__ == "__main__":
    extraer_de_dinahosting(HACE_CUANTOS_DIAS)