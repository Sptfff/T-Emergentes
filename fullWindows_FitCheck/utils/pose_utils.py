"""
Utilidades para cálculo de pose y ángulos
"""
import math
from utils.logger import get_logger

logger = get_logger()

def calcular_angulo(p1, p2, p3):
    """
    Calcula el ángulo formado en p2 por los puntos p1 y p3.
    p1, p2, p3 son tuplas (x, y)
    
    Args:
        p1: Tupla (x, y) del primer punto
        p2: Tupla (x, y) del vértice del ángulo
        p3: Tupla (x, y) del tercer punto
        
    Returns:
        float: Ángulo en grados (0-180)
    """
    try:
        # Validar que los puntos sean tuplas válidas
        if not all(isinstance(p, (tuple, list)) and len(p) >= 2 for p in [p1, p2, p3]):
            logger.error("Puntos inválidos para calcular ángulo")
            return 0.0
        
        # Calcular vectores
        a = (p1[0] - p2[0], p1[1] - p2[1])
        b = (p3[0] - p2[0], p3[1] - p2[1])
        
        # Calcular magnitudes
        magnitud_a = math.sqrt(a[0]**2 + a[1]**2)
        magnitud_b = math.sqrt(b[0]**2 + b[1]**2)
        
        # Validar que los vectores no sean nulos
        if magnitud_a < 1e-6 or magnitud_b < 1e-6:
            logger.warning("Vectores colineales o puntos superpuestos detectados")
            return 0.0
        
        # Calcular producto punto
        producto_punto = a[0] * b[0] + a[1] * b[1]
        
        # Calcular coseno y limitar a rango válido [-1, 1]
        cos_angulo = producto_punto / (magnitud_a * magnitud_b)
        cos_angulo = max(-1.0, min(1.0, cos_angulo))
        
        # Calcular ángulo
        angulo_rad = math.acos(cos_angulo)
        angulo_deg = math.degrees(angulo_rad)
        
        return angulo_deg
        
    except Exception as e:
        logger.error(f"Error calculando ángulo: {e}")
        return 0.0

def validar_landmarks(landmarks, required_keys):
    """
    Valida que todos los landmarks requeridos estén presentes
    
    Args:
        landmarks: Diccionario de landmarks
        required_keys: Lista de claves requeridas
        
    Returns:
        bool: True si todos los landmarks están presentes
    """
    try:
        for key in required_keys:
            if key not in landmarks:
                logger.warning(f"Landmark faltante: {key}")
                return False
            # Validar que tenga coordenadas x, y
            if not hasattr(landmarks[key], 'x') or not hasattr(landmarks[key], 'y'):
                logger.warning(f"Landmark {key} sin coordenadas válidas")
                return False
        return True
    except Exception as e:
        logger.error(f"Error validando landmarks: {e}")
        return False
