# Configuración de FitCheck

# ===========================
# CONFIGURACIÓN DE CÁMARA
# ===========================
# Índice de la cámara a utilizar (0 = cámara por defecto, 1 = cámara externa, etc.)
CAMERA_INDEX = 0  # Cambiado a 0 (cámara por defecto)

# Backend de captura de video para Windows
# Opciones: "CAP_DSHOW" (recomendado para Windows), "CAP_MSMF", "CAP_ANY"
CAMERA_BACKEND = "CAP_DSHOW"

# Lista de índices de cámara a probar en orden
CAMERA_INDICES_TO_TRY = [0, 1, 2]

# Lista de backends a probar en orden
CAMERA_BACKENDS_TO_TRY = ["CAP_DSHOW", "CAP_MSMF", "CAP_ANY"]

# Resolución de la cámara
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# ===========================
# CONFIGURACIÓN DE MEDIAPIPE
# ===========================
# Complejidad del modelo (0, 1, o 2) - Mayor = más preciso pero más lento
MODEL_COMPLEXITY = 0

# Confianza mínima para la detección
MIN_DETECTION_CONFIDENCE = 0.5

# Confianza mínima para el seguimiento
MIN_TRACKING_CONFIDENCE = 0.5

# ===========================
# CONFIGURACIÓN DE ENTRENAMIENTO
# ===========================
# Máximo de segundos sin repetir antes de finalizar automáticamente
INACTIVIDAD_MAX = 15

# Segundos antes de mostrar advertencia de inactividad
ADVERTENCIA_TIEMPO = 5

# Límite de FPS para el procesamiento de video (reduce carga de CPU)
FPS_LIMIT = 15

# Frecuencia de detección de errores (optimización de rendimiento)
# Cada cuántos frames se debe verificar la forma y detectar errores
# Valores recomendados: 3-7 frames (para FPS_LIMIT=15)
# - 3 frames = 5 checks/seg (alta frecuencia)
# - 5 frames = 3 checks/seg (RECOMENDADO - balance óptimo)
# - 7 frames = 2.1 checks/seg (baja frecuencia)
ERROR_CHECK_INTERVAL = 5

# Número de detecciones consecutivas requeridas para confirmar un error
# Esto evita falsos positivos por movimientos momentáneos
ERROR_CONFIRMATION_FRAMES = 2

# Tiempo que un mensaje de error permanece visible en pantalla (segundos)
MENSAJE_ERROR_TTL = 2.0

# ===========================
# CONFIGURACIÓN DE REPETICIONES
# ===========================
# Rango de repeticiones permitidas
MIN_REPETICIONES = 1
MAX_REPETICIONES = 30

# ===========================
# CONFIGURACIÓN DE INTERFAZ
# ===========================
# Tamaño de la ventana principal
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Colores de tema (formato RGB)
COLOR_BACKGROUND = "black"
COLOR_TEXT_PRIMARY = "white"
COLOR_TEXT_SECONDARY = "orange"
COLOR_ERROR = "red"
COLOR_SUCCESS = "green"

# ===========================
# CONFIGURACIÓN DE VIDEOS
# ===========================
# Ruta a la carpeta de videos demostrativos
VIDEOS_FOLDER = "videos"

# Tamaño de redimensión de los GIFs (ancho x alto en píxeles)
GIF_WIDTH = 300
GIF_HEIGHT = 300

# Velocidad de animación de GIFs (milisegundos por frame)
GIF_ANIMATION_SPEED = 100

# ===========================
# CONFIGURACIÓN DE AUDIO
# ===========================
# Habilitar/deshabilitar feedback por voz
AUDIO_HABILITADO = True

# Velocidad de la voz (palabras por minuto)
# Valores típicos: 125-175 (150 es estándar)
AUDIO_VELOCIDAD = 150

# Volumen de la voz (0.0 a 1.0)
AUDIO_VOLUMEN = 0.9

# Tiempo de cooldown entre mensajes duplicados (segundos)
# Evita spam de mensajes repetidos
AUDIO_COOLDOWN = 5.0

# Habilitar audio solo para errores (desactiva guías informativas)
AUDIO_SOLO_ERRORES = False

# Prioridad mínima para reproducir (1=crítica, 2=alta, 3=media, 4=baja)
# Si AUDIO_SOLO_ERRORES=True, esto se ignora y solo se reproducen errores (1-2)
AUDIO_PRIORIDAD_MINIMA = 2
