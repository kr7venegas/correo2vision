import pyautogui
import time

print("--- CALIBRADOR DE PÍXELES ---")
print("Mueve el ratón al botón deseado. Tienes 5 segundos.")
print("La coordenada que veas aquí es la que debes poner en el código.")
print("-" * 30)

try:
    while True:
        # Esto te da la posición REAL en tu monitor
        x, y = pyautogui.position()
        print(f"X: {x}  Y: {y}  (Presiona Ctrl+C para salir)", end="\r")
        time.sleep(0.1)
except KeyboardInterrupt:
    print(f"\n\nÚltima posición capturada: COORD = ({x}, {y})")