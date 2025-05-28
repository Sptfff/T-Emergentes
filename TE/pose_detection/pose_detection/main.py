import cv2
import numpy as np
import time
from ejercicios.sentadilla import Sentadilla
from ejercicios.flexion import Flexion
from detector.pose_detector import DetectorPostura, calcular_angulo
from contador.contador import ContadorRepeticiones 

# --- Configuración de ejercicios disponibles ---
EJERCICIOS_DISPONIBLES = {
    "Sentadilla": Sentadilla,
    "Flexion": Flexion,
}

ejercicio_seleccionado = None
verificador = None
modo_seleccion = True

# Inicializar
cap = cv2.VideoCapture(0)
detector = DetectorPostura()
contador = ContadorRepeticiones()

empezado = False
serie_finalizada = False
ultimo_tiempo_repeticion = None
tiempo_limite = 10  # segundos de inactividad permitidos

# Posiciones de botones
botones = {
    "Sentadilla": ((10, 10), (210, 60)),
    "Flexion": ((10, 70), (210, 120))
}

def evento_click(evento, x, y, flags, param):
    global empezado, serie_finalizada, ultimo_tiempo_repeticion
    global modo_seleccion, verificador, ejercicio_seleccionado

    if evento == cv2.EVENT_LBUTTONDOWN:
        if modo_seleccion:
            for nombre, (pt1, pt2) in botones.items():
                if pt1[0] < x < pt2[0] and pt1[1] < y < pt2[1]:
                    ejercicio_seleccionado = nombre
                    verificador = EJERCICIOS_DISPONIBLES[nombre]()
                    modo_seleccion = False
                    print(f"Ejercicio seleccionado: {nombre}")
        else:
            if 10 < x < 210 and 10 < y < 60:
                empezado = True
                serie_finalizada = False
                contador.contador = 0
                contador.direccion = 0
                ultimo_tiempo_repeticion = None

cv2.namedWindow("Entrenador")
cv2.setMouseCallback("Entrenador", evento_click)

while True:
    exito, img = cap.read()
    img = cv2.flip(img, 1)

    if modo_seleccion:
        # Menú de selección de ejercicio
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(img, "Selecciona un ejercicio", (50, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        for nombre, (pt1, pt2) in botones.items():
            cv2.rectangle(img, pt1, pt2, (0, 255, 0), -1)
            cv2.putText(img, nombre, (pt1[0]+10, pt1[1]+35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
        cv2.imshow("Entrenador", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    img = detector.encontrar_postura(img)
    puntos = detector.obtener_puntos_clave(img)

    feedback = ""
    progreso = 0
    conteo = contador.contador

    tiempo_inactivo = 0
    if ultimo_tiempo_repeticion is not None:
        tiempo_inactivo = time.time() - ultimo_tiempo_repeticion
    tiempo_restante = max(0, int(tiempo_limite - tiempo_inactivo))

    if empezado and not serie_finalizada:
        if puntos and len(puntos) > 32:
            feedback, progreso = verificador.verificar(puntos)
            angulo_prom = (
                calcular_angulo(puntos[23], puntos[25], puntos[27]) +
                calcular_angulo(puntos[24], puntos[26], puntos[28])
            ) / 2
            conteo_anterior = contador.contador
            contador.actualizar(angulo_prom)
            conteo = contador.contador

            if conteo > conteo_anterior:
                ultimo_tiempo_repeticion = time.time()

        if conteo > 0 and tiempo_restante <= 5:
            cv2.putText(img, f"Fin en {tiempo_restante}s",
                        (400, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        if conteo > 0 and tiempo_inactivo > tiempo_limite:
            serie_finalizada = True
            empezado = False

    if not empezado and not serie_finalizada:
        cv2.rectangle(img, (10, 10), (210, 60), (0, 255, 0), -1)
        cv2.putText(img, "EMPEZAR", (30, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    cv2.putText(img, f'Repeticiones: {conteo}', (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

    if empezado and not serie_finalizada:
        progreso_barra = int(np.interp(progreso, [0, 100], [400, 150]))
        cv2.rectangle(img, (570, 150), (600, 400), (0, 255, 0), 2)
        cv2.rectangle(img, (570, progreso_barra), (600, 400), (0, 255, 0), -1)
        cv2.putText(img, f'{int(progreso)}%', (570, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    if feedback:
        for i, linea in enumerate(feedback.split("\n")):
            cv2.putText(img, linea, (20, 400 + i*30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    if serie_finalizada:
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(img, "Serie finalizada", (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
        cv2.putText(img, f"Total repeticiones: {conteo}", (50, 200),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
        cv2.putText(img, "Haz click en EMPEZAR para reiniciar", (50, 300),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)

    cv2.imshow("Entrenador", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
