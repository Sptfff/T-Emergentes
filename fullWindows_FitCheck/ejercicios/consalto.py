from .base import EjercicioBase
from utils.pose_utils import calcular_angulo
import cv2
import numpy as np

class SentadillaConSalto(EjercicioBase):
    def __init__(self):
        super().__init__()
        self.estado_actual = "arriba"
        self.mensaje_guia = ""
        self.en_salto = False
        self.altura_max_salto = 0.0

        self.errores_contador = {
            "pies_juntos": 0,
            "espalda_inclinada": 0,
            "rodillas_hacia_adentro": 0,
            "sin_salto": 0,
            "salto_insuficiente": 0
        }

        self.error_flags = {
            "pies_juntos": False,
            "espalda_inclinada": False,
            "rodillas_hacia_adentro": False,
            "sin_salto": False,
            "salto_insuficiente": False
        }

    def procesar_pose(self, landmarks):
        rodilla = (landmarks['RIGHT_KNEE'].x, landmarks['RIGHT_KNEE'].y)
        cadera = (landmarks['RIGHT_HIP'].x, landmarks['RIGHT_HIP'].y)
        tobillo = (landmarks['RIGHT_ANKLE'].x, landmarks['RIGHT_ANKLE'].y)
        hombro = (landmarks['RIGHT_SHOULDER'].x, landmarks['RIGHT_SHOULDER'].y)

        angulo_rodilla = calcular_angulo(cadera, rodilla, tobillo)
        angulo_espalda = calcular_angulo(hombro, cadera, rodilla)
        distancia_pies = abs(landmarks['RIGHT_FOOT_INDEX'].x - landmarks['LEFT_FOOT_INDEX'].x)
        altura_cadera = cadera[1]

        umbral_bajada = 90
        umbral_subida = 160
        umbral_dist_pies = 0.12
        umbral_espalda = 70
        umbral_salto = 0.05

        mensajes = []
        nueva_repeticion = False

        if self.estado_actual == "arriba" and angulo_rodilla < umbral_bajada:
            self.estado_actual = "bajando"
            self.altura_max_salto = altura_cadera
        elif self.estado_actual == "bajando" and angulo_rodilla > umbral_subida:
            # Detectamos salto si sube más de lo habitual
            if altura_cadera < self.altura_max_salto - umbral_salto:
                self.en_salto = True
            self.estado_actual = "subiendo"
        elif self.estado_actual == "subiendo" and angulo_rodilla > umbral_subida:
            if self.en_salto:
                self.repeticiones += 1
                mensajes.append("Buen salto!")
                nueva_repeticion = True
            else:
                if not self.error_flags["sin_salto"]:
                    self.errores_contador["sin_salto"] += 1
                    self.error_flags["sin_salto"] = True
                    mensajes.append("Debes saltar luego de la sentadilla")
            self.en_salto = False
            self.estado_actual = "arriba"

        if distancia_pies < umbral_dist_pies and not self.error_flags["pies_juntos"]:
            self.errores_contador["pies_juntos"] += 1
            self.error_flags["pies_juntos"] = True
            mensajes.append("Separa los pies")

        if angulo_espalda < umbral_espalda and not self.error_flags["espalda_inclinada"]:
            self.errores_contador["espalda_inclinada"] += 1
            self.error_flags["espalda_inclinada"] = True
            mensajes.append("Manten la espalda recta")

        if rodilla[0] < tobillo[0] - 0.07 and not self.error_flags["rodillas_hacia_adentro"]:
            self.errores_contador["rodillas_hacia_adentro"] += 1
            self.error_flags["rodillas_hacia_adentro"] = True
            mensajes.append("Rodillas hacia adentro")

        if self.en_salto and self.altura_max_salto - altura_cadera < umbral_salto and not self.error_flags["salto_insuficiente"]:
            self.errores_contador["salto_insuficiente"] += 1
            self.error_flags["salto_insuficiente"] = True
            mensajes.append("Salta mas alto")

        if nueva_repeticion:
            for key in self.error_flags:
                self.error_flags[key] = False

        if not mensajes and self.estado_actual == "arriba":
            mensajes.append("Baja y salta")

        self.mensaje_guia = " | ".join(mensajes)

    def dibujar_feedback(self, frame, landmarks):
        height, width = frame.shape[:2]
        overlay = np.zeros_like(frame)

        def to_pixel(landmark):
            return int(landmark.x * width), int(landmark.y * height)

        cadera_px = to_pixel(landmarks['RIGHT_HIP'])
        rodilla_px = to_pixel(landmarks['RIGHT_KNEE'])
        tobillo_px = to_pixel(landmarks['RIGHT_ANKLE'])

        # Dibujo de líneas y puntos del ángulo
        cv2.line(overlay, cadera_px, rodilla_px, (0, 255, 0), 6)
        cv2.line(overlay, rodilla_px, tobillo_px, (0, 255, 0), 6)
        cv2.circle(overlay, cadera_px, 8, (255, 0, 0), -1)
        cv2.circle(overlay, rodilla_px, 8, (0, 255, 255), -1)
        cv2.circle(overlay, tobillo_px, 8, (0, 0, 255), -1)

        triangle_cnt = np.array([cadera_px, rodilla_px, tobillo_px])
        cv2.fillPoly(overlay, [triangle_cnt], color=(128, 0, 250))

        if hasattr(self, "ultimo_angulo"):
            angulo_mostrado = int(max(0, min(180, self.ultimo_angulo)))
            cv2.putText(overlay, str(angulo_mostrado),
                        (rodilla_px[0] + 10, rodilla_px[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

        # Barra de progreso
        barra_altura = int(height * 0.6)
        barra_ancho = 30
        barra_x = width - 50
        barra_y = int(height * 0.2)

        for i in range(barra_altura):
            progreso_local = 1.0 - i / barra_altura
            r = int(255 * (1 - progreso_local))
            g = int(255 * progreso_local)
            color = (0, g, r)
            cv2.line(overlay,
                     (barra_x, barra_y + i),
                     (barra_x + barra_ancho, barra_y + i),
                     color, 1)

        progreso_px = int((1.0 - self.progreso) * barra_altura)
        cv2.rectangle(overlay,
                      (barra_x - 2, barra_y + progreso_px - 2),
                      (barra_x + barra_ancho + 2, barra_y + progreso_px + 2),
                      (255, 255, 255), -1)

        # Mostrar mensaje guía
        if self.mensaje_guia:
            # Calcular el tamaño del texto para ajustarlo al espacio
            (text_width, text_height), baseline = cv2.getTextSize(self.mensaje_guia, cv2.FONT_HERSHEY_SIMPLEX, 2.0, 2)
            box_x, box_y = 45, 30

            # Ajustar el tamaño de la fuente si el texto es demasiado largo
            max_width = frame.shape[1] - 100  # Ancho máximo disponible para el texto
            if text_width > max_width:
                scale_factor = max_width / text_width  # Calcular un factor de escala
                font_scale = 2.0 * scale_factor  # Ajustar el tamaño de la fuente
            else:
                font_scale = 2.0  # Mantener el tamaño original de la fuente si cabe

            # Recalcular el tamaño del texto con el nuevo font_scale
            (text_width, text_height), baseline = cv2.getTextSize(self.mensaje_guia, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)

            # Dibujar fondo negro para el texto (opaco)
            cv2.rectangle(frame, (box_x - 10, box_y - 10), (box_x + text_width + 20, box_y + text_height + 20), (0, 0, 0), -1)

            # Dibujar el texto ajustado
            cv2.putText(frame, self.mensaje_guia, (box_x, box_y + text_height + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), 2, cv2.LINE_AA)

        return cv2.addWeighted(frame, 1, overlay, 0.7, 0)

