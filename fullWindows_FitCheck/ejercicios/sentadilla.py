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
        
        # Configuración del sistema de fases
        self.fases_config = {
            "reposo_inicial": {
                "rango_progreso": (0.0, 0.0),
                "condicion_transicion": lambda ang, obj: ang < 155 and not obj.esta_en_reposo(),
                "siguiente_fase": "descendente",
                "mensaje": "Comienza a bajar"
            },
            "descendente": {
                "rango_progreso": (0.0, 0.5),
                "angulo_inicio": 160,
                "angulo_fin": 90,
                "condicion_transicion": lambda ang, obj: ang < 100,
                "siguiente_fase": "punto_bajo",
                "mensaje": "Continúa bajando"
            },
            "punto_bajo": {
                "rango_progreso": (0.5, 0.5),
                "condicion_transicion": lambda ang, obj: ang > 95 and not obj.esta_en_reposo(),
                "siguiente_fase": "ascendente",
                "mensaje": "¡Bien! Ahora sube"
            },
            "ascendente": {
                "rango_progreso": (0.5, 1.0),
                "angulo_inicio": 90,
                "angulo_fin": 160,
                "condicion_transicion": lambda ang, obj: ang > 155,
                "siguiente_fase": "completado",
                "mensaje": "Continúa subiendo"
            },
            "completado": {
                "rango_progreso": (1.0, 1.0),
                "condicion_transicion": lambda ang, obj: False,  # Reset manejado por delay automático
                "siguiente_fase": "reposo_inicial",
                "mensaje": "¡Repetición completa!"
            }
        }
        
        self.fase_actual = "reposo_inicial"
    
    def calcular_progreso_por_fase(self, angulo):
        """Calcula progreso visual basado en fase actual y ángulo"""
        fase = self.fases_config.get(self.fase_actual, {})
        rango = fase.get("rango_progreso", (0.0, 0.0))
        
        if self.fase_actual in ["reposo_inicial", "punto_bajo", "completado"]:
            # Fases estáticas
            return rango[0]
        
        elif self.fase_actual == "descendente":
            # Mapear ángulo 160→90 a progreso 0.0→0.5
            ang_inicio = fase.get("angulo_inicio", 160)
            ang_fin = fase.get("angulo_fin", 90)
            progreso_normalizado = (ang_inicio - angulo) / (ang_inicio - ang_fin)
            progreso_normalizado = max(0.0, min(1.0, progreso_normalizado))
            return rango[0] + (rango[1] - rango[0]) * progreso_normalizado
        
        elif self.fase_actual == "ascendente":
            # Mapear ángulo 90→160 a progreso 0.5→1.0
            ang_inicio = fase.get("angulo_inicio", 90)
            ang_fin = fase.get("angulo_fin", 160)
            progreso_normalizado = (angulo - ang_inicio) / (ang_fin - ang_inicio)
            progreso_normalizado = max(0.0, min(1.0, progreso_normalizado))
            return rango[0] + (rango[1] - rango[0]) * progreso_normalizado
        
        return 0.0

    def procesar_pose(self, landmarks):
        """
        Procesar pose con sistema de fases y detección de errores.
        Ahora usa el sistema de fases para un progreso más preciso.
        """
        # ===== NIVEL 1: PROCESAMIENTO VISUAL CON SISTEMA DE FASES =====
        rodilla = (landmarks['RIGHT_KNEE'].x, landmarks['RIGHT_KNEE'].y)
        cadera = (landmarks['RIGHT_HIP'].x, landmarks['RIGHT_HIP'].y)
        tobillo = (landmarks['RIGHT_ANKLE'].x, landmarks['RIGHT_ANKLE'].y)

        # Calcular ángulo principal
        angulo_rodilla = calcular_angulo(cadera, rodilla, tobillo)
        self.ultimo_angulo = angulo_rodilla
        
        mensajes = []

        # Actualizar fase y progreso usando el sistema de fases
        # Esto automáticamente maneja las transiciones y el incremento de repeticiones
        self.actualizar_fase_y_progreso(angulo_rodilla)

        # ===== NIVEL 2: DETECCIÓN DE ERRORES (CONDICIONAL) =====
        if self.debe_verificar_errores():
            # Solo ahora calculamos métricas adicionales
            hombro = (landmarks['RIGHT_SHOULDER'].x, landmarks['RIGHT_SHOULDER'].y)
            distancia_pies = abs(landmarks['RIGHT_FOOT_INDEX'].x - landmarks['LEFT_FOOT_INDEX'].x)
            angulo_espalda = calcular_angulo(hombro, cadera, rodilla)
            
            umbral_dist_pies = 0.12

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
                angulo_espalda < 70
            ):
                msg = "Manten la espalda recta"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True, critico=True)

            if self.validar_error_con_confirmacion(
                "tobillos_no_apoyados",
                tobillo[1] > cadera[1] + 0.1
            ):
                msg = "Apoya bien los tobillos"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True)

            if self.validar_error_con_confirmacion(
                "rodillas_hacia_adentro",
                rodilla[1] < tobillo[1]
            ):
                msg = "Evita que las rodillas se muevan hacia adentro"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True, critico=True)

            if self.validar_error_con_confirmacion(
                "rodillas_no_alineadas",
                abs(rodilla[0] - tobillo[0]) > 0.1
            ):
                msg = "Alinea tus rodillas con los pies"
                mensajes.append(msg)
                self.enviar_audio(msg, es_error=True)

        # Mensaje por defecto basado en la fase actual
        if not mensajes and not self.mensaje_cache:
            fase_config = self.fases_config.get(self.fase_actual, {})
            mensaje_fase = fase_config.get("mensaje", "")
            if mensaje_fase:
                mensajes.append(mensaje_fase)

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
