from .base import EjercicioBase 
from utils.pose_utils import calcular_angulo
import cv2
import numpy as np

class StepUp(EjercicioBase):
    def __init__(self):
        super().__init__()
        self.estado_actual = "abajo"
        self.mensaje_guia = ""
        self.errores_contador = {
            "rodilla_delantera_pasada": 0,
            "equilibrio_inestable": 0,
            "pierna_trasera_sin_apoyo": 0,
            "angulo_rodilla_excesivo": 0,
            "pie_trasero_no_apoyado": 0
        }
        self.error_flags = {key: False for key in self.errores_contador}

    def procesar_pose(self, landmarks):
        cadera_d = (landmarks['RIGHT_HIP'].x, landmarks['RIGHT_HIP'].y)
        rodilla_d = (landmarks['RIGHT_KNEE'].x, landmarks['RIGHT_KNEE'].y)
        tobillo_d = (landmarks['RIGHT_ANKLE'].x, landmarks['RIGHT_ANKLE'].y)

        cadera_i = (landmarks['LEFT_HIP'].x, landmarks['LEFT_HIP'].y)
        rodilla_i = (landmarks['LEFT_KNEE'].x, landmarks['LEFT_KNEE'].y)
        tobillo_i = (landmarks['LEFT_ANKLE'].x, landmarks['LEFT_ANKLE'].y)

        angulo_delantera = calcular_angulo(cadera_d, rodilla_d, tobillo_d)
        angulo_trasera = calcular_angulo(cadera_i, rodilla_i, tobillo_i)

        umbral_subida = 100
        umbral_bajada = 160

        mensajes = []
        nueva_repeticion = False

        # Flujo de repeticiones con estados: abajo → subiendo → arriba → bajando → abajo
        if self.estado_actual == "abajo" and angulo_delantera < umbral_subida:
            self.estado_actual = "subiendo"
            self.mensaje_guia = "Buen impulso! Manten el equilibrio"

        elif self.estado_actual == "subiendo" and angulo_delantera > umbral_bajada:
            self.estado_actual = "arriba"
            self.mensaje_guia = "Excelente! Ahora baja controladamente"

        elif self.estado_actual == "arriba" and angulo_delantera < umbral_subida:
            self.estado_actual = "bajando"
            self.mensaje_guia = "Controla la bajada"

        elif self.estado_actual == "bajando" and angulo_delantera > umbral_bajada:
            self.estado_actual = "abajo"
            self.repeticiones += 1
            nueva_repeticion = True
            self.mensaje_guia = "Repeticion completada!"

        # Detección de errores
        if rodilla_d[0] > tobillo_d[0] + 0.05 and not self.error_flags["rodilla_delantera_pasada"]:
            self.errores_contador["rodilla_delantera_pasada"] += 1
            self.error_flags["rodilla_delantera_pasada"] = True
            mensajes.append("No dejes que la rodilla pase el pie")

        if abs(landmarks['LEFT_FOOT_INDEX'].y - tobillo_i[1]) < 0.1 and not self.error_flags["equilibrio_inestable"]:
            self.errores_contador["equilibrio_inestable"] += 1
            self.error_flags["equilibrio_inestable"] = True
            mensajes.append("Manten el equilibrio")

        if tobillo_i[1] < cadera_i[1] - 0.05 and not self.error_flags["pierna_trasera_sin_apoyo"]:
            self.errores_contador["pierna_trasera_sin_apoyo"] += 1
            self.error_flags["pierna_trasera_sin_apoyo"] = True
            mensajes.append("Apoya completamente la pierna trasera")

        if angulo_delantera < 90 and not self.error_flags["angulo_rodilla_excesivo"]:
            self.errores_contador["angulo_rodilla_excesivo"] += 1
            self.error_flags["angulo_rodilla_excesivo"] = True
            mensajes.append("Evita un angulo demasiado agudo de rodilla")

        if abs(landmarks['LEFT_FOOT_INDEX'].y - tobillo_i[1]) > 0.3 and not self.error_flags["pie_trasero_no_apoyado"]:
            self.errores_contador["pie_trasero_no_apoyado"] += 1
            self.error_flags["pie_trasero_no_apoyado"] = True
            mensajes.append("Apoya el pie trasero en el suelo")

        if nueva_repeticion:
            self.error_flags = {key: False for key in self.error_flags}

        if not mensajes and self.estado_actual == "abajo":
            mensajes.append("Baja controladamente")

        self.mensaje_guia = " | ".join(mensajes)
        self.progreso = max(0.0, min(1.0, (angulo_delantera - umbral_subida) / (umbral_bajada - umbral_subida)))
        self.ultimo_angulo = angulo_delantera

    def dibujar_feedback(self, frame, landmarks):
        height, width = frame.shape[:2]
        overlay = np.zeros_like(frame)

        def to_pixel(landmark):
            return int(landmark.x * width), int(landmark.y * height)

        cadera_px = to_pixel(landmarks['RIGHT_HIP'])
        rodilla_px = to_pixel(landmarks['RIGHT_KNEE'])
        tobillo_px = to_pixel(landmarks['RIGHT_ANKLE'])

        # Triángulo del ángulo de la pierna delantera
        triangle_cnt = np.array([cadera_px, rodilla_px, tobillo_px], dtype=np.int32)
        cv2.fillPoly(overlay, [triangle_cnt], color=(200, 255, 255))
        cv2.polylines(overlay, [triangle_cnt], isClosed=True, color=(0, 100, 200), thickness=2)

        cv2.line(overlay, cadera_px, rodilla_px, (0, 255, 0), 6)
        cv2.line(overlay, rodilla_px, tobillo_px, (0, 255, 0), 6)
        cv2.circle(overlay, cadera_px, 8, (255, 0, 0), -1)
        cv2.circle(overlay, rodilla_px, 8, (0, 255, 255), -1)
        cv2.circle(overlay, tobillo_px, 8, (0, 0, 255), -1)

        # Pierna trasera
        cadera_i_px = to_pixel(landmarks['LEFT_HIP'])
        rodilla_i_px = to_pixel(landmarks['LEFT_KNEE'])
        tobillo_i_px = to_pixel(landmarks['LEFT_ANKLE'])

        cv2.line(overlay, cadera_i_px, rodilla_i_px, (255, 100, 0), 2)
        cv2.line(overlay, rodilla_i_px, tobillo_i_px, (255, 100, 0), 2)

        if hasattr(self, "ultimo_angulo"):
            cv2.putText(overlay, str(int(self.ultimo_angulo)),
                        (rodilla_px[0] + 10, rodilla_px[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

        barra_altura = int(height * 0.6)
        barra_ancho = 30
        barra_x = width - 50
        barra_y = int(height * 0.2)

        for i in range(barra_altura):
            progreso_local = 1.0 - i / barra_altura
            r = int(255 * (1 - progreso_local))
            g = int(255 * progreso_local)
            color = (0, g, r)
            cv2.line(overlay, (barra_x, barra_y + i), (barra_x + barra_ancho, barra_y + i), color, 1)

        progreso_px = int((1.0 - self.progreso) * barra_altura)
        cv2.rectangle(overlay, (barra_x - 2, barra_y + progreso_px - 2),
                      (barra_x + barra_ancho + 2, barra_y + progreso_px + 2), (255, 255, 255), -1)

        if self.mensaje_guia:
            (text_width, text_height), baseline = cv2.getTextSize(self.mensaje_guia, cv2.FONT_HERSHEY_PLAIN, 2.0, 2)
            box_x, box_y = 45, 30
            max_width = frame.shape[1] - 100
            font_scale = 2.0 * min(1.0, max_width / text_width) if text_width > max_width else 2.0
            (text_width, text_height), _ = cv2.getTextSize(self.mensaje_guia, cv2.FONT_HERSHEY_PLAIN, font_scale, 2)
            cv2.rectangle(frame, (box_x - 10, box_y - 10), (box_x + text_width + 20, box_y + text_height + 20), (0, 0, 0), -1)
            cv2.putText(frame, self.mensaje_guia, (box_x, box_y + text_height + 5),
                        cv2.FONT_HERSHEY_PLAIN, font_scale, (0, 0, 255), 2, cv2.LINE_AA)

        return cv2.addWeighted(frame, 1, overlay, 0.6, 0)
