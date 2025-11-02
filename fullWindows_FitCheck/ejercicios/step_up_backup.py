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
        """
        Procesar pose con sistema de dos niveles:
        - SIEMPRE: Actualizar estado, progreso, repeticiones
        - CONDICIONAL: Detectar errores de forma
        """
        # ===== NIVEL 1: PROCESAMIENTO VISUAL (SIEMPRE) =====
        cadera_d = (landmarks['RIGHT_HIP'].x, landmarks['RIGHT_HIP'].y)
        rodilla_d = (landmarks['RIGHT_KNEE'].x, landmarks['RIGHT_KNEE'].y)
        tobillo_d = (landmarks['RIGHT_ANKLE'].x, landmarks['RIGHT_ANKLE'].y)

        # Calcular ángulo principal para estado y progreso
        angulo_delantera = calcular_angulo(cadera_d, rodilla_d, tobillo_d)

        umbral_subida = 100
        umbral_bajada = 160

        mensajes = []
        nueva_repeticion = False

        # Flujo de repeticiones (SIEMPRE se verifica)
        if self.estado_actual == "abajo" and angulo_delantera < umbral_subida:
            self.estado_actual = "subiendo"
            mensajes.append("Buen impulso! Manten el equilibrio")

        elif self.estado_actual == "subiendo" and angulo_delantera > umbral_bajada:
            self.estado_actual = "arriba"
            mensajes.append("Excelente! Ahora baja controladamente")

        elif self.estado_actual == "arriba" and angulo_delantera < umbral_subida:
            self.estado_actual = "bajando"
            mensajes.append("Controla la bajada")

        elif self.estado_actual == "bajando" and angulo_delantera > umbral_bajada:
            self.estado_actual = "abajo"
            self.repeticiones += 1
            nueva_repeticion = True
            msg_rep = "Repeticion completada!"
            mensajes.append(msg_rep)
            self.enviar_audio(msg_rep, es_error=False)

        # Actualizar progreso (SIEMPRE)
        self.progreso = max(0.0, min(1.0, (angulo_delantera - umbral_subida) / (umbral_bajada - umbral_subida)))
        self.ultimo_angulo = angulo_delantera

        # ===== NIVEL 2: DETECCIÓN DE ERRORES (CONDICIONAL) =====
        if self.debe_verificar_errores():
            # Solo ahora calculamos métricas adicionales
            cadera_i = (landmarks['LEFT_HIP'].x, landmarks['LEFT_HIP'].y)
            tobillo_i = (landmarks['LEFT_ANKLE'].x, landmarks['LEFT_ANKLE'].y)
            pie_i = landmarks['LEFT_FOOT_INDEX']

            # Detección de errores con confirmación
            if self.validar_error_con_confirmacion(
                "rodilla_delantera_pasada",
                rodilla_d[0] > tobillo_d[0] + 0.05
            ):
                msg = "No dejes que la rodilla pase el pie"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True, critico=True)

            if self.validar_error_con_confirmacion(
                "equilibrio_inestable",
                abs(pie_i.y - tobillo_i[1]) < 0.1
            ):
                msg = "Manten el equilibrio"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True)

            if self.validar_error_con_confirmacion(
                "pierna_trasera_sin_apoyo",
                tobillo_i[1] < cadera_i[1] - 0.05
            ):
                msg = "Apoya la pierna trasera"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True)

            if self.validar_error_con_confirmacion(
                "angulo_rodilla_excesivo",
                angulo_delantera < 90
            ):
                msg = "Evita un angulo muy agudo"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True, critico=True)

            if self.validar_error_con_confirmacion(
                "pie_trasero_no_apoyado",
                abs(pie_i.y - tobillo_i[1]) > 0.3
            ):
                msg = "Apoya el pie trasero"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True)

        # Resetear flags si hay nueva repetición
        if nueva_repeticion:
            self.resetear_flags_errores()

        # Mensaje por defecto si no hay errores ni indicaciones
        if not mensajes and not self.mensaje_cache and self.estado_actual == "abajo":
            mensajes.append("Baja controladamente")

        # Actualizar mensaje con sistema de cache
        self.actualizar_mensaje_guia(mensajes if mensajes else None)

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

        # Nota: Barra de progreso y mensajes ahora se dibujan en la UI de Tkinter

        return cv2.addWeighted(frame, 1, overlay, 0.6, 0)
