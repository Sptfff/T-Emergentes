# FitCheck - Sistema de Detección de Ejercicios con IA

## Descripción
FitCheck es una aplicación de escritorio que utiliza visión por computadora y análisis de pose para detectar y analizar ejercicios físicos en tiempo real. Proporciona feedback instantáneo sobre la forma del ejercicio y cuenta repeticiones automáticamente.

## Características
- ✅ Detección automática de 5 tipos de ejercicios
- ✅ Contador de repeticiones en tiempo real
- ✅ Análisis de forma y postura
- ✅ Feedback visual con mensajes correctivos
- ✅ Resumen detallado al finalizar la sesión
- ✅ Visualización de GIFs demostrativos

## Ejercicios Soportados
1. Sentadilla tradicional
2. Estocadas
3. Step-Ups
4. Sentadilla con salto
5. Sentadilla sumo

## Requisitos del Sistema
- Python 3.8 o superior
- Cámara web funcional
- Sistema operativo: Windows, macOS, o Linux

## Instalación

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd fullWindows_FitCheck
```

### 2. Crear entorno virtual (recomendado)
```bash
python -m venv venv
```

### 3. Activar el entorno virtual
- Windows:
  ```bash
  venv\Scripts\activate
  ```
- macOS/Linux:
  ```bash
  source venv/bin/activate
  ```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

## Ejecución

### Desde la línea de comandos:
```cmd
DENTRO DE LA CARPETA DE "fullWindows_FitCheck" 
install.bat #Para validar e instalar las dependencias necesarias
run.bat  #crea el entorno virtual y ejecuta el programa
```
```bash
python main.py
```

### Desde VS Code:
1. Abrir el archivo `main.py`
2. Click derecho → "Run Python File in Terminal"
3. O presionar el botón "Run" en la esquina superior derecha

## Uso de la Aplicación

1. **Seleccionar Ejercicio**: Elige uno de los 5 ejercicios disponibles
2. **Configurar Repeticiones**: Selecciona cuántas repeticiones deseas realizar (1-30)
3. **Posicionamiento**: Colócate de perfil derecho frente a la cámara
4. **Iniciar Entrenamiento**: Haz click en "Empezar" cuando estés listo
5. **Realizar Ejercicio**: Sigue las indicaciones en pantalla
6. **Revisar Resumen**: Al finalizar, verás un resumen con consejos personalizados

## Importante
⚠️ **Posicionamiento**: El sistema detecta movimientos del lado derecho del cuerpo. Posiciónate de perfil derecho para un conteo correcto.

⚠️ **Inactividad**: Si pasas 15 segundos sin hacer repeticiones, la sesión finalizará automáticamente.

⚠️ **Iluminación**: Asegúrate de tener buena iluminación para una mejor detección.

## Estructura del Proyecto
```
fullWindows_FitCheck/
│
├── main.py                 # Punto de entrada de la aplicación
├── requirements.txt        # Dependencias del proyecto
│
├── screens/               # Pantallas de la interfaz
│   ├── bienvenida.py     # Pantalla inicial
│   ├── seleccion_reps.py # Selección de repeticiones
│   ├── entrenamiento.py  # Pantalla de entrenamiento
│   └── resumen.py        # Resumen de la sesión
│
├── ejercicios/           # Lógica de cada ejercicio
│   ├── base.py          # Clase base abstracta
│   ├── sentadilla.py    # Sentadilla tradicional
│   ├── estocada.py      # Estocadas
│   ├── step_up.py       # Step-Ups
│   ├── consalto.py      # Sentadilla con salto
│   └── sumo.py          # Sentadilla sumo
│
├── utils/               # Utilidades
│   └── pose_utils.py   # Funciones de cálculo de ángulos
│
├── recursos/           # Recursos de MediaPipe
│   └── mediapipe/
│
└── videos/            # GIFs demostrativos de ejercicios
```

## Dependencias Principales
- **opencv-python**: Procesamiento de video y visualización
- **mediapipe**: Detección y análisis de pose
- **Pillow**: Manejo de imágenes y GIFs
- **numpy**: Cálculos numéricos
- **tkinter**: Interfaz gráfica (incluido en Python)

## Solución de Problemas

### La cámara no se detecta
- Verifica que ninguna otra aplicación esté usando la cámara
- Prueba cambiar el índice de la cámara en `entrenamiento.py` (línea 48):
  ```python
  self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Prueba con 0, 1, o 2
  ```

### Error de importación de módulos
- Asegúrate de haber instalado todas las dependencias:
  ```bash
  pip install -r requirements.txt
  ```

### La aplicación no responde
- Cierra la aplicación y reinicia
- Verifica que tu sistema cumpla con los requisitos mínimos

## Contribuciones
Las contribuciones son bienvenidas. Por favor:
1. Fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit de tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia
Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## Contacto
Para preguntas o sugerencias, abre un issue en el repositorio.
