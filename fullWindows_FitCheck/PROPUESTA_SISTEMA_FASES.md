# Sistema de Fases para Ejercicios - Propuesta Técnica

## 🎯 Problema Actual

La barra de progreso se calcula linealmente basándose únicamente en el ángulo, sin considerar:
- No se resetea entre repeticiones
- No distingue entre fase descendente y ascendente
- El 0% y 100% representan el mismo punto físico (posición inicial)
- No hay forma de identificar estados de "reposo" vs "ejecución"

## 💡 Solución Propuesta: Sistema de Fases

### Concepto Base
Similar a cómo distinguimos `"izquierda"` y `"derecha"`, crear un sistema que identifique **fases del movimiento**:

```python
# Ejemplo para Sentadilla
FASES = {
    "reposo_inicial": {
        "condicion": "angulo > 160 y velocidad baja",
        "progreso_visual": 0.0,
        "transicion_a": "descendente"
    },
    "descendente": {
        "condicion": "angulo decreciendo hacia 90",
        "progreso_visual": "0.0 -> 0.5",  # Primera mitad de la barra
        "transicion_a": "punto_bajo"
    },
    "punto_bajo": {
        "condicion": "angulo < 100 y velocidad baja",
        "progreso_visual": 0.5,
        "transicion_a": "ascendente"
    },
    "ascendente": {
        "condicion": "angulo creciendo hacia 160",
        "progreso_visual": "0.5 -> 1.0",  # Segunda mitad de la barra
        "transicion_a": "completado"
    },
    "completado": {
        "condicion": "angulo > 160",
        "progreso_visual": 1.0,
        "transicion_a": "reposo_inicial"  # Reset automático
    }
}
```

### Flujo Visual

```
SENTADILLA:
┌─────────────┐
│ REPOSO      │ ángulo: 170°  →  Barra: ████░░░░░░ 0%
│ (inicial)   │                   Mensaje: "Comienza a bajar"
└─────────────┘
       ↓ (persona baja)
┌─────────────┐
│ DESCENDENTE │ ángulo: 130°  →  Barra: ████████░░ 25%
│             │                   Mensaje: "Continúa bajando"
└─────────────┘
       ↓
┌─────────────┐
│ PUNTO BAJO  │ ángulo: 85°   →  Barra: ██████████ 50%
│             │                   Mensaje: "¡Bien! Ahora sube"
└─────────────┘
       ↓ (persona sube)
┌─────────────┐
│ ASCENDENTE  │ ángulo: 120°  →  Barra: ███████████████ 75%
│             │                   Mensaje: "Continúa subiendo"
└─────────────┘
       ↓
┌─────────────┐
│ COMPLETADO  │ ángulo: 165°  →  Barra: ████████████████████ 100%
│             │                   Mensaje: "¡Repetición completa!"
└─────────────┘
       ↓ (auto-reset)
┌─────────────┐
│ REPOSO      │ ángulo: 170°  →  Barra: ████░░░░░░ 0%  ← RESET
│ (nuevo)     │                   Mensaje: "Comienza siguiente"
└─────────────┘
```

## 🔧 Implementación Técnica

### 1. Atributos Nuevos en `EjercicioBase`

```python
class EjercicioBase:
    def __init__(self):
        # ... atributos existentes ...
        
        # Sistema de fases
        self.fase_actual = "reposo_inicial"
        self.fases_config = {}  # Definido por cada ejercicio
        self.progreso_fase = 0.0  # Progreso dentro de la fase actual (0.0-1.0)
        self.progreso_total = 0.0  # Progreso total de la repetición (0.0-1.0)
        
        # Detección de reposo/movimiento
        self.historial_angulos = []  # Últimos 5-10 frames
        self.velocidad_movimiento = 0.0
        self.umbral_reposo = 3.0  # grados/frame
```

### 2. Métodos Auxiliares

```python
def calcular_velocidad_movimiento(self, angulo_actual):
    """
    Calcula velocidad de cambio del ángulo principal
    Útil para detectar estados de reposo
    """
    self.historial_angulos.append(angulo_actual)
    if len(self.historial_angulos) > 10:
        self.historial_angulos.pop(0)
    
    if len(self.historial_angulos) >= 3:
        # Velocidad = cambio promedio en últimos 3 frames
        cambios = [abs(self.historial_angulos[i] - self.historial_angulos[i-1]) 
                   for i in range(1, len(self.historial_angulos))]
        self.velocidad_movimiento = sum(cambios) / len(cambios)
    
    return self.velocidad_movimiento

def esta_en_reposo(self):
    """Determina si la persona está en reposo basado en velocidad"""
    return self.velocidad_movimiento < self.umbral_reposo

def actualizar_fase_y_progreso(self, angulo_principal):
    """
    Lógica central del sistema de fases
    Actualiza fase_actual y progreso_total basándose en las transiciones
    """
    self.calcular_velocidad_movimiento(angulo_principal)
    
    fase_config = self.fases_config.get(self.fase_actual, {})
    condicion_transicion = fase_config.get("condicion_transicion")
    
    # Evaluar si debe cambiar de fase
    if condicion_transicion and condicion_transicion(angulo_principal, self):
        siguiente_fase = fase_config.get("siguiente_fase")
        if siguiente_fase:
            self.fase_actual = siguiente_fase
            
            # Si completó repetición, incrementar contador
            if self.fase_actual == "completado":
                self.repeticiones += 1
                # Auto-reset a reposo_inicial después de breve pausa
                self.fase_actual = "reposo_inicial"
    
    # Calcular progreso visual según la fase
    self.progreso_total = self.calcular_progreso_por_fase(angulo_principal)
    
    return self.progreso_total
```

