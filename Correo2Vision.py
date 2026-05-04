from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

# 1. Configuración de opciones del navegador
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_experimental_option("detach", True)

service = Service() 
driver = webdriver.Chrome(service=service, options=chrome_options)

# --- Credenciales ---
USER_EMAIL = os.getenv("WEBMAIL_USER", "info@cuidamosgranada.com")
USER_PASS = os.getenv("WEBMAIL_PASS", "FCC_cuidamos_granada_2026")
FCCMA_USER = os.getenv("FCCMA_USER", "gonzaled1014")
FCCMA_PASS = os.getenv("FCCMA_PASS", "UPl()adingkr7")

def iniciar_acceso():
    try:
        driver.get("https://dinahosting.email/login")
        wait = WebDriverWait(driver, 10)
        user_field = wait.until(EC.presence_of_element_located((By.ID, "user")))
        user_field.send_keys(USER_EMAIL)
        driver.find_element(By.ID, "password").send_keys(USER_PASS)
        driver.find_element(By.ID, "password").submit()
        
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.list-group-item")))
        asunto_buscado = "Se ha rellenado el formulario de recogida de muebles/enseres"
        fecha_hoy = time.strftime("%d/%m/%Y")
        
        target_ids = []
        listado = driver.find_elements(By.CSS_SELECTOR, "li.list-group-item")
        
        for email in listado:
            try:
                asunto = email.find_element(By.CSS_SELECTOR, "div.small span.ng-binding").text.strip()
                fecha_texto = email.find_element(By.CSS_SELECTOR, "small.text-muted").text.strip()
                if asunto == asunto_buscado:
                    if "/" not in fecha_texto or "Hoy" in fecha_texto or fecha_hoy in fecha_texto:
                        target_ids.append(email.get_attribute("id"))
            except: continue

        all_extracted_data = []
        for index, mail_id in enumerate(target_ids):
            try:
                elemento = wait.until(EC.element_to_be_clickable((By.ID, mail_id)))
                elemento.click()
                time.sleep(3)
                mail_body = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#preview-mail-detail div[ng-bind-html^='wmdc.mail.body']")))
                
                nombres = mail_body.find_elements(By.CSS_SELECTOR, "td.field-name strong")
                valores = mail_body.find_elements(By.CSS_SELECTOR, "td.field-value")
                
                if nombres and valores:
                    form_data = {"mail_id": mail_id}
                    for n_el, v_el in zip(nombres, valores):
                        form_data[n_el.text.replace(':', '').strip()] = v_el.text.strip()
                    all_extracted_data.append(form_data)
                
                if index < len(target_ids) - 1:
                    driver.back()
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.webmail__mails-list")))
            except Exception as e:
                print(f"Error en correo {mail_id}: {e}")
        return all_extracted_data
    except Exception as e:
        print(f"Error general Dinahosting: {e}")
        return []

def iniciar_sesion_fccma():
    try:
        driver.get("https://portal.fccma.com/vision/#/areas")
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(FCCMA_USER)
        driver.find_element(By.ID, "password").send_keys(FCCMA_PASS)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        wait.until(EC.url_contains("/areas"))
        driver.get("https://portal.fccma.com/vision/#/ma_prc_609_300/INC/93545/d/1")
        time.sleep(5)
    except Exception as e:
        print(f"Error login VISION: {e}")

