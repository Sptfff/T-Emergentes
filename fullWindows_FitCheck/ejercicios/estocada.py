from .base import EjercicioBase
from utils.pose_utils import calcular_angulo
import cv2
import numpy as np

class Estocada(EjercicioBase):
    def __init__(self):
        super().__init__()
        self.estado_actual = "arriba"
        self.mensaje_guia = ""
        self.errores_contador = {
            "pies_en_linea": 0,
            "rodilla_delantera_pasada": 0,
            "tronco_inclinado": 0,
            "tobillo_trasero_despegado": 0,
            "paso_corto": 0
        }
        # Flags para evitar múltiples conteos por repetición
        self.error_flags = {
            "pies_en_linea": False,
            "rodilla_delantera_pasada": False,
            "tronco_inclinado": False,
            "tobillo_trasero_despegado": False,
            "paso_corto": False
        }

    def procesar_pose(self, landmarks):
        rodilla_d = (landmarks['RIGHT_KNEE'].x, landmarks['RIGHT_KNEE'].y)
        cadera_d = (landmarks['RIGHT_HIP'].x, landmarks['RIGHT_HIP'].y)
        tobillo_d = (landmarks['RIGHT_ANKLE'].x, landmarks['RIGHT_ANKLE'].y)
        hombro_d = (landmarks['RIGHT_SHOULDER'].x, landmarks['RIGHT_SHOULDER'].y)

        rodilla_i = (landmarks['LEFT_KNEE'].x, landmarks['LEFT_KNEE'].y)
        cadera_i = (landmarks['LEFT_HIP'].x, landmarks['LEFT_HIP'].y)
        tobillo_i = (landmarks['LEFT_ANKLE'].x, landmarks['LEFT_ANKLE'].y)

        pie_d = landmarks['RIGHT_FOOT_INDEX']
        pie_i = landmarks['LEFT_FOOT_INDEX']

        angulo_delantero = calcular_angulo(cadera_d, rodilla_d, tobillo_d)
        angulo_trasero = calcular_angulo(cadera_i, rodilla_i, tobillo_i)
        angulo_espalda = calcular_angulo(hombro_d, cadera_d, rodilla_d)

        umbral_bajada = 100
        umbral_subida = 160

        mensajes = []
        nueva_repeticion = False

        # Flujo de repeticiones
        if self.estado_actual == "arriba" and angulo_delantero < umbral_bajada:
            self.estado_actual = "bajando"
        elif self.estado_actual == "bajando" and angulo_delantero > umbral_subida:
            self.estado_actual = "arriba"
            self.repeticiones += 1
            mensajes.append("Buena repeticion!")
            nueva_repeticion = True

        # Detección de errores (una vez por repetición)
        if abs(pie_d.x - pie_i.x) < 0.05 and not self.error_flags["pies_en_linea"]:
            self.errores_contador["pies_en_linea"] += 1
            self.error_flags["pies_en_linea"] = True
            mensajes.append("Separa los pies")

        if rodilla_d[0] > tobillo_d[0] + 0.05 and not self.error_flags["rodilla_delantera_pasada"]:
            self.errores_contador["rodilla_delantera_pasada"] += 1
            self.error_flags["rodilla_delantera_pasada"] = True
            mensajes.append("No dejes que la rodilla sobrepase el pie")

        if angulo_espalda < 70 and not self.error_flags["tronco_inclinado"]:
            self.errores_contador["tronco_inclinado"] += 1
            self.error_flags["tronco_inclinado"] = True
            mensajes.append("Manten el tronco mas recto")

        if tobillo_i[1] < cadera_i[1] - 0.05 and not self.error_flags["tobillo_trasero_despegado"]:
            self.errores_contador["tobillo_trasero_despegado"] += 1
            self.error_flags["tobillo_trasero_despegado"] = True
            mensajes.append("Apoya el pie trasero correctamente")
        # Medir distancia horizontal entre tobillo delantero y trasero
        distancia_pasos = abs(tobillo_d[0] - tobillo_i[0])
        if distancia_pasos < 0.15 and not self.error_flags["paso_corto"]:
            self.errores_contador["paso_corto"] += 1
            self.error_flags["paso_corto"] = True
            mensajes.append("Da un paso más largo para mejorar estabilidad y forma")

        if nueva_repeticion:
            for key in self.error_flags:
                self.error_flags[key] = False

        # Mensaje alternativo si no hay errores ni indicaciones y está arriba
        if not mensajes and self.estado_actual == "arriba":
            mensajes.append("Baja mas")

        self.mensaje_guia = " | ".join(mensajes)

        self.progreso = max(0.0, min(1.0, (angulo_delantero - umbral_bajada) / (umbral_subida - umbral_bajada)))
        self.ultimo_angulo = angulo_delantero

    def dibujar_feedback(self, frame, landmarks):
        height, width = frame.shape[:2]
        overlay = np.zeros_like(frame)

        def to_pixel(landmark):
            return int(landmark.x * width), int(landmark.y * height)

        # Pierna delantera
        cadera_px = to_pixel(landmarks['RIGHT_HIP'])
        rodilla_px = to_pixel(landmarks['RIGHT_KNEE'])
        tobillo_px = to_pixel(landmarks['RIGHT_ANKLE'])

        # Pierna trasera
        cadera_i_px = to_pixel(landmarks['LEFT_HIP'])
        rodilla_i_px = to_pixel(landmarks['LEFT_KNEE'])
        tobillo_i_px = to_pixel(landmarks['LEFT_ANKLE'])

        # Visualización pierna delantera
        cv2.fillPoly(overlay, [np.array([cadera_px, rodilla_px, tobillo_px])], (128, 0, 250))
        cv2.line(overlay, cadera_px, rodilla_px, (0, 255, 0), 6)
        cv2.line(overlay, rodilla_px, tobillo_px, (0, 255, 0), 6)
        cv2.circle(overlay, cadera_px, 8, (255, 0, 0), -1)
        cv2.circle(overlay, rodilla_px, 8, (0, 255, 255), -1)
        cv2.circle(overlay, tobillo_px, 8, (0, 0, 255), -1)

        # Visualización pierna trasera
        cv2.fillPoly(overlay, [np.array([cadera_i_px, rodilla_i_px, tobillo_i_px])], (240, 141, 46))
        cv2.line(overlay, cadera_i_px, rodilla_i_px, (255, 100, 0), 2)
        cv2.line(overlay, rodilla_i_px, tobillo_i_px, (255, 100, 0), 2)

        # Mostrar ángulo
        if hasattr(self, "ultimo_angulo"):
            cv2.putText(overlay, str(int(self.ultimo_angulo)),
                        (rodilla_i_px[0] + 10, rodilla_i_px[1] - 10),
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
            cv2.line(overlay, (barra_x, barra_y + i), (barra_x + barra_ancho, barra_y + i), color, 1)

        progreso_px = int((1.0 - self.progreso) * barra_altura)
        cv2.rectangle(overlay, (barra_x - 2, barra_y + progreso_px - 2),
                      (barra_x + barra_ancho + 2, barra_y + progreso_px + 2), (255, 255, 255), -1)

        # Mostrar mensaje guía
        if self.mensaje_guia:
            # Calcular el tamaño del texto para ajustarlo al espacio
            (text_width, text_height), baseline = cv2.getTextSize(self.mensaje_guia, cv2.FONT_HERSHEY_PLAIN, 2.0, 2)
            box_x, box_y = 45, 30

            # Ajustar el tamaño de la fuente si el texto es demasiado largo
            max_width = frame.shape[1] - 100  # Ancho máximo disponible para el texto
            if text_width > max_width:
                scale_factor = max_width / text_width  # Calcular un factor de escala
                font_scale = 2.0 * scale_factor  # Ajustar el tamaño de la fuente
            else:
                font_scale = 2.0  # Mantener el tamaño original de la fuente si cabe

            # Recalcular el tamaño del texto con el nuevo font_scale
            (text_width, text_height), baseline = cv2.getTextSize(self.mensaje_guia, cv2.FONT_HERSHEY_PLAIN, font_scale, 2)

            # Dibujar fondo negro para el texto (opaco)
            cv2.rectangle(frame, (box_x - 10, box_y - 10), (box_x + text_width + 20, box_y + text_height + 20), (0, 0, 0), -1)

            # Dibujar el texto ajustado
            cv2.putText(frame, self.mensaje_guia, (box_x, box_y + text_height + 5),
                        cv2.FONT_HERSHEY_PLAIN, font_scale, (0, 0, 255), 2, cv2.LINE_AA)


        return cv2.addWeighted(frame, 1, overlay, 0.7, 0)
