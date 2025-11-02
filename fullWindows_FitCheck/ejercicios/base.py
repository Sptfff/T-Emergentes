"""
Clase base para todos los ejercicios
Proporciona funcionalidad común y métodos abstractos
"""
import cv2
import numpy as np
import time
from typing import Optional
from utils.logger import get_logger
from config import (
    ERROR_CHECK_INTERVAL, 
    ERROR_CONFIRMATION_FRAMES, 
    MENSAJE_ERROR_TTL,
    AUDIO_HABILITADO,
    AUDIO_SOLO_ERRORES,
    AUDIO_PRIORIDAD_MINIMA
)

logger = get_logger()

class EjercicioBase:
    def __init__(self):
        self.repeticiones = 0
        self.estado_actual = None  # Por ejemplo, "bajando" o "subiendo"
        self.progreso = 0.0        # Para barra de progreso (0 a 1)
        self.mensaje_guia = ""
        self.errores_contador = {}
        self.error_flags = {}
        self.ultimo_angulo = 0
        
        # Sistema de fases (nuevo)
        self.fase_actual = "reposo_inicial"
        self.fases_config = {}  # Definido por cada ejercicio específico
        self.progreso_fase = 0.0  # Progreso dentro de la fase actual (0.0-1.0)
        self.historial_angulos = []  # Para detectar reposo/movimiento
        self.velocidad_movimiento = 0.0
        self.umbral_reposo = 3.0  # grados/frame para considerar reposo
        self.tiempo_completado = None  # Timestamp cuando se alcanza 100%
        self.delay_completado = 0.7  # Segundos de delay en 100% antes de resetear
        
        # Nuevos atributos para control de frecuencia de detección
        self.frame_counter = 0
        self.error_check_interval = ERROR_CHECK_INTERVAL
        self.error_confirmation_frames = ERROR_CONFIRMATION_FRAMES
        
        # Cache de mensajes para mantener visibilidad entre frames
        self.mensaje_cache = ""
        self.timestamp_mensaje = 0
        self.mensaje_ttl = MENSAJE_ERROR_TTL
        
        # Contador de detecciones consecutivas por tipo de error
        self.errores_consecutivos = {}
        
        # Gestor de audio (se asigna desde entrenamiento.py)
        self.audio_manager: Optional['AudioManager'] = None

    def procesar_pose(self, landmarks):
        """
        Procesar landmarks recibidos y actualizar el estado del ejercicio,
        progreso y repeticiones.
        
        SISTEMA DE DOS NIVELES:
        - Procesamiento visual: SIEMPRE (cada frame)
        - Detección de errores: CONDICIONAL (cada N frames)
        
        Este método debe ser implementado por cada ejercicio específico.
        """
        raise NotImplementedError("Debe implementar procesar_pose en la subclase")
    
    def debe_verificar_errores(self):
        """
        Determina si en este frame se deben verificar errores
        
        Returns:
            bool: True si corresponde verificar errores en este frame
        """
        self.frame_counter += 1
        return self.frame_counter % self.error_check_interval == 0
    
    def actualizar_mensaje_guia(self, nuevos_mensajes):
        """
        Actualiza el mensaje guía con cache y TTL
        
        Args:
            nuevos_mensajes: Lista de mensajes nuevos o None
        """
        ahora = time.time()
        
        if nuevos_mensajes:
            # Hay mensajes nuevos, actualizar cache
            self.mensaje_cache = " | ".join(nuevos_mensajes)
            self.timestamp_mensaje = ahora
            self.mensaje_guia = self.mensaje_cache
        else:
            # No hay mensajes nuevos, usar cache si no ha expirado
            if ahora - self.timestamp_mensaje < self.mensaje_ttl:
                self.mensaje_guia = self.mensaje_cache
            else:
                # Cache expirado, limpiar mensaje
                self.mensaje_guia = ""
                self.mensaje_cache = ""
    
    def validar_error_con_confirmacion(self, tipo_error, condicion):
        """
        Valida un error con confirmación de múltiples frames consecutivos
        Esto evita falsos positivos por movimientos momentáneos
        
        Args:
            tipo_error: Identificador del tipo de error
            condicion: Booleano indicando si la condición de error se cumple
            
        Returns:
            bool: True si el error debe ser reportado
        """
        # Inicializar contador si no existe
        if tipo_error not in self.errores_consecutivos:
            self.errores_consecutivos[tipo_error] = 0
        
        if condicion and not self.error_flags.get(tipo_error, False):
            # Error detectado, incrementar contador
            self.errores_consecutivos[tipo_error] += 1
            
            # Verificar si alcanzamos el umbral de confirmación
            if self.errores_consecutivos[tipo_error] >= self.error_confirmation_frames:
                # Error confirmado
                self.error_flags[tipo_error] = True
                if tipo_error in self.errores_contador:
                    self.errores_contador[tipo_error] += 1
                return True
        else:
            # No hay error o ya está marcado, resetear contador
            self.errores_consecutivos[tipo_error] = 0
        
        return False
    
    def resetear_flags_errores(self):
        """
        Resetea los flags de errores (típicamente al completar una repetición)
        """
        for key in self.error_flags:
            self.error_flags[key] = False
    
    def calcular_velocidad_movimiento(self, angulo_actual):
        """
        Calcula velocidad de cambio del ángulo principal.
        Útil para detectar estados de reposo vs movimiento activo.
        
        Args:
            angulo_actual: Ángulo actual en grados
            
        Returns:
            float: Velocidad promedio de cambio (grados/frame)
        """
        self.historial_angulos.append(angulo_actual)
        
        # Mantener solo los últimos 10 frames
        if len(self.historial_angulos) > 10:
            self.historial_angulos.pop(0)
        
        # Necesitamos al menos 3 valores para calcular velocidad
        if len(self.historial_angulos) >= 3:
            # Calcular cambios absolutos entre frames consecutivos
            cambios = [
                abs(self.historial_angulos[i] - self.historial_angulos[i-1])
                for i in range(1, len(self.historial_angulos))
            ]
            self.velocidad_movimiento = sum(cambios) / len(cambios)
        
        return self.velocidad_movimiento
    
    def esta_en_reposo(self):
        """
        Determina si la persona está en reposo basándose en la velocidad de movimiento.
        
        Returns:
            bool: True si está en reposo, False si está en movimiento
        """
        return self.velocidad_movimiento < self.umbral_reposo
    
    def actualizar_fase_y_progreso(self, angulo_principal):
        """
        Sistema de fases: Actualiza la fase actual y el progreso total
        basándose en las transiciones definidas en fases_config.
        
        Este método debe ser llamado en cada frame desde procesar_pose().
        
        Args:
            angulo_principal: Ángulo principal del ejercicio (ej: rodilla)
            
        Returns:
            float: Progreso total de la repetición (0.0-1.0)
        """
        # Actualizar velocidad de movimiento
        self.calcular_velocidad_movimiento(angulo_principal)
        
        # Obtener configuración de la fase actual
        fase_config = self.fases_config.get(self.fase_actual, {})
        condicion_transicion = fase_config.get("condicion_transicion")
        
        # Si estamos en fase "completado", manejar el delay
        if self.fase_actual == "completado":
            if self.tiempo_completado is None:
                # Primera vez que llegamos a completado, marcar timestamp
                self.tiempo_completado = time.time()
                logger.info(f"Repetición completada! Total: {self.repeticiones}")
                
                # Enviar audio de repetición completada
                if hasattr(self, 'audio_manager') and self.audio_manager:
                    self.enviar_audio("Buena repeticion!", es_error=False)
            
            # Verificar si ha pasado el delay
            tiempo_transcurrido = time.time() - self.tiempo_completado
            if tiempo_transcurrido >= self.delay_completado:
                # Delay completado, resetear a reposo_inicial
                logger.info(f"Reset a reposo_inicial después de {tiempo_transcurrido:.2f}s")
                self.fase_actual = "reposo_inicial"
                self.tiempo_completado = None
                self.resetear_flags_errores()
        else:
            # No estamos en completado, resetear el timestamp
            self.tiempo_completado = None
            
            # Evaluar si debe cambiar de fase
            if condicion_transicion and condicion_transicion(angulo_principal, self):
                siguiente_fase = fase_config.get("siguiente_fase")
                if siguiente_fase:
                    logger.info(f"Transición de fase: {self.fase_actual} → {siguiente_fase}")
                    
                    # Si la siguiente fase es "completado", incrementar repeticiones
                    if siguiente_fase == "completado":
                        self.repeticiones += 1
                    
                    self.fase_actual = siguiente_fase
        
        # Calcular progreso visual según la fase actual
        self.progreso = self.calcular_progreso_por_fase(angulo_principal)
        
        # Actualizar mensaje guía según la fase
        mensaje_fase = fase_config.get("mensaje", "")
        if mensaje_fase and not self.mensaje_cache:
            self.mensaje_guia = mensaje_fase
        
        return self.progreso
    
    def calcular_progreso_por_fase(self, angulo):
        """
        Calcula el progreso visual basándose en la fase actual.
        Este método debe ser sobrescrito por cada ejercicio específico.
        
        Args:
            angulo: Ángulo principal del ejercicio
            
        Returns:
            float: Progreso entre 0.0 y 1.0
        """
        # Implementación por defecto (lineal simple)
        fase = self.fases_config.get(self.fase_actual, {})
        rango = fase.get("rango_progreso", (0.0, 0.0))
        
        # Si es una fase estática (reposo, punto_bajo, completado)
        if rango[0] == rango[1]:
            return rango[0]
        
        # Si es una fase dinámica, necesita información de ángulos
        # Esto debe ser implementado por cada ejercicio
        return rango[0]

        # También resetear contadores de confirmación
        for key in self.errores_consecutivos:
            self.errores_consecutivos[key] = 0
    
    def set_audio_manager(self, audio_manager):
        """
        Asignar gestor de audio al ejercicio.
        
        Args:
            audio_manager: Instancia de AudioManager
        """
        self.audio_manager = audio_manager
    
    def enviar_audio(self, texto: str, es_error: bool = False, critico: bool = False):
        """
        Enviar mensaje de audio si el sistema está habilitado.
        
        Args:
            texto: Texto a reproducir
            es_error: Si es un mensaje de error (mayor prioridad)
            critico: Si es crítico (solo aplica si es_error=True)
        """
        if not self.audio_manager or not AUDIO_HABILITADO:
            return
        
        # Determinar prioridad
        if es_error:
            prioridad = self.audio_manager.PRIORIDAD_CRITICA if critico else self.audio_manager.PRIORIDAD_ALTA
            categoria = "error"
        else:
            prioridad = self.audio_manager.PRIORIDAD_MEDIA
            categoria = "guia"
        
        # Filtrar según configuración
        if AUDIO_SOLO_ERRORES and not es_error:
            return
        
        if prioridad > AUDIO_PRIORIDAD_MINIMA:
            return
        
        # Enviar mensaje
        self.audio_manager.agregar_mensaje(texto, prioridad, categoria)

    def get_repeticiones(self):
        return self.repeticiones

    def get_progreso(self):
        return self.progreso
    
    def dibujar_barra_progreso(self, frame, overlay, progreso):
        """
        Dibuja barra de progreso lateral tipo "relleno" (contorno + relleno de color)
        
        Args:
            frame: Frame de OpenCV
            overlay: Overlay transparente
            progreso: Valor entre 0.0 y 1.0
        """
        height, width = frame.shape[:2]
        
        barra_altura = int(height * 0.6)
        barra_ancho = 30
        barra_x = width - 50
        barra_y = int(height * 0.2)
        
        # Dibujar contorno de la barra (blanco)
        cv2.rectangle(overlay,
                     (barra_x, barra_y),
                     (barra_x + barra_ancho, barra_y + barra_altura),
                     (255, 255, 255), 3)
        
        # Calcular altura del relleno según progreso
        altura_relleno = int(progreso * barra_altura)
        
        if altura_relleno > 0:
            # Calcular color según progreso (rojo -> amarillo -> verde)
            if progreso < 0.5:
                # Rojo a Amarillo
                r = 255
                g = int(255 * (progreso * 2))
                b = 0
            else:
                # Amarillo a Verde
                r = int(255 * (2 - progreso * 2))
                g = 255
                b = 0
            
            color_relleno = (b, g, r)  # BGR para OpenCV
            
            # Dibujar relleno desde abajo hacia arriba
            y_inicio = barra_y + barra_altura - altura_relleno
            cv2.rectangle(overlay,
                         (barra_x + 2, y_inicio),
                         (barra_x + barra_ancho - 2, barra_y + barra_altura - 2),
                         color_relleno, -1)
        
        # Dibujar texto de porcentaje
        porcentaje = int(progreso * 100)
        texto = f"{porcentaje}%"
        (text_width, text_height), _ = cv2.getTextSize(
            texto, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
        )
        text_x = barra_x + (barra_ancho - text_width) // 2
        text_y = barra_y + barra_altura + 25
        
        # Fondo para el texto
        cv2.rectangle(overlay,
                     (text_x - 5, text_y - text_height - 5),
                     (text_x + text_width + 5, text_y + 5),
                     (0, 0, 0), -1)
        
        # Texto
        cv2.putText(overlay, texto, (text_x, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    def dibujar_mensaje_guia(self, frame, mensaje):
        """
        Dibuja un mensaje de guía en la parte superior del frame
        
        Args:
            frame: Frame de OpenCV
            mensaje: Texto a mostrar
        """
        if not mensaje:
            return
        
        try:
            # Calcular tamaño del texto
            (text_width, text_height), baseline = cv2.getTextSize(
                mensaje, cv2.FONT_HERSHEY_SIMPLEX, 2.0, 2
            )
            
            box_x, box_y = 45, 30
            
            # Ajustar escala si el texto es muy largo
            max_width = frame.shape[1] - 100
            if text_width > max_width:
                scale_factor = max_width / text_width
                font_scale = 2.0 * scale_factor
            else:
                font_scale = 2.0
            
            # Recalcular con nueva escala
            (text_width, text_height), _ = cv2.getTextSize(
                mensaje, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2
            )
            
            # Dibujar fondo negro
            cv2.rectangle(frame,
                         (box_x - 10, box_y - 10),
                         (box_x + text_width + 20, box_y + text_height + 20),
                         (0, 0, 0), -1)
            
            # Dibujar texto
            cv2.putText(frame, mensaje,
                       (box_x, box_y + text_height + 5),
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                       (0, 0, 255), 2, cv2.LINE_AA)
        except Exception as e:
            logger.error(f"Error dibujando mensaje: {e}")
    
    def dibujar_angulo(self, overlay, angulo, posicion):
        """
        Dibuja el valor del ángulo en la posición especificada
        
        Args:
            overlay: Overlay transparente
            angulo: Valor del ángulo
            posicion: Tupla (x, y) donde dibujar
        """
        try:
            angulo_mostrado = int(max(0, min(180, angulo)))
            cv2.putText(overlay, str(angulo_mostrado),
                       (posicion[0] + 10, posicion[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                       (255, 255, 255), 3)
        except Exception as e:
            logger.error(f"Error dibujando ángulo: {e}")
    
    def dibujar_triangulo_angulo(self, overlay, p1, p2, p3, color=(128, 0, 250)):
        """
        Dibuja un triángulo para visualizar el ángulo formado por tres puntos
        
        Args:
            overlay: Overlay transparente
            p1, p2, p3: Tuplas (x, y) de los tres puntos
            color: Color del triángulo en formato BGR
        """
        try:
            triangle = np.array([p1, p2, p3], dtype=np.int32)
            cv2.fillPoly(overlay, [triangle], color=color)
        except Exception as e:
            logger.error(f"Error dibujando triángulo: {e}")
    
    def dibujar_lineas_articulacion(self, overlay, p1, p2, p3, color=(0, 255, 0), grosor=6):
        """
        Dibuja líneas entre tres puntos de articulación
        
        Args:
            overlay: Overlay transparente
            p1, p2, p3: Tuplas (x, y) de los puntos
            color: Color de las líneas en BGR
            grosor: Grosor de las líneas
        """
        try:
            cv2.line(overlay, p1, p2, color, grosor)
            cv2.line(overlay, p2, p3, color, grosor)
            
            # Dibujar puntos
            cv2.circle(overlay, p1, 8, (255, 0, 0), -1)
            cv2.circle(overlay, p2, 8, (0, 255, 255), -1)
            cv2.circle(overlay, p3, 8, (0, 0, 255), -1)
        except Exception as e:
            logger.error(f"Error dibujando líneas: {e}")
    
    def dibujar_feedback(self, frame, landmarks):
        """
        Dibuja feedback visual en el frame.
        Este método debe ser implementado o sobrescrito por cada ejercicio.
        """
        raise NotImplementedError("Debe implementar dibujar_feedback en la subclase")