def rellenar_formulario_fccma(data_list):
    wait = WebDriverWait(driver, 15)

    def get_element_shadow(field_name, tag="input"):
        script = f"""
            const findLast = (sel) => {{
                const elms = document.querySelectorAll(sel);
                return elms.length > 0 ? elms[elms.length - 1] : null;
            }};
            let field = findLast(`[field-name='{field_name}'], [name='{field_name}']`);
            if (!field) return null;
            let inner = field.tagName.includes('INPUT-') ? field : field.querySelector('input-text, input-number, input-selector, input-textarea');
            if (!inner || !inner.shadowRoot) return null;
            return inner.shadowRoot.querySelector('{tag}');
        """
        return driver.execute_script(script)

    def type_slowly(element, text):
        if not element: return
        element.click()
        driver.execute_script("arguments[0].value = '';", element)
        for char in str(text):
            element.send_keys(char)
            time.sleep(0.05)
        driver.execute_script("""
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));
        """, element)

    def open_flechita(field_name):
        script = f"""
            const findLast = (sel) => {{
                const elms = document.querySelectorAll(sel);
                return elms.length > 0 ? elms[elms.length - 1] : null;
            }};
            let field = findLast(`[field-name='{field_name}'], [name='{field_name}']`);
            if (!field) return;
            let inner = field.tagName === 'INPUT-SELECTOR' ? field : field.querySelector('input-selector');
            if (!inner || !inner.shadowRoot) return;
            const arrow = inner.shadowRoot.querySelector('icon-dropdown-selector, .icon-selector, button, .arrow');
            if (arrow) arrow.click();
        """
        driver.execute_script(script)

    def marcar_checkbox_otro(field_name):
        script = f"""
            const findLast = (sel) => {{
                const elms = document.querySelectorAll(sel);
                return elms.length > 0 ? elms[elms.length - 1] : null;
            }};
            let field = findLast(`[field-name='{field_name}'], [name='{field_name}']`);
            if (!field) return false;
            let inner = field.tagName === 'INPUT-SELECTOR' ? field : field.querySelector('input-selector');
            if (!inner || !inner.shadowRoot) return false;
            const options = inner.shadowRoot.querySelectorAll('option-row, .option-item, label');
            for (let opt of options) {{
                if (opt.textContent.toLowerCase().includes('otro')) {{
                    const box = opt.querySelector('input[type="checkbox"]') || opt.querySelector('.checkbox-icon') || opt;
                    box.click();
                    return true;
                }}
            }}
            return false;
        """
        return driver.execute_script(script)

    def click_first_option(field_name):
        script = f"""
            const findLast = (sel) => {{
                const elms = document.querySelectorAll(sel);
                return elms.length > 0 ? elms[elms.length - 1] : null;
            }};
            let field = findLast(`[field-name='{field_name}'], [name='{field_name}']`);
            if (!field) return;
            let inner = field.tagName === 'INPUT-SELECTOR' ? field : field.querySelector('input-selector');
            if (!inner || !inner.shadowRoot) return;
            const firstOption = inner.shadowRoot.querySelector('option-row, label');
            if (firstOption) firstOption.click();
        """
        driver.execute_script(script)
    
    for item_data in data_list:
        try:
            print(f"\n> Procesando correo ID: {item_data.get('mail_id')}")

            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "action-bar[main-bar]")))
            driver.execute_script("""
                const actionBar = document.querySelector('action-bar[main-bar]');
                const btn = actionBar.shadowRoot.querySelector('bar-button[type="add"]');
                if (btn) btn.click();
            """)
            
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form-field[field-name='ior_inc']")))
            time.sleep(2)

            # --- PASO 1: SELECCIONAR TIPO (LO PRIMERO PARA DISPARAR CARGA) ---
            print("  > 1. Tipo: Seleccionando 'recogida de muebles y enseres'...")
            open_flechita("tin_inc")
            time.sleep(1)
            target_type = get_element_shadow("tin_inc")
            if target_type:
                type_slowly(target_type, "recogida de muebles y enseres")
                time.sleep(2)
                click_first_option("tin_inc")
                driver.execute_script("document.activeElement.blur();")

            # --- PASO 2: RELLENAR EL RESTO MIENTRAS EL SISTEMA CARGA DETALLE1 ---
            print("  > 2. Rellenando datos generales...")
            
            # Solicitado por
            sol_field = get_element_shadow("ior_inc")
            if sol_field: type_slowly(sol_field, "BSRME")

            # Dirección y Número
            direccion_original = item_data.get("Dirección de recogida", "")
            direccion_busqueda = " ".join(direccion_original.split()[1:])
            driver.execute_script("""
                const elms = document.querySelectorAll("[field-name='calle'], [name='calle']");
                const field = elms[elms.length - 1];
                const inner = field.tagName === 'INPUT-SELECTOR' ? field : field.querySelector('input-selector');
                const input = inner.shadowRoot.querySelector('input');
                if (input) input.click();
            """)
            time.sleep(1)
            addr_input = get_element_shadow("calle")
            if addr_input:
                type_slowly(addr_input, direccion_busqueda)
                time.sleep(2)
                click_first_option("calle")

            num_field = get_element_shadow("numero")
            if num_field: type_slowly(num_field, item_data.get("Número de la calle", ""))
            
            nen_field = get_element_shadow("nen_inc")
            if nen_field: type_slowly(nen_field, item_data.get("Número de enseres", ""))

            # Prioridad
            open_flechita("pri_inc")
            time.sleep(1)
            target_pri = get_element_shadow("pri_inc")
            if target_pri:
                type_slowly(target_pri, "Alta")
                time.sleep(1)
                click_first_option("pri_inc")

            # Observaciones
            muebles = item_data.get("Mobiliario y Descanso", "").replace("\n", " ").strip()
            raee = item_data.get("Aparatos Electrónicos (RAEE)", "").replace("\n", " ").strip()
            obs_list = []
            if muebles: obs_list.append(f"Muebles: {muebles}")
            if raee: obs_list.append(f"RAEE: {raee}")
            text_obs = " | ".join(obs_list) if obs_list else "Recogida de enseres"
            obs_field = get_element_shadow("obs_inc", tag="textarea")
            if obs_field: type_slowly(obs_field, text_obs)

            # --- PASO 3: MARCAR 'OTRO' (ÚLTIMO PASO ANTES DE GUARDAR) ---
            print("  > 3. Marcando checkbox 'Otro' en detalle1...")
            open_flechita("detalle1")
            time.sleep(2) # Pausa mínima final de seguridad
            
            if marcar_checkbox_otro("detalle1"):
                print("  [OK]: Checkbox 'Otro' marcado.")
            else:
                print("  [!] No se pudo marcar 'Otro'.")

            # --- PASO 4: GUARDAR ---
            print("  > 4. Guardando formulario...")
            driver.execute_script("""
                const btns = document.querySelectorAll('input-button[name="finish-button"]');
                if (btns.length > 0) btns[btns.length - 1].shadowRoot.querySelector('button').click();
            """)
            
            print("  OK. Registro completado.")
            time.sleep(2)
            
        except Exception as e:
            print(f"  X Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    extracted_email_data = iniciar_acceso() 
    if extracted_email_data:
        iniciar_sesion_fccma()
        rellenar_formulario_fccma(extracted_email_data)
    print("\nProceso terminado.")