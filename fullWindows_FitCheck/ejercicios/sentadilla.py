from .base import EjercicioBase
from utils.pose_utils import calcular_angulo
import cv2
import numpy as np

class Sentadilla(EjercicioBase):
    def __init__(self):
        super().__init__()
        self.estado_actual = "arriba"
        self.mensaje_guia = ""
        self.errores_contador = {
            "pies_juntos": 0,
            "espalda_inclinada": 0,
            "tobillos_no_apoyados": 0,
            "rodillas_hacia_adentro": 0,
            "rodillas_no_alineadas": 0
        }
        # Flags para evitar múltiples conteos por repetición
        self.error_flags = {
            "pies_juntos": False,
            "espalda_inclinada": False,
            "tobillos_no_apoyados": False,
            "rodillas_hacia_adentro": False,
            "rodillas_no_alineadas": False
        }

    def procesar_pose(self, landmarks):
        rodilla = (landmarks['RIGHT_KNEE'].x, landmarks['RIGHT_KNEE'].y)
        cadera = (landmarks['RIGHT_HIP'].x, landmarks['RIGHT_HIP'].y)
        tobillo = (landmarks['RIGHT_ANKLE'].x, landmarks['RIGHT_ANKLE'].y)
        hombro = (landmarks['RIGHT_SHOULDER'].x, landmarks['RIGHT_SHOULDER'].y)

        angulo_rodilla = calcular_angulo(cadera, rodilla, tobillo)
        distancia_pies = abs(landmarks['RIGHT_FOOT_INDEX'].x - landmarks['LEFT_FOOT_INDEX'].x)
        umbral_dist_pies = 0.12

        umbral_bajada = 90
        umbral_subida = 160

        angulo_espalda = calcular_angulo(hombro, cadera, rodilla)

        mensajes = []
        nueva_repeticion = False

        # Flujo de repeticiones
        if self.estado_actual == "arriba" and angulo_rodilla < umbral_bajada:
            self.estado_actual = "bajando"
        elif self.estado_actual == "bajando" and angulo_rodilla > umbral_subida:
            self.estado_actual = "arriba"
            self.repeticiones += 1
            mensajes.append("Buena repeticion!")
            nueva_repeticion = True

        # Detección de errores (una vez por repetición)
        if distancia_pies < umbral_dist_pies and not self.error_flags["pies_juntos"]:
            self.errores_contador["pies_juntos"] += 1
            self.error_flags["pies_juntos"] = True
            mensajes.append("Separa los pies")

        if angulo_espalda < 70 and not self.error_flags["espalda_inclinada"]:
            self.errores_contador["espalda_inclinada"] += 1
            self.error_flags["espalda_inclinada"] = True
            mensajes.append("Manten la espalda recta")

        if tobillo[1] > cadera[1] + 0.1 and not self.error_flags["tobillos_no_apoyados"]:
            self.errores_contador["tobillos_no_apoyados"] += 1
            self.error_flags["tobillos_no_apoyados"] = True
            mensajes.append("Apoya bien los tobillos")

        # Rodillas hacia adentro
        if rodilla[1] < tobillo[1] and not self.error_flags["rodillas_hacia_adentro"]:
            self.errores_contador["rodillas_hacia_adentro"] += 1
            self.error_flags["rodillas_hacia_adentro"] = True
            mensajes.append("Evita que las rodillas se muevan hacia adentro")

        # Alineación de rodillas con los pies
        if abs(rodilla[0] - tobillo[0]) > 0.1 and not self.error_flags["rodillas_no_alineadas"]:
            self.errores_contador["rodillas_no_alineadas"] += 1
            self.error_flags["rodillas_no_alineadas"] = True
            mensajes.append("Alinea tus rodillas con los pies")

        if nueva_repeticion:
            for key in self.error_flags:
                self.error_flags[key] = False

        # Mensaje alternativo si no hay errores ni indicaciones y está arriba
        if not mensajes and self.estado_actual == "arriba":
            mensajes.append("Baja mas")

        self.mensaje_guia = " | ".join(mensajes)

        self.progreso = (angulo_rodilla - umbral_bajada) / (umbral_subida - umbral_bajada)
        self.progreso = max(0.0, min(1.0, self.progreso))
        self.ultimo_angulo = angulo_rodilla

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
