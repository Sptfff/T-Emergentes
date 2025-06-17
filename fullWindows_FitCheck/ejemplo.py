import cv2
import time

def probar_camara(indice, backends):
    for backend in backends:
        print(f"\nIntentando abrir cámara {indice} con backend {backend}...")
        cap = cv2.VideoCapture(indice, backend)
        time.sleep(1)  # Dar tiempo a que se inicialice

        if not cap.isOpened():
            print(f"[ERROR] No se pudo abrir la cámara con backend {backend}")
            continue

        ret, frame = cap.read()
        if not ret or frame is None:
            print(f"[ADVERTENCIA] Cámara abierta con backend {backend}, pero no entrega imagen (ret={ret})")
            cap.release()
            continue

        print(f"[OK] Cámara {indice} funciona con backend {backend}")
        cv2.imshow(f"Cámara {indice} con backend {backend}", frame)
        cv2.waitKey(0)
        cap.release()
        cv2.destroyAllWindows()
        return

    print(f"[ERROR] Ninguna combinación funcionó para la cámara {indice}")

# Ejecutar prueba
probar_camara(1, [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY])
