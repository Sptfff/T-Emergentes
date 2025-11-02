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
        altura_cadera = cadera[1]

        umbral_bajada = 90
        umbral_subida = 160
        umbral_salto = 0.05

        mensajes = []
        nueva_repeticion = False

        # Flujo de repeticiones (SIEMPRE se verifica)
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
                msg_rep = "Buen salto!"
                mensajes.append(msg_rep)
                self.enviar_audio(msg_rep, es_error=False)
                nueva_repeticion = True
            self.en_salto = False
            self.estado_actual = "arriba"

        # ===== NIVEL 2: DETECCIÓN DE ERRORES (CONDICIONAL) =====
        if self.debe_verificar_errores():
            # Solo ahora calculamos métricas adicionales
            hombro = (landmarks['RIGHT_SHOULDER'].x, landmarks['RIGHT_SHOULDER'].y)
            angulo_espalda = calcular_angulo(hombro, cadera, rodilla)
            distancia_pies = abs(landmarks['RIGHT_FOOT_INDEX'].x - landmarks['LEFT_FOOT_INDEX'].x)

            umbral_dist_pies = 0.12
            umbral_espalda = 70

            # Detección de errores con confirmación
            if self.validar_error_con_confirmacion(
                "pies_juntos",
                distancia_pies < umbral_dist_pies
            ):
                msg = "Separa los pies"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True)

            if self.validar_error_con_confirmacion(
                "espalda_inclinada",
                angulo_espalda < umbral_espalda
            ):
                msg = "Manten la espalda recta"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True, critico=True)

            if self.validar_error_con_confirmacion(
                "rodillas_hacia_adentro",
                rodilla[0] < tobillo[0] - 0.07
            ):
                msg = "Rodillas hacia adentro"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True, critico=True)

            # Validar que realmente saltó al completar la repetición
            if self.estado_actual == "subiendo" and not self.en_salto:
                if self.validar_error_con_confirmacion("sin_salto", True):
                    msg = "Debes saltar"
                    mensajes.append(msg)
                    self.enviar_audio(msg, es_error=True)

            if self.validar_error_con_confirmacion(
                "salto_insuficiente",
                self.en_salto and self.altura_max_salto - altura_cadera < umbral_salto
            ):
                msg = "Salta mas alto"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True)

        # Resetear flags si hay nueva repetición
        if nueva_repeticion:
            self.resetear_flags_errores()

        # Mensaje por defecto si no hay errores ni indicaciones
        if not mensajes and not self.mensaje_cache and self.estado_actual == "arriba":
            mensajes.append("Baja y salta")

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

