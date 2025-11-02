# PROPUESTA: ESTANDARIZACIÓN BASADA EN CONFIGURACIÓN

## 🎯 Objetivo
Convertir la lógica de detección de ejercicios de **código hard-coded** a un **sistema configurable y extensible** que permita agregar nuevos ejercicios sin escribir código repetitivo.

---

## 📊 ANÁLISIS DE BENEFICIOS

### ✅ Ventajas Principales

#### 1. **Escalabilidad Extrema**
```
Situación Actual: Agregar 1 ejercicio = 150-200 líneas de código
Situación Propuesta: Agregar 1 ejercicio = 1 archivo JSON/YAML (~50 líneas)

Para 20 ejercicios:
- Actual: ~3000-4000 líneas de código Python
- Propuesto: ~1000 líneas JSON + motor genérico (500 líneas Python)
```

#### 2. **Mantenimiento Simplificado**
- ✅ Cambiar umbral de error: editar JSON, no tocar código
- ✅ Ajustar mensaje: editar JSON, no recompilar
- ✅ Un bug en motor afecta todos los ejercicios → una sola corrección

#### 3. **Testing Más Fácil**
```python
# Actual: Mock de toda la clase
mock_sentadilla = MagicMock()

# Propuesto: Solo cambiar configuración
test_config = {
    "umbral_bajada": 90,
    "umbral_error_espalda": 70
}
```

#### 4. **Colaboración No-Técnica**
- Entrenadores pueden ajustar umbrales sin programar
- Editar mensajes en JSON es más accesible
- Versionado de configuraciones independiente del código

#### 5. **Reutilización de Código**
```
Código Actual (5 ejercicios):
- calcular_angulo() llamado 25+ veces
- validar_error_con_confirmacion() copiado 25+ veces
- Lógica de estado repetida 5 veces

Código Propuesto:
- Motor genérico ejecuta configuración
- 1 implementación de cada función
- Lógica de estado centralizada
```

#### 6. **Documentación Automática**
```yaml
# La configuración ES la documentación
ejercicios/sentadilla.yaml:
  nombre: "Sentadilla Tradicional"
  descripción: "Ejercicio de piernas que trabaja cuádriceps..."
  umbrales:
    bajada: 90  # < 90° = posición baja
```

---

## 🏗️ ARQUITECTURA PROPUESTA

### Estructura de Directorios
```
fullWindows_FitCheck/
├── ejercicios/
│   ├── base.py                 # Motor genérico
│   ├── configs/                # ⭐ NUEVO
│   │   ├── sentadilla.json
│   │   ├── estocada.json
│   │   ├── step_up.json
│   │   ├── consalto.json
│   │   ├── sumo.json
│   │   └── schema.json         # Validación de formato
│   └── __init__.py
├── utils/
│   ├── exercise_engine.py      # ⭐ NUEVO: Motor de ejecución
│   ├── config_loader.py        # ⭐ NUEVO: Cargador de configs
│   └── validators.py           # ⭐ NUEVO: Validadores reutilizables
```

---

## 📝 FORMATO DE CONFIGURACIÓN

### Ejemplo: `ejercicios/configs/sentadilla.json`

