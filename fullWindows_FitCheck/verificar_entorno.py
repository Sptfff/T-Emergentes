"""
Script de verificación del entorno FitCheck
Verifica dependencias, estructura de carpetas y configuración
"""
import sys
import os

def verificar_python():
    """Verifica la versión de Python"""
    print("=" * 60)
    print("VERIFICACIÓN DE PYTHON")
    print("=" * 60)
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("⚠ ADVERTENCIA: Se recomienda Python 3.8 o superior")
        return False
    return True

def verificar_dependencias():
    """Verifica que todas las dependencias estén instaladas"""
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE DEPENDENCIAS")
    print("=" * 60)
    
    dependencias = {
        'cv2': 'opencv-python',
        'mediapipe': 'mediapipe',
        'PIL': 'Pillow',
        'numpy': 'numpy',
        'tkinter': 'tkinter (incluido en Python)'
    }
    
    todas_ok = True
    for modulo, nombre in dependencias.items():
        try:
            __import__(modulo)
            print(f"✓ {nombre}")
        except ImportError:
            print(f"✗ {nombre} - NO INSTALADO")
            todas_ok = False
    
    return todas_ok

def verificar_estructura():
    """Verifica la estructura de carpetas del proyecto"""
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE ESTRUCTURA")
    print("=" * 60)
    
    carpetas_requeridas = [
        'screens',
        'ejercicios',
        'utils',
        'videos',
        'recursos/mediapipe/pose_landmark'
    ]
    
    archivos_requeridos = [
        'main.py',
        'config.py',
        'requirements.txt',
        'screens/bienvenida.py',
        'screens/seleccion_reps.py',
        'screens/entrenamiento.py',
        'screens/resumen.py',
        'ejercicios/base.py',
        'utils/logger.py',
        'utils/pose_utils.py',
        'utils/camera_manager.py'
    ]
    
    todas_ok = True
    
    print("\nCarpetas:")
    for carpeta in carpetas_requeridas:
        if os.path.exists(carpeta):
            print(f"✓ {carpeta}/")
        else:
            print(f"✗ {carpeta}/ - NO EXISTE")
            todas_ok = False
    
    print("\nArchivos:")
    for archivo in archivos_requeridos:
        if os.path.exists(archivo):
            print(f"✓ {archivo}")
        else:
            print(f"✗ {archivo} - NO EXISTE")
            todas_ok = False
    
    return todas_ok

def verificar_camara():
    """Verifica que se pueda detectar al menos una cámara"""
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE CÁMARA")
    print("=" * 60)
    
    try:
        import cv2
        
        camaras_encontradas = []
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                camaras_encontradas.append(i)
                cap.release()
        
        if camaras_encontradas:
            print(f"✓ Cámaras detectadas en índices: {camaras_encontradas}")
            return True
        else:
            print("⚠ No se detectaron cámaras")
            print("  Esto puede ser normal si no hay cámara conectada")
            return True  # No es error crítico
    except Exception as e:
        print(f"✗ Error verificando cámaras: {e}")
        return False

def verificar_config():
    """Verifica que el archivo de configuración sea válido"""
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE CONFIGURACIÓN")
    print("=" * 60)
    
    try:
        import config
        
        # Verificar variables críticas
        variables = [
            'CAMERA_INDEX',
            'CAMERA_INDICES_TO_TRY',
            'CAMERA_BACKENDS_TO_TRY',
            'MODEL_COMPLEXITY',
            'INACTIVIDAD_MAX',
            'FPS_LIMIT'
        ]
        
        todas_ok = True
        for var in variables:
            if hasattr(config, var):
                valor = getattr(config, var)
                print(f"✓ {var} = {valor}")
            else:
                print(f"✗ {var} - NO DEFINIDO")
                todas_ok = False
        
        return todas_ok
    except Exception as e:
        print(f"✗ Error cargando config.py: {e}")
        return False

def main():
    """Ejecuta todas las verificaciones"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "VERIFICACIÓN DE ENTORNO FITCHECK" + " " * 16 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    resultados = {
        'Python': verificar_python(),
        'Dependencias': verificar_dependencias(),
        'Estructura': verificar_estructura(),
        'Configuración': verificar_config(),
        'Cámara': verificar_camara()
    }
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    for nombre, resultado in resultados.items():
        estado = "✓ OK" if resultado else "✗ ERROR"
        print(f"{nombre:20} {estado}")
    
    print("\n" + "=" * 60)
    
    if all(resultados.values()):
        print("✓ ¡TODOS LOS CHECKS PASARON!")
        print("  El proyecto está listo para ejecutarse.")
        print("\n  Ejecuta: python main.py")
    else:
        print("✗ ALGUNOS CHECKS FALLARON")
        print("  Revisa los errores arriba y:")
        print("  1. Instala dependencias: pip install -r requirements.txt")
        print("  2. Verifica la estructura de carpetas")
        print("  3. Revisa config.py")
    
    print("=" * 60)
    print()

if __name__ == "__main__":
    main()
