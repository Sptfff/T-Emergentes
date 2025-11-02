from .base import EjercicioBase
from utils.pose_utils import calcular_angulo
import cv2
import numpy as np

class SentadillaSumo(EjercicioBase):
    def __init__(self):
        super().__init__()
        self.estado_actual = "arriba"
        self.mensaje_guia = ""
        self.errores_contador = {
            "pies_juntos": 0,
            "espalda_inclinada": 0,
            "rodillas_no_abiertas": 0,
            "rodillas_no_alineadas": 0,
            "tobillos_no_apoyados": 0
        }
        self.error_flags = {key: False for key in self.errores_contador}

    def procesar_pose(self, landmarks):
        """
        Procesar pose con sistema de dos niveles:
        - SIEMPRE: Actualizar estado, progreso, repeticiones
        - CONDICIONAL: Detectar errores de forma
        """
        # ===== NIVEL 1: PROCESAMIENTO VISUAL (SIEMPRE) =====
        rodilla = (landmarks['RIGHT_KNEE'].x, landmarks['RIGHT_KNEE'].y)
        cadera = (landmarks['RIGHT_HIP'].x, landmarks['RIGHT_HIP'].y)
        tobillo = (landmarks['RIGHT_ANKLE'].x, landmarks['RIGHT_ANKLE'].y)

        # Calcular ángulo principal para estado y progreso
        angulo_rodilla = calcular_angulo(cadera, rodilla, tobillo)

        umbral_bajada = 105
        umbral_subida = 160

        nueva_repeticion = False
        mensajes = []

        # Flujo de repeticiones (SIEMPRE se verifica)
        if self.estado_actual == "arriba" and angulo_rodilla < umbral_bajada:
            self.estado_actual = "bajando"
            
        elif self.estado_actual == "bajando" and angulo_rodilla > umbral_subida:
            self.estado_actual = "arriba"
            self.repeticiones += 1
            msg_rep = "Buena repeticion!"
            mensajes.append(msg_rep)
            self.enviar_audio(msg_rep, es_error=False)
            nueva_repeticion = True

        # Actualizar progreso (SIEMPRE)
        self.progreso = (angulo_rodilla - umbral_bajada) / (umbral_subida - umbral_bajada)
        self.progreso = max(0.0, min(1.0, self.progreso))
        self.ultimo_angulo = angulo_rodilla

        # ===== NIVEL 2: DETECCIÓN DE ERRORES (CONDICIONAL) =====
        if self.debe_verificar_errores():
            # Solo ahora calculamos métricas adicionales
            hombro = (landmarks['RIGHT_SHOULDER'].x, landmarks['RIGHT_SHOULDER'].y)
            angulo_espalda = calcular_angulo(hombro, cadera, rodilla)
            distancia_pies = abs(landmarks['RIGHT_FOOT_INDEX'].x - landmarks['LEFT_FOOT_INDEX'].x)

            umbral_dist_pies = 0.20  # Más ancho que en la sentadilla normal
            umbral_rodillas_abiertas = 0.1  # Las rodillas no deben colapsar hacia adentro

            # Detección de errores con confirmación
            if self.validar_error_con_confirmacion(
                "pies_juntos",
                distancia_pies < umbral_dist_pies
            ):
                msg = "Abre mas los pies"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True)

            if self.validar_error_con_confirmacion(
                "espalda_inclinada",
                angulo_espalda < 70
            ):
                msg = "Manten la espalda recta"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True, critico=True)

            if self.validar_error_con_confirmacion(
                "rodillas_no_abiertas",
                rodilla[0] < tobillo[0] - umbral_rodillas_abiertas
            ):
                msg = "Empuja las rodillas afuera"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True, critico=True)

            if self.validar_error_con_confirmacion(
                "rodillas_no_alineadas",
                abs(rodilla[0] - tobillo[0]) > 0.1
            ):
                msg = "Alinea rodillas con pies"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True)

            if self.validar_error_con_confirmacion(
                "tobillos_no_apoyados",
                tobillo[1] > cadera[1] + 0.1
            ):
                msg = "Apoya bien los talones"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True)

        # Resetear flags si hay nueva repetición
        if nueva_repeticion:
            self.resetear_flags_errores()

        # Mensaje por defecto si no hay errores ni indicaciones
        if not mensajes and not self.mensaje_cache and self.estado_actual == "arriba":
            mensajes.append("Baja con control")

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

        # Nota: Barra de progreso y mensajes ahora se dibujan en la UI de Tkinter

        return cv2.addWeighted(frame, 1, overlay, 0.7, 0)
