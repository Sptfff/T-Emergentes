"""
Sistema de logging para FitCheck
Proporciona registro de eventos, errores y debugging
"""
import logging
import os
from datetime import datetime

class FitCheckLogger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        
        # Crear carpeta de logs si no existe
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Nombre del archivo de log con fecha
        log_filename = os.path.join(
            log_dir, 
            f'fitcheck_{datetime.now().strftime("%Y%m%d")}.log'
        )
        
        # Configurar el logger
        self.logger = logging.getLogger('FitCheck')
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar duplicar handlers
        if not self.logger.handlers:
            # Handler para archivo
            file_handler = logging.FileHandler(log_filename, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # Handler para consola
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formato
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def get_logger(self):
        return self.logger

# Función conveniente para obtener el logger
def get_logger():
    return FitCheckLogger().get_logger()