```json
{
  "metadata": {
    "nombre": "Sentadilla Tradicional",
    "descripcion": "Ejercicio de piernas para cuádriceps, glúteos y core",
    "dificultad": "intermedio",
    "musculos_objetivo": ["cuadriceps", "gluteos", "core"],
    "version": "1.0"
  },
  
  "anatomia": {
    "landmarks_principales": [
      "RIGHT_HIP",
      "RIGHT_KNEE",
      "RIGHT_ANKLE"
    ],
    "landmarks_secundarios": [
      "RIGHT_SHOULDER",
      "RIGHT_FOOT_INDEX",
      "LEFT_FOOT_INDEX"
    ],
    "lado": "derecho"
  },
  
  "metricas_principales": {
    "angulo_rodilla": {
      "puntos": ["RIGHT_HIP", "RIGHT_KNEE", "RIGHT_ANKLE"],
      "tipo": "angulo_3_puntos",
      "frecuencia": "cada_frame"
    }
  },
  
  "metricas_secundarias": {
    "angulo_espalda": {
      "puntos": ["RIGHT_SHOULDER", "RIGHT_HIP", "RIGHT_KNEE"],
      "tipo": "angulo_3_puntos",
      "frecuencia": "cada_verificacion"
    },
    "distancia_pies": {
      "puntos": ["RIGHT_FOOT_INDEX", "LEFT_FOOT_INDEX"],
      "tipo": "distancia_horizontal",
      "frecuencia": "cada_verificacion"
    },
    "altura_tobillo": {
      "puntos": ["RIGHT_ANKLE", "RIGHT_HIP"],
      "tipo": "diferencia_vertical",
      "frecuencia": "cada_verificacion"
    }
  },
  
  "maquina_estados": {
    "inicial": "arriba",
    "transiciones": [
      {
        "de": "arriba",
        "a": "bajando",
        "condicion": "angulo_rodilla < 90"
      },
      {
        "de": "bajando",
        "a": "arriba",
        "condicion": "angulo_rodilla > 160",
        "accion": "incrementar_repeticion"
      }
    ]
  },
  
  "progreso": {
    "metrica": "angulo_rodilla",
    "min": 90,
    "max": 160,
    "invertir": false
  },
  
  "validaciones": [
    {
      "nombre": "pies_juntos",
      "condicion": "distancia_pies < 0.12",
      "mensaje": "Separa los pies",
      "severidad": "media",
      "requiere_confirmacion": true
    },
    {
      "nombre": "espalda_inclinada",
      "condicion": "angulo_espalda < 70",
      "mensaje": "Manten la espalda recta",
      "severidad": "alta",
      "requiere_confirmacion": true
    },
    {
      "nombre": "tobillos_no_apoyados",
      "condicion": "altura_tobillo > 0.1",
      "mensaje": "Apoya bien los tobillos",
      "severidad": "media",
      "requiere_confirmacion": true
    },
    {
      "nombre": "rodillas_hacia_adentro",
      "condicion": "RIGHT_KNEE.y < RIGHT_ANKLE.y",
      "mensaje": "Evita que las rodillas se muevan hacia adentro",
      "severidad": "alta",
      "requiere_confirmacion": true
    },
    {
      "nombre": "rodillas_no_alineadas",
      "condicion": "abs(RIGHT_KNEE.x - RIGHT_ANKLE.x) > 0.1",
      "mensaje": "Alinea tus rodillas con los pies",
      "severidad": "media",
      "requiere_confirmacion": true
    }
  ],
  
  "mensajes_guia": {
    "arriba": "Baja más",
    "bajando": "Continúa bajando",
    "repeticion_completada": "Buena repeticion!"
  },
  
  "visualizacion": {
    "lineas": [
      {
        "desde": "RIGHT_HIP",
        "hasta": "RIGHT_KNEE",
        "color": [0, 255, 0],
        "grosor": 6
      },
      {
        "desde": "RIGHT_KNEE",
        "hasta": "RIGHT_ANKLE",
        "color": [0, 255, 0],
        "grosor": 6
      }
    ],
    "puntos": [
      {"landmark": "RIGHT_HIP", "color": [255, 0, 0], "radio": 8},
      {"landmark": "RIGHT_KNEE", "color": [0, 255, 255], "radio": 8},
      {"landmark": "RIGHT_ANKLE", "color": [0, 0, 255], "radio": 8}
    ],
    "mostrar_angulo": {
      "punto": "RIGHT_KNEE",
      "metrica": "angulo_rodilla"
    }
  }
}
```

---

## 🔧 MOTOR GENÉRICO

### `utils/exercise_engine.py`

```python
"""
Motor genérico para ejecutar ejercicios basados en configuración.
"""
import json
import time
from typing import Dict, List, Any, Optional
from utils.pose_utils import calcular_angulo
from utils.logger import get_logger

logger = get_logger()

class ExerciseEngine:
    """
    Motor que ejecuta ejercicios basados en configuración JSON/YAML.
    Reemplaza las clases individuales por ejercicio.
    """
    
    def __init__(self, config_path: str):
        """Inicializar motor con configuración de ejercicio."""
        self.config = self._cargar_config(config_path)
        self.estado_actual = self.config['maquina_estados']['inicial']
        self.repeticiones = 0
        self.progreso = 0.0
        self.ultimo_angulo = 0
        
        # Sistema de frecuencia (heredado de FASE 1)
        self.frame_counter = 0
        self.mensaje_cache = None
        self.mensaje_timestamp = 0
        
        # Inicializar contadores de errores
        self.errores_contador = {}
        self.error_flags = {}
        self.error_confirmation_counters = {}
        
        for validacion in self.config['validaciones']:
            nombre = validacion['nombre']
            self.errores_contador[nombre] = 0
            self.error_flags[nombre] = False
            self.error_confirmation_counters[nombre] = 0
        
        # Cache de métricas calculadas
        self.metricas_cache = {}
        
        logger.info(f"Motor inicializado para: {self.config['metadata']['nombre']}")
    
    def _cargar_config(self, config_path: str) -> Dict:
        """Cargar y validar configuración."""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # TODO: Validar contra schema.json
        return config
    
    def _calcular_metrica(self, landmarks: Dict, metrica_config: Dict) -> float:
        """
        Calcular métrica según configuración.
        
        Tipos soportados:
        - angulo_3_puntos: Ángulo formado por 3 landmarks
        - distancia_horizontal: Distancia en X entre 2 puntos
        - distancia_vertical: Distancia en Y entre 2 puntos
        - diferencia_vertical: landmark1.y - landmark2.y
        """
        tipo = metrica_config['tipo']
        puntos = [landmarks[p] for p in metrica_config['puntos']]
        
        if tipo == 'angulo_3_puntos':
            p1 = (puntos[0].x, puntos[0].y)
            p2 = (puntos[1].x, puntos[1].y)
            p3 = (puntos[2].x, puntos[2].y)
            return calcular_angulo(p1, p2, p3)
        
        elif tipo == 'distancia_horizontal':
            return abs(puntos[0].x - puntos[1].x)
        
        elif tipo == 'distancia_vertical':
            return abs(puntos[0].y - puntos[1].y)
        
        elif tipo == 'diferencia_vertical':
            return puntos[0].y - puntos[1].y
        
        else:
            logger.warning(f"Tipo de métrica desconocido: {tipo}")
            return 0.0
    
    def _evaluar_condicion(self, condicion: str, contexto: Dict) -> bool:
        """
        Evaluar condición booleana con acceso a métricas y landmarks.
        
        Ejemplos:
        - "angulo_rodilla < 90"
        - "distancia_pies < 0.12"
        - "RIGHT_KNEE.y < RIGHT_ANKLE.y"
        """
        try:
            # Crear espacio de nombres seguro con métricas
            namespace = {**contexto}
            return eval(condicion, {"__builtins__": {}}, namespace)
        except Exception as e:
            logger.error(f"Error evaluando condición '{condicion}': {e}")
            return False
    
    def procesar_pose(self, landmarks: Dict):
        """
        Procesamiento genérico de pose basado en configuración.
        Implementa sistema de dos niveles de FASE 1.
        """
        # ===== NIVEL 1: PROCESAMIENTO VISUAL (SIEMPRE) =====
        
        # Calcular métricas principales (cada frame)
        for nombre, config in self.config['metricas_principales'].items():
            if config['frecuencia'] == 'cada_frame':
                self.metricas_cache[nombre] = self._calcular_metrica(landmarks, config)
        
        # Obtener métrica principal para progreso
        metrica_progreso_config = self.config['progreso']
        metrica_progreso = self.metricas_cache[metrica_progreso_config['metrica']]
        
        # Actualizar progreso
        min_val = metrica_progreso_config['min']
        max_val = metrica_progreso_config['max']
        self.progreso = (metrica_progreso - min_val) / (max_val - min_val)
        self.progreso = max(0.0, min(1.0, self.progreso))
        
        if metrica_progreso_config.get('invertir', False):
            self.progreso = 1.0 - self.progreso
        
        self.ultimo_angulo = metrica_progreso
        
        # Máquina de estados
        mensajes = []
        nueva_repeticion = False
        
        # Crear contexto para evaluación de condiciones
        contexto = {
            **self.metricas_cache,
            **{name: landmarks[name] for name in self.config['anatomia']['landmarks_principales']},
            **{name: landmarks[name] for name in self.config['anatomia']['landmarks_secundarios']}
        }
        
        for transicion in self.config['maquina_estados']['transiciones']:
            if self.estado_actual == transicion['de']:
                if self._evaluar_condicion(transicion['condicion'], contexto):
                    self.estado_actual = transicion['a']
                    
                    # Ejecutar acción si existe
                    if transicion.get('accion') == 'incrementar_repeticion':
                        self.repeticiones += 1
                        nueva_repeticion = True
                        msg_key = 'repeticion_completada'
                        mensajes.append(self.config['mensajes_guia'].get(msg_key, "¡Bien!"))
        
        # ===== NIVEL 2: DETECCIÓN DE ERRORES (CONDICIONAL) =====
        
        if self.debe_verificar_errores():
            # Calcular métricas secundarias solo cuando se verifica errores
            for nombre, config in self.config['metricas_secundarias'].items():
                if config['frecuencia'] == 'cada_verificacion':
                    self.metricas_cache[nombre] = self._calcular_metrica(landmarks, config)
            
            # Actualizar contexto con nuevas métricas
            contexto.update(self.metricas_cache)
            
            # Validar errores
            for validacion in self.config['validaciones']:
                nombre_error = validacion['nombre']
                condicion = validacion['condicion']
                
                if self.validar_error_con_confirmacion(
                    nombre_error,
                    self._evaluar_condicion(condicion, contexto)
                ):
                    mensajes.append(validacion['mensaje'])
        
        # Resetear flags si hay nueva repetición
        if nueva_repeticion:
            self.resetear_flags_errores()
        
        # Mensaje por defecto
        if not mensajes and not self.mensaje_cache:
            mensaje_default = self.config['mensajes_guia'].get(self.estado_actual)
            if mensaje_default:
                mensajes.append(mensaje_default)
        
        # Actualizar mensaje con sistema de cache
        self.actualizar_mensaje_guia(mensajes if mensajes else None)
    
    # Métodos heredados de FASE 1 (copiados de base.py)
    
    def debe_verificar_errores(self) -> bool:
        """Determina si en este frame se deben verificar errores."""
        from config import ERROR_CHECK_INTERVAL
        self.frame_counter += 1
        return self.frame_counter % ERROR_CHECK_INTERVAL == 0
    
    def actualizar_mensaje_guia(self, nuevos_mensajes: Optional[List[str]]):
        """Actualiza el mensaje con sistema de cache y TTL."""
        from config import MENSAJE_ERROR_TTL
        
        if nuevos_mensajes:
            self.mensaje_cache = " | ".join(nuevos_mensajes)
            self.mensaje_timestamp = time.time()
            self.mensaje_guia = self.mensaje_cache
        elif self.mensaje_cache:
            if time.time() - self.mensaje_timestamp < MENSAJE_ERROR_TTL:
                self.mensaje_guia = self.mensaje_cache
            else:
                self.mensaje_cache = None
                self.mensaje_guia = ""
        else:
            self.mensaje_guia = ""
    
    def validar_error_con_confirmacion(self, error_name: str, condicion: bool) -> bool:
        """Valida un error requiriendo confirmación en frames consecutivos."""
        from config import ERROR_CONFIRMATION_FRAMES
        
        if condicion:
            self.error_confirmation_counters[error_name] += 1
            if self.error_confirmation_counters[error_name] >= ERROR_CONFIRMATION_FRAMES:
                if not self.error_flags.get(error_name, False):
                    self.errores_contador[error_name] += 1
                    self.error_flags[error_name] = True
                    return True
        else:
            self.error_confirmation_counters[error_name] = 0
        
        return False
    
    def resetear_flags_errores(self):
        """Resetea todos los flags de errores al completar una repetición."""
        for key in self.error_flags:
            self.error_flags[key] = False
        for key in self.error_confirmation_counters:
            self.error_confirmation_counters[key] = 0
    
    def dibujar_feedback(self, frame, landmarks):
        """Dibujar feedback visual basado en configuración."""
        import cv2
        import numpy as np
        
        height, width = frame.shape[:2]
        overlay = np.zeros_like(frame)
        
        def to_pixel(landmark):
            return int(landmark.x * width), int(landmark.y * height)
        
        # Dibujar líneas
        for linea in self.config['visualizacion']['lineas']:
            p1 = to_pixel(landmarks[linea['desde']])
            p2 = to_pixel(landmarks[linea['hasta']])
            color = tuple(linea['color'])
            grosor = linea['grosor']
            cv2.line(overlay, p1, p2, color, grosor)
        
        # Dibujar puntos
        for punto in self.config['visualizacion']['puntos']:
            px = to_pixel(landmarks[punto['landmark']])
            color = tuple(punto['color'])
            radio = punto['radio']
            cv2.circle(overlay, px, radio, color, -1)
        
        # Mostrar ángulo si está configurado
        if 'mostrar_angulo' in self.config['visualizacion']:
            angulo_config = self.config['visualizacion']['mostrar_angulo']
            punto_px = to_pixel(landmarks[angulo_config['punto']])
            metrica = self.metricas_cache.get(angulo_config['metrica'], 0)
            cv2.putText(overlay, f"{int(metrica)}°", 
                       (punto_px[0] + 20, punto_px[1] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        
        # Blend overlay
        frame = cv2.addWeighted(frame, 1, overlay, 0.6, 0)
        
        # Dibujar barra de progreso y mensajes (reutilizar de base.py)
        # ... (código similar a base.py)
        
        return frame
```

---

## 📈 COMPARACIÓN: ANTES vs DESPUÉS

### Agregar Nuevo Ejercicio: "Flexiones"

#### ❌ ANTES (Código Actual)
```python
# 1. Crear ejercicios/flexiones.py (~150 líneas)
class Flexiones(EjercicioBase):
    def __init__(self):
        super().__init__()
        self.estado_actual = "arriba"
        self.errores_contador = {...}  # 15 líneas
        self.error_flags = {...}        # 15 líneas
    
    def procesar_pose(self, landmarks):
        # Calcular ángulos (10 líneas)
        codo = (landmarks['RIGHT_ELBOW'].x, ...)
        hombro = (landmarks['RIGHT_SHOULDER'].x, ...)
        # ... 80 líneas más
        
        if self.debe_verificar_errores():
            # ... 40 líneas de validaciones
    
    def dibujar_feedback(self, frame, landmarks):
        # ... 30 líneas de dibujo

# 2. Modificar screens/seleccion_reps.py
# 3. Modificar screens/entrenamiento.py  
# 4. Testing manual completo

TOTAL: ~200 líneas código + 3 archivos modificados
```

#### ✅ DESPUÉS (Sistema Configurable)
```json
// ejercicios/configs/flexiones.json (~50 líneas)
{
  "metadata": {
    "nombre": "Flexiones de Pecho",
    "descripcion": "Ejercicio de empuje para pectorales y tríceps"
  },
  "anatomia": {
    "landmarks_principales": ["RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"]
  },
  "metricas_principales": {
    "angulo_codo": {
      "puntos": ["RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"],
      "tipo": "angulo_3_puntos"
    }
  },
  "maquina_estados": {
    "inicial": "arriba",
    "transiciones": [
      {"de": "arriba", "a": "bajando", "condicion": "angulo_codo < 90"},
      {"de": "bajando", "a": "arriba", "condicion": "angulo_codo > 160", "accion": "incrementar_repeticion"}
    ]
  },
  "validaciones": [
    {"nombre": "cadera_baja", "condicion": "RIGHT_HIP.y > RIGHT_SHOULDER.y", "mensaje": "Sube la cadera"}
  ]
}

// screens/seleccion_reps.py - Solo agregar a lista:
ejercicios = ["Sentadilla", "Estocada", ..., "Flexiones"]  # 1 palabra

TOTAL: 1 archivo JSON + 1 palabra en lista
```

**Reducción: 200 líneas → 50 líneas (~75% menos código)**

---

## ⚠️ DESVENTAJAS Y LIMITACIONES

### 1. **Complejidad Inicial Mayor**
- Requiere diseñar motor genérico robusto
- Más difícil de debuggear al principio
- Curva de aprendizaje para nuevo formato

### 2. **Menos Flexibilidad para Casos Extremos**
```python
# Fácil en código:
if ejercicio == "consalto" and detectar_salto_especial():
    hacer_algo_muy_custom()

# Difícil en config:
# Requeriría agregar "plugins" o "hooks"
```

### 3. **Performance (Muy Leve)**
- Evaluar condiciones con `eval()` es ~10-20% más lento que código nativo
- Para 3 FPS de errores: impacto insignificante (<5ms por frame)

### 4. **Validación de Configuración**
- JSON malformado puede romper todo
- Necesita schema validation robusto
- Errores menos claros que Python syntax errors

---

## 🎯 RECOMENDACIÓN FINAL

### ✅ **SÍ Estandarizar SI:**

1. **Planeas agregar 10+ ejercicios**
   - ROI positivo después de ~5 ejercicios
   
2. **Tienes colaboradores no-técnicos**
   - Entrenadores ajustando umbrales
   
3. **Necesitas A/B testing de parámetros**
   - Fácil crear variantes de ejercicio
   
4. **Quieres app configurable por usuario final**
   - JSON puede cargarse de servidor/API

### ⚠️ **NO Estandarizar SI:**

1. **Solo tienes 5 ejercicios actuales**
   - Mantener código actual es razonable
   
2. **Ejercicios muy heterogéneos**
   - Lógica muy custom entre ejercicios
   
3. **Equipo pequeño/temporal**
   - Overhead de mantenimiento del motor

---

## 🚀 RUTA DE IMPLEMENTACIÓN (Si decides hacerlo)

### FASE 2.5: Refactorización Opcional (Después de FASE 2)

**Paso 1: Prototipar Motor (2-3 días)**
- Implementar `ExerciseEngine` básico
- Convertir 1 ejercicio (sentadilla) a JSON
- Validar que funciona igual que antes

**Paso 2: Migrar Gradualmente (5-7 días)**
- Convertir ejercicios uno por uno
- Mantener código viejo como fallback
- Testing exhaustivo de cada migración

**Paso 3: Refinar Motor (2-3 días)**
- Agregar features faltantes
- Optimizar performance
- Mejorar validación de configs

**Paso 4: Limpieza (1-2 días)**
- Eliminar código viejo
- Documentar sistema
- Crear tutorial para agregar ejercicios

**TOTAL: ~10-15 días de desarrollo**

---

## 💡 PROPUESTA HÍBRIDA (Lo Mejor de Ambos Mundos)

### Opción Intermedia Recomendada:

```python
# ejercicios/base.py - Métodos reutilizables actuales ✅
class EjercicioBase:
    def debe_verificar_errores(self): ...
    def validar_error_con_confirmacion(self): ...
    # etc.

# ejercicios/configs/ - Solo datos, no lógica
sentadilla_config = {
    "umbrales": {"bajada": 90, "subida": 160},
    "errores": {
        "pies_juntos": {"umbral": 0.12, "mensaje": "Separa los pies"},
        # ...
    }
}

# ejercicios/sentadilla.py - Código + Config híbrido
class Sentadilla(EjercicioBase):
    def __init__(self):
        super().__init__()
        self.config = load_config('sentadilla')  # ⭐ Cargar desde JSON
    
    def procesar_pose(self, landmarks):
        # Lógica custom si es necesaria
        angulo = calcular_angulo(...)
        
        # Umbrales desde config
        if angulo < self.config['umbrales']['bajada']:
            # ...
        
        # Errores desde config (loop genérico)
        for nombre, params in self.config['errores'].items():
            if self.validar_error(nombre, params, landmarks):
                mensajes.append(params['mensaje'])
```

**Ventajas:**
- ✅ Externalizas datos (umbrales, mensajes)
- ✅ Mantienes flexibilidad en código Python
- ✅ Migración gradual posible
- ✅ Menos complejidad que motor completo

---

## 📊 RESUMEN EJECUTIVO

| Criterio | Código Actual | Sistema Config Completo | Híbrido |
|----------|---------------|-------------------------|---------|
| **Tiempo para nuevo ejercicio** | 4-6 horas | 30-60 min | 2-3 horas |
| **Líneas de código** | ~150 | ~50 JSON | ~80 |
| **Flexibilidad** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Mantenibilidad (5+ ejercicios)** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Complejidad inicial** | Baja | Alta | Media |
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Recomendado para** | 1-5 ejercicios | 10+ ejercicios | 5-15 ejercicios |

---

## 🎯 MI RECOMENDACIÓN FINAL

**Para tu caso (planeas agregar más ejercicios):**

1. **AHORA:** Mantener código actual + completar FASE 2 (audio)
2. **DESPUÉS:** Implementar **Sistema Híbrido**
   - Externalizar umbrales y mensajes a JSON
   - Mantener lógica de estado en Python
   - Crear helpers genéricos en `base.py`
3. **FUTURO:** Si llegas a 10+ ejercicios, considerar motor completo

**Justificación:**
- ✅ No interrumpe desarrollo actual
- ✅ Mejora incremental sin reescribir todo
- ✅ ROI positivo desde el primer ejercicio migrado
- ✅ Mantiene flexibilidad para casos custom

---

**¿Te gustaría que implemente el sistema híbrido después de FASE 2, o prefieres mantener el código actual y enfocarte en agregar más ejercicios directamente?** 🤔