### 3. Configuración por Ejercicio (Ejemplo: Sentadilla)

```python
class Sentadilla(EjercicioBase):
    def __init__(self):
        super().__init__()
        
        # Configurar fases específicas de sentadilla
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
                "condicion_transicion": lambda ang, obj: True,  # Auto-reset inmediato
                "siguiente_fase": "reposo_inicial",
                "mensaje": "¡Repetición completa!"
            }
        }
        
        self.fase_actual = "reposo_inicial"
    
    def calcular_progreso_por_fase(self, angulo):
        """Calcula progreso visual basado en fase actual"""
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
        # Calcular ángulo
        angulo_rodilla = calcular_angulo(cadera, rodilla, tobillo)
        
        # Actualizar fase y progreso (REEMPLAZA el cálculo lineal actual)
        self.progreso = self.actualizar_fase_y_progreso(angulo_rodilla)
        
        # El resto de la lógica permanece igual...
```

## 🎨 Ventajas del Sistema

### 1. **Progreso Visual Intuitivo**
- ✅ Barra se resetea automáticamente después de cada repetición
- ✅ 0% = inicio, 50% = punto medio, 100% = completado
- ✅ Flujo visual claro: vacío → medio lleno → lleno → vacío

### 2. **Base para Sistema Híbrido**
- ✅ Configuración declarativa (JSON-friendly)
- ✅ Fácil de extender a nuevos ejercicios
- ✅ Separación clara: configuración vs lógica

### 3. **Detección Inteligente**
- ✅ Distingue reposo vs movimiento (velocidad angular)
- ✅ Evita conteos prematuros
- ✅ Transiciones suaves entre fases

### 4. **Mensajes Contextuales**
- ✅ Cada fase puede tener su mensaje específico
- ✅ Guía al usuario durante el movimiento
- ✅ Feedback más preciso

## 📋 Ejemplo de Configuración JSON (Futuro Sistema Híbrido)

```json
{
  "nombre": "Sentadilla",
  "angulo_principal": "rodilla_derecha",
  "fases": [
    {
      "id": "reposo_inicial",
      "progreso": 0.0,
      "transicion": {
        "condicion": "angulo < 155 AND velocidad > umbral_reposo",
        "siguiente": "descendente"
      },
      "mensaje": "Comienza a bajar",
      "audio": "Preparate para bajar"
    },
    {
      "id": "descendente",
      "progreso": {"tipo": "lineal", "rango": [0.0, 0.5]},
      "angulos": {"inicio": 160, "fin": 90},
      "transicion": {
        "condicion": "angulo < 100",
        "siguiente": "punto_bajo"
      },
      "mensaje": "Continúa bajando",
      "validaciones": [
        {"tipo": "espalda_recta", "critico": true},
        {"tipo": "rodillas_alineadas", "critico": false}
      ]
    },
    {
      "id": "punto_bajo",
      "progreso": 0.5,
      "transicion": {
        "condicion": "angulo > 95 AND velocidad > umbral_reposo",
        "siguiente": "ascendente"
      },
      "mensaje": "¡Bien! Ahora sube",
      "audio": "Muy bien, ahora sube"
    },
    {
      "id": "ascendente",
      "progreso": {"tipo": "lineal", "rango": [0.5, 1.0]},
      "angulos": {"inicio": 90, "fin": 160},
      "transicion": {
        "condicion": "angulo > 155",
        "siguiente": "completado"
      },
      "mensaje": "Continúa subiendo"
    },
    {
      "id": "completado",
      "progreso": 1.0,
      "transicion": {
        "condicion": "true",
        "siguiente": "reposo_inicial"
      },
      "mensaje": "¡Repetición completa!",
      "audio": "Excelente repeticion",
      "acciones": ["incrementar_contador", "resetear_flags"]
    }
  ]
}
```

## 🚀 Plan de Implementación

### Fase 1: Prototipo en EjercicioBase (2-3 días)
1. Añadir atributos de sistema de fases
2. Implementar métodos auxiliares (velocidad, reposo, transiciones)
3. Crear `actualizar_fase_y_progreso()`

### Fase 2: Migrar Sentadilla (1 día)
1. Definir `fases_config` en `__init__`
2. Implementar `calcular_progreso_por_fase()`
3. Reemplazar cálculo lineal de progreso
4. Probar exhaustivamente

### Fase 3: Generalizar (2-3 días)
1. Migrar otros 4 ejercicios
2. Refinar lógica de transiciones
3. Ajustar umbrales según pruebas

### Fase 4: Preparar JSON (1-2 días)
1. Documentar schema de configuración
2. Crear parser de fases desde JSON
3. Validar que sea backward-compatible

## ❓ Decisión Requerida

**¿Quieres que implemente este sistema ahora o prefieres:**
1. **Implementar prototipo básico** (sistema de fases sin JSON, hardcodeado en Python)
2. **Esperar al sistema híbrido completo** (con JSON y todo el plan de 15 días)
3. **Solución intermedia rápida** (simplemente resetear progreso en cada repetición sin fases)

La opción 1 tomaría ~1-2 días y sería la base perfecta para el sistema híbrido.
La opción 3 tomaría ~1 hora y resolvería el problema visual inmediatamente.
