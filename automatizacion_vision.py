import os
import time
import ast
import pyautogui
import pyperclip  # Recuerda instalarlo ejecutando en tu terminal: pip install pyperclip
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==================================================
# CONFIGURACIÓN GENERAL
# ==================================================
HACE_CUANTOS_DIAS = 0

# ==================================================
# CONFIGURACIÓN DE COORDENADAS PÍXELES
# ==================================================
COORD_BOTON_AÑADIR     = (532, 288)    
COORD_CAMPO_TIPO       = (972, 455)      
COORD_SOLICITADO       = (1079, 303)
COORD_PRIORIDAD        = (975, 640)
COORD_CALLE            = (1110, 358)
COORD_NUMERO           = (1212, 354)
COORD_SCROLL_ENSERES   = (842, 594)  
COORD_ENSERES          = (785, 595)  
COORD_OBSERVACIONES    = (750, 680)
COORD_BOTON_GUARDAR    = (1202, 214)

# ==================================================
# SEGURIDAD Y CREDENCIALES
# ==================================================
pyautogui.FAILSAFE = True  
FCCMA_USER = os.getenv("FCCMA_USER",  "gonzaled1014")
FCCMA_PASS = os.getenv("FCCMA_PASS",  "UPl()adingkr7")

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

def construir_descripcion(item):
    detalles = []
    for clave in ["Mobiliario y Descanso", "Aparatos Electrónicos (RAEE)", "Línea Blanca (Electrodomésticos)"]:
        valor = item.get(clave, "").strip()
        if valor:
            detalles.append(valor)
    return " | ".join(detalles) if detalles else "CALLCENTER"

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
        pyautogui.write("CALLCENTER", interval=0.03)
        time.sleep(3)
        pyautogui.press('down')
        pyautogui.press('enter')
        
        # 3. Solicitado y Prioridad Alta
        pyautogui.click(COORD_SOLICITADO)
        pyautogui.write("BSRME")
        time.sleep(0.5)
        
        pyautogui.click(COORD_PRIORIDAD)
        time.sleep(0.5)
        pyautogui.write("Alta")
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(0.5)

        # 4. Calle (Corregido con pyperclip y pulsación hacia arriba)
        dir_orig = item.get("Dirección de recogida", "")
        calle = " ".join(dir_orig.split()[1:]) if len(dir_orig.split()) > 1 else dir_orig
        
        pyautogui.click(COORD_CALLE)
        time.sleep(0.5)
        
        # Copiar calle al portapapeles y pegar (evita problemas de tildes)
        pyperclip.copy(calle)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(4) # Espera a que cargue el desplegable de direcciones
        
        # LÓGICA NUEVA: 1 click hacia arriba selecciona el último elemento directamente
        pyautogui.press('up')
        time.sleep(0.2)
        pyautogui.press('enter')
        time.sleep(1)

        # 5. Número
        pyautogui.click(COORD_NUMERO)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        pyautogui.write(str(item.get("Número de la calle", "1")))
        
        # 6. SCROLL CORREGIDO (Usa la rueda del ratón de forma nativa)
        # Hacemos clic primero en la zona para darle foco al formulario intermedio
        pyautogui.click(COORD_SCROLL_ENSERES)
        time.sleep(0.2)
        # Un valor de -300 o -400 equivale a deslizar la rueda hacia abajo varias veces
        pyautogui.scroll(-400) 
        time.sleep(2)
        
        # 7. Número de enseres
        pyautogui.click(COORD_ENSERES)
        pyautogui.write(str(item.get("Número de enseres", "1")))
        
        # 8. Observaciones (Corregido también con pyperclip por si contiene tildes)
        pyautogui.click(COORD_OBSERVACIONES)
        pyperclip.copy(texto_obs.replace("\n", " "))
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        
        # 9. Guardar
        pyautogui.click(COORD_BOTON_GUARDAR)
        print(f"OK: Registro {item.get('mail_id')} procesado con canales corregidos.")
        time.sleep(8) 


if __name__ == "__main__":
    datos = cargar_datos_locales(HACE_CUANTOS_DIAS)
    
    if datos:
        driver_v = preparar_vision()
        ejecutar_rellenado_pixeles(datos)
        print("[PROCESO TERMINADO] Rellenado en Vision completado con éxito.")
    else:
        print(f"[ALERTA] No existen datos guardados localmente para la fecha seleccionada ({HACE_CUANTOS_DIAS} días atrás). Ejecuta primero 'extractor_correo.py'.")