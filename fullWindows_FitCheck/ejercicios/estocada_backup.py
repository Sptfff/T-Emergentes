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
        """
        Procesar pose con sistema de dos niveles:
        - SIEMPRE: Actualizar estado, progreso, repeticiones
        - CONDICIONAL: Detectar errores de forma
        """
        # ===== NIVEL 1: PROCESAMIENTO VISUAL (SIEMPRE) =====
        rodilla_d = (landmarks['RIGHT_KNEE'].x, landmarks['RIGHT_KNEE'].y)
        cadera_d = (landmarks['RIGHT_HIP'].x, landmarks['RIGHT_HIP'].y)
        tobillo_d = (landmarks['RIGHT_ANKLE'].x, landmarks['RIGHT_ANKLE'].y)

        # Calcular ángulo principal para estado y progreso
        angulo_delantero = calcular_angulo(cadera_d, rodilla_d, tobillo_d)
        
        umbral_bajada = 100
        umbral_subida = 160

        mensajes = []
        nueva_repeticion = False

        # Flujo de repeticiones (SIEMPRE se verifica)
        if self.estado_actual == "arriba" and angulo_delantero < umbral_bajada:
            self.estado_actual = "bajando"
        elif self.estado_actual == "bajando" and angulo_delantero > umbral_subida:
            self.estado_actual = "arriba"
            self.repeticiones += 1
            msg_rep = "Buena repeticion!"
            mensajes.append(msg_rep)
            self.enviar_audio(msg_rep, es_error=False)
            nueva_repeticion = True

        # Actualizar progreso (SIEMPRE)
        self.progreso = max(0.0, min(1.0, (angulo_delantero - umbral_bajada) / (umbral_subida - umbral_bajada)))
        self.ultimo_angulo = angulo_delantero

        # ===== NIVEL 2: DETECCIÓN DE ERRORES (CONDICIONAL) =====
        if self.debe_verificar_errores():
            # Solo ahora calculamos métricas adicionales
            hombro_d = (landmarks['RIGHT_SHOULDER'].x, landmarks['RIGHT_SHOULDER'].y)
            rodilla_i = (landmarks['LEFT_KNEE'].x, landmarks['LEFT_KNEE'].y)
            cadera_i = (landmarks['LEFT_HIP'].x, landmarks['LEFT_HIP'].y)
            tobillo_i = (landmarks['LEFT_ANKLE'].x, landmarks['LEFT_ANKLE'].y)
            pie_d = landmarks['RIGHT_FOOT_INDEX']
            pie_i = landmarks['LEFT_FOOT_INDEX']
            
            angulo_espalda = calcular_angulo(hombro_d, cadera_d, rodilla_d)
            distancia_pasos = abs(tobillo_d[0] - tobillo_i[0])

            # Detección de errores con confirmación
            if self.validar_error_con_confirmacion(
                "pies_en_linea",
                abs(pie_d.x - pie_i.x) < 0.05
            ):
                msg = "Separa los pies"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True)

            if self.validar_error_con_confirmacion(
                "rodilla_delantera_pasada",
                rodilla_d[0] > tobillo_d[0] + 0.05
            ):
                msg = "No dejes que la rodilla sobrepase el pie"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True, critico=True)

            if self.validar_error_con_confirmacion(
                "tronco_inclinado",
                angulo_espalda < 70
            ):
                msg = "Manten el tronco mas recto"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True)

            if self.validar_error_con_confirmacion(
                "tobillo_trasero_despegado",
                tobillo_i[1] < cadera_i[1] - 0.05
            ):
                msg = "Apoya el pie trasero correctamente"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True)

            if self.validar_error_con_confirmacion(
                "paso_corto",
                distancia_pasos < 0.15
            ):
                msg = "Da un paso más largo"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True)

        # Resetear flags si hay nueva repetición
        if nueva_repeticion:
            self.resetear_flags_errores()

        # Mensaje por defecto si no hay errores ni indicaciones
        if not mensajes and not self.mensaje_cache and self.estado_actual == "arriba":
            mensajes.append("Baja mas")

        # Actualizar mensaje con sistema de cache
        self.actualizar_mensaje_guia(mensajes if mensajes else None)

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

        # Nota: Barra de progreso y mensajes ahora se dibujan en la UI de Tkinter

        return cv2.addWeighted(frame, 1, overlay, 0.7, 0)
        return cv2.addWeighted(frame, 1, overlay, 0.7, 0)
