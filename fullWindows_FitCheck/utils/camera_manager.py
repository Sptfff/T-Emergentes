"""
Gestor de cámara con detección automática y manejo robusto de errores
"""
import cv2
import time
from utils.logger import get_logger
from config import (
    CAMERA_INDICES_TO_TRY, 
    CAMERA_BACKENDS_TO_TRY,
    CAMERA_WIDTH,
    CAMERA_HEIGHT
)

logger = get_logger()

class CameraManager:
    """Gestiona la inicialización y configuración de la cámara"""
    
    def __init__(self):
        self.cap = None
        self.camera_index = None
        self.camera_backend = None
    
    def initialize_camera(self):
        """
        Intenta inicializar la cámara probando diferentes índices y backends
        
        Returns:
            tuple: (cv2.VideoCapture, index, backend) o (None, None, None) si falla
        """
        logger.info("Iniciando detección de cámara...")
        
        for index in CAMERA_INDICES_TO_TRY:
            for backend_name in CAMERA_BACKENDS_TO_TRY:
                try:
                    # Obtener el valor del backend desde cv2
                    backend = getattr(cv2, backend_name, cv2.CAP_ANY)
                    
                    logger.debug(f"Probando cámara {index} con backend {backend_name}")
                    
                    # Intentar abrir la cámara
                    cap = cv2.VideoCapture(index, backend)
                    
                    # Esperar un momento para que se inicialice
                    time.sleep(0.5)
                    
                    if not cap.isOpened():
                        logger.debug(f"No se pudo abrir cámara {index} con {backend_name}")
                        cap.release()
                        continue
                    
                    # Configurar resolución
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
                    
                    # Intentar leer un frame de prueba
                    ret, frame = cap.read()
                    
                    if not ret or frame is None:
                        logger.warning(f"Cámara {index} con {backend_name} abierta pero sin imagen")
                        cap.release()
                        continue
                    
                    # ¡Éxito!
                    logger.info(f"✓ Cámara inicializada: índice={index}, backend={backend_name}")
                    logger.info(f"  Resolución: {frame.shape[1]}x{frame.shape[0]}")
                    
                    self.cap = cap
                    self.camera_index = index
                    self.camera_backend = backend_name
                    
                    return cap, index, backend_name
                    
                except Exception as e:
                    logger.error(f"Error con cámara {index}/{backend_name}: {e}")
                    continue
        
        # No se encontró ninguna cámara funcional
        logger.error("✗ No se pudo inicializar ninguna cámara")
        return None, None, None
    
    def release(self):
        """Libera los recursos de la cámara de forma segura"""
        if self.cap is not None:
            try:
                if self.cap.isOpened():
                    self.cap.release()
                    logger.info("Cámara liberada correctamente")
            except Exception as e:
                logger.error(f"Error al liberar cámara: {e}")
            finally:
                self.cap = None
    
    def is_opened(self):
        """Verifica si la cámara está abierta"""
        return self.cap is not None and self.cap.isOpened()
    
    def read(self):
        """
        Lee un frame de la cámara con validación
        
        Returns:
            tuple: (ret, frame) o (False, None) si hay error
        """
        if not self.is_opened():
            return False, None
        
        try:
            return self.cap.read()
        except Exception as e:
            logger.error(f"Error leyendo frame: {e}")
            return False, None
