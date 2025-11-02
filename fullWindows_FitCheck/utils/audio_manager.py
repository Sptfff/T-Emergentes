"""
Sistema de gestión de audio para feedback por voz.
Implementa cola de prioridad con prevención de spam y reproducción asíncrona.
"""
import pyttsx3
import queue
import threading
import time
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime
from utils.logger import get_logger

logger = get_logger()


@dataclass(order=True)
class AudioMessage:
    """Mensaje de audio con prioridad."""
    prioridad: int  # Menor número = mayor prioridad
    timestamp: float = field(compare=False)
    texto: str = field(compare=False)
    categoria: str = field(compare=False, default="info")


class AudioManager:
    """
    Gestor de audio para feedback por voz durante entrenamiento.
    
    Características:
    - Cola de prioridad (errores > guías > info)
    - Prevención de spam (no repetir mensajes recientes)
    - Reproducción asíncrona (no bloquea UI)
    - Thread-safe
    """
    
    # Prioridades
    PRIORIDAD_CRITICA = 1    # Errores graves de forma
    PRIORIDAD_ALTA = 2       # Errores menores
    PRIORIDAD_MEDIA = 3      # Guías de ejecución
    PRIORIDAD_BAJA = 4       # Información general
    
    def __init__(self, habilitado: bool = True):
        """
        Inicializar gestor de audio.
        
        Args:
            habilitado: Si False, el sistema no reproducirá audio (útil para testing)
        """
        self.habilitado = habilitado
        self.running = False
        self.pausado = False
        
        # Cola de mensajes con prioridad
        self.cola_mensajes = queue.PriorityQueue()
        
        # Thread de reproducción
        self.audio_thread: Optional[threading.Thread] = None
        
        # Control de duplicados (prevención de spam)
        self.mensajes_recientes: List[Dict] = []
        self.max_mensajes_recientes = 10
        self.tiempo_cooldown = 5.0  # Segundos antes de permitir repetir mensaje
        
        # Motor TTS
        self.engine: Optional[pyttsx3.Engine] = None
        self.engine_lock = threading.Lock()
        
        # Estadísticas
        self.mensajes_enviados = 0
        self.mensajes_bloqueados = 0
        
        if self.habilitado:
            self._inicializar_engine()
            self._iniciar_thread()
        
        logger.info(f"AudioManager inicializado (habilitado={habilitado})")
    
    def _inicializar_engine(self):
        """Inicializar motor TTS con configuración optimizada."""
        try:
            self.engine = pyttsx3.init()
            
            # Configuración de voz
            voices = self.engine.getProperty('voices')
            
            # Intentar seleccionar voz en español
            for voice in voices:
                if 'spanish' in voice.name.lower() or 'español' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    logger.info(f"Voz seleccionada: {voice.name}")
                    break
            
            # Configuración de parámetros
            self.engine.setProperty('rate', 150)    # Velocidad (palabras por minuto)
            self.engine.setProperty('volume', 0.9)  # Volumen (0.0 a 1.0)
            
            logger.info("Motor TTS inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando motor TTS: {e}")
            self.habilitado = False
    
    def _iniciar_thread(self):
        """Iniciar thread de reproducción de audio."""
        self.running = True
        self.audio_thread = threading.Thread(
            target=self._audio_loop,
            name="AudioThread",
            daemon=True
        )
        self.audio_thread.start()
        logger.info("Thread de audio iniciado")
    
    def _audio_loop(self):
        """
        Loop principal del thread de audio.
        Procesa mensajes de la cola y los reproduce.
        """
        logger.info("Audio loop iniciado")
        
        while self.running:
            try:
                # Esperar mensaje con timeout
                try:
                    mensaje: AudioMessage = self.cola_mensajes.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Si está pausado, esperar
                while self.pausado and self.running:
                    time.sleep(0.1)
                
                if not self.running:
                    break
                
                # Reproducir mensaje
                self._reproducir_mensaje(mensaje)
                
                # Marcar como completado
                self.cola_mensajes.task_done()
                
            except Exception as e:
                logger.error(f"Error en audio loop: {e}", exc_info=True)
        
        logger.info("Audio loop finalizado")
    
    def _reproducir_mensaje(self, mensaje: AudioMessage):
        """
        Reproducir mensaje de audio.
        
        Args:
            mensaje: Mensaje a reproducir
        """
        if not self.habilitado or not self.engine:
            return
        
        try:
            with self.engine_lock:
                logger.debug(f"Reproduciendo audio [P{mensaje.prioridad}]: {mensaje.texto}")
                
                # Sintetizar y reproducir
                self.engine.say(mensaje.texto)
                self.engine.runAndWait()
                
                self.mensajes_enviados += 1
                logger.debug(f"Audio reproducido correctamente ({self.mensajes_enviados} total)")
                
        except Exception as e:
            logger.error(f"Error reproduciendo audio: {e}")
    
    def _es_mensaje_duplicado(self, texto: str, categoria: str) -> bool:
        """
        Verificar si un mensaje es duplicado reciente.
        
        Args:
            texto: Texto del mensaje
            categoria: Categoría del mensaje
            
        Returns:
            True si el mensaje es duplicado y está en cooldown
        """
        ahora = time.time()
        
        # Buscar en mensajes recientes
        for msg in self.mensajes_recientes:
            if msg['texto'] == texto and msg['categoria'] == categoria:
                tiempo_transcurrido = ahora - msg['timestamp']
                
                if tiempo_transcurrido < self.tiempo_cooldown:
                    # Mensaje duplicado en cooldown
                    return True
        
        return False
    
    def _agregar_a_recientes(self, texto: str, categoria: str):
        """
        Agregar mensaje a lista de recientes.
        
        Args:
            texto: Texto del mensaje
            categoria: Categoría del mensaje
        """
        # Agregar nuevo mensaje
        self.mensajes_recientes.append({
            'texto': texto,
            'categoria': categoria,
            'timestamp': time.time()
        })
        
        # Limpiar mensajes viejos
        ahora = time.time()
        self.mensajes_recientes = [
            msg for msg in self.mensajes_recientes
            if ahora - msg['timestamp'] < self.tiempo_cooldown * 2
        ]
        
        # Limitar tamaño
        if len(self.mensajes_recientes) > self.max_mensajes_recientes:
            self.mensajes_recientes.pop(0)
    
    def agregar_mensaje(
        self,
        texto: str,
        prioridad: int = PRIORIDAD_MEDIA,
        categoria: str = "info",
        forzar: bool = False
    ):
        """
        Agregar mensaje a la cola de reproducción.
        
        Args:
            texto: Texto a reproducir
            prioridad: Prioridad del mensaje (usar constantes PRIORIDAD_*)
            categoria: Categoría del mensaje (error, guia, info, etc.)
            forzar: Si True, ignora prevención de spam
        """
        if not self.habilitado:
            return
        
        # Validar texto
        if not texto or not texto.strip():
            return
        
        texto = texto.strip()
        
        # Verificar duplicados (a menos que se fuerce)
        if not forzar and self._es_mensaje_duplicado(texto, categoria):
            self.mensajes_bloqueados += 1
            logger.debug(f"Mensaje bloqueado (duplicado): {texto}")
            return
        
        # Crear mensaje
        mensaje = AudioMessage(
            prioridad=prioridad,
            timestamp=time.time(),
            texto=texto,
            categoria=categoria
        )
        
        # Agregar a cola
        self.cola_mensajes.put(mensaje)
        
        # Registrar en recientes
        self._agregar_a_recientes(texto, categoria)
        
        logger.debug(f"Mensaje agregado a cola [P{prioridad}]: {texto}")
    
    def agregar_error(self, texto: str, critico: bool = False):
        """
        Agregar mensaje de error.
        
        Args:
            texto: Texto del error
            critico: Si es crítico (mayor prioridad)
        """
        prioridad = self.PRIORIDAD_CRITICA if critico else self.PRIORIDAD_ALTA
        self.agregar_mensaje(texto, prioridad, "error")
    
    def agregar_guia(self, texto: str):
        """
        Agregar mensaje de guía.
        
        Args:
            texto: Texto de la guía
        """
        self.agregar_mensaje(texto, self.PRIORIDAD_MEDIA, "guia")
    
    def agregar_info(self, texto: str):
        """
        Agregar mensaje informativo.
        
        Args:
            texto: Texto informativo
        """
        self.agregar_mensaje(texto, self.PRIORIDAD_BAJA, "info")
    
    def pausar(self):
        """Pausar reproducción de audio."""
        self.pausado = True
        logger.info("Audio pausado")
    
    def reanudar(self):
        """Reanudar reproducción de audio."""
        self.pausado = False
        logger.info("Audio reanudado")
    
    def limpiar_cola(self):
        """Limpiar todos los mensajes pendientes en la cola."""
        while not self.cola_mensajes.empty():
            try:
                self.cola_mensajes.get_nowait()
                self.cola_mensajes.task_done()
            except queue.Empty:
                break
        
        logger.info("Cola de audio limpiada")
    
    def esperar_cola_vacia(self, timeout: float = 5.0) -> bool:
        """
        Esperar a que la cola se vacíe.
        
        Args:
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            True si la cola se vació, False si hubo timeout
        """
        try:
            # Queue.join() bloquea hasta que todos los items sean procesados
            # Usamos un loop con timeout manual
            inicio = time.time()
            while not self.cola_mensajes.empty():
                if time.time() - inicio > timeout:
                    return False
                time.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"Error esperando cola: {e}")
            return False
    
    def detener(self):
        """Detener el gestor de audio y liberar recursos."""
        logger.info("Deteniendo AudioManager...")
        
        # Señalar detención
        self.running = False
        
        # Esperar a que termine el thread
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=2.0)
        
        # Limpiar cola
        self.limpiar_cola()
        
        # Liberar motor TTS
        if self.engine:
            try:
                with self.engine_lock:
                    self.engine.stop()
                    del self.engine
                    self.engine = None
            except Exception as e:
                logger.error(f"Error liberando motor TTS: {e}")
        
        logger.info(f"AudioManager detenido. Estadísticas: {self.mensajes_enviados} enviados, {self.mensajes_bloqueados} bloqueados")
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtener estadísticas del gestor de audio.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'habilitado': self.habilitado,
            'running': self.running,
            'pausado': self.pausado,
            'mensajes_enviados': self.mensajes_enviados,
            'mensajes_bloqueados': self.mensajes_bloqueados,
            'cola_tamano': self.cola_mensajes.qsize(),
            'mensajes_recientes': len(self.mensajes_recientes)
        }
    
    def __del__(self):
        """Destructor: asegurar cleanup."""
        if self.running:
            self.detener()
