# PLAN DE EJECUCIÓN: SISTEMA HÍBRIDO DE CONFIGURACIÓN

## 📋 Resumen Ejecutivo

**Objetivo:** Transformar el sistema actual de ejercicios de código hard-coded a un sistema híbrido donde los **datos** (umbrales, mensajes, validaciones) están externalizados en archivos JSON, mientras que la **lógica** permanece en Python.

**Beneficios:**
- ✅ Agregar ejercicio: 4-6 horas → 2-3 horas (~50% reducción)
- ✅ Ajustar umbrales: editar JSON vs recompilar código
- ✅ Modificar mensajes: editar JSON sin tocar Python
- ✅ Versionar configuraciones independiente del código

**Tiempo Estimado Total:** 12-15 días de desarrollo

---

## 🎯 FASE 1: ANÁLISIS Y DISEÑO (2-3 días)

### Día 1: Análisis de Patrones Comunes

#### Tareas:
1. **Inventario de Ejercicios Actuales**
   - Documentar estructura de cada ejercicio
   - Identificar patrones compartidos
   - Mapear diferencias únicas

2. **Extracción de Datos Configurables**
   ```
   Por cada ejercicio, identificar:
   ├── Landmarks utilizados (principales y secundarios)
   ├── Métricas calculadas (ángulos, distancias, etc.)
   ├── Umbrales de estado (bajada, subida, etc.)
   ├── Umbrales de errores
   ├── Mensajes (errores, guías, completación)
   └── Configuración visual (líneas, puntos, colores)
   ```

3. **Análisis de Dependencias**
   - Funciones compartidas en `pose_utils.py`
   - Métodos de `EjercicioBase`
   - Flujos de estado únicos vs genéricos

#### Entregables:
- ✅ Documento: `ANALISIS_EJERCICIOS.md`
- ✅ Tabla comparativa de ejercicios
- ✅ Lista de elementos configurables

---

### Día 2-3: Diseño del Schema JSON

#### Tareas:
1. **Diseñar Estructura JSON**
   ```json
   {
     "metadata": {...},           // Nombre, descripción, dificultad
     "anatomia": {...},           // Landmarks usados
     "metricas": {...},           // Qué calcular y cuándo
     "maquina_estados": {...},    // Transiciones de estado
     "progreso": {...},           // Cómo calcular progreso
     "validaciones": [...],       // Errores a detectar
     "mensajes": {...},           // Textos por situación
     "visualizacion": {...}       // Líneas, puntos, colores
   }
   ```

2. **Crear Schema de Validación**
   - Usar JSON Schema Draft-07
   - Definir tipos de datos
   - Validaciones de rangos
   - Propiedades requeridas vs opcionales

3. **Prototipar 1 Ejercicio Completo**
   - Convertir `sentadilla.py` a JSON
   - Documentar decisiones de diseño
   - Identificar casos edge

#### Entregables:
- ✅ `ejercicios/configs/schema.json` - Schema de validación
- ✅ `ejercicios/configs/sentadilla.json` - Prototipo completo
- ✅ Documento: `DISEÑO_SCHEMA.md` con justificaciones

---

## 🔧 FASE 2: IMPLEMENTACIÓN DEL CORE (4-5 días)

### Día 4-5: ConfigLoader y Validación

#### Tareas:
1. **Crear `utils/config_loader.py`**
   ```python
   class ConfigLoader:
       - load_exercise_config(nombre)
       - validate_config(config, schema)
       - get_all_exercises()
       - reload_config(nombre)
   ```

2. **Implementar Validación JSON Schema**
   ```python
   import jsonschema
   
   def validar_configuracion(config, schema):
       # Validar estructura
       # Validar tipos de datos
       # Validar rangos
       # Logging de errores
   ```

3. **Sistema de Cache**
   - Cachear configs cargados
   - Detección de cambios en archivos
   - Hot-reload opcional

4. **Testing Unitario**
   - Tests de carga correcta
   - Tests de validación
   - Tests de errores (configs inválidos)

#### Entregables:
- ✅ `utils/config_loader.py` (200-250 líneas)
- ✅ `tests/test_config_loader.py`
- ✅ Documentación de API

---

### Día 6-7: Refactorización de EjercicioBase

#### Tareas:
1. **Agregar Soporte de Configuración**
   ```python
   class EjercicioBase:
       def __init__(self, config_path=None):
           if config_path:
               self.config = ConfigLoader.load(config_path)
           else:
               self.config = None  # Modo legacy
   ```

2. **Métodos Helper Genéricos**
   ```python
   def calcular_metrica_generica(self, landmarks, metrica_config):
       """Calcula métrica según tipo (ángulo, distancia, etc.)"""
   
   def evaluar_transicion_estado(self, contexto):
       """Evalúa transiciones de máquina de estados"""
   
   def validar_errores_desde_config(self, landmarks):
       """Valida errores definidos en config"""
   ```

3. **Modo Híbrido (Backward Compatibility)**
   - Si `self.config` existe → usar sistema nuevo
   - Si no → usar métodos legacy (código actual)
   - Ambos modos funcionan simultáneamente

4. **Refactorizar Métodos de Dibujo**
   ```python
   def dibujar_desde_config(self, frame, landmarks):
       """Dibuja líneas/puntos según config.visualizacion"""
   ```

#### Entregables:
- ✅ `ejercicios/base.py` modificado (400-450 líneas)
- ✅ Tests de backward compatibility
- ✅ Documentación de migración

---

### Día 8: Sistema de Evaluación de Expresiones

#### Tareas:
1. **Crear `utils/expression_evaluator.py`**
   ```python
   class ExpressionEvaluator:
       """
       Evalúa expresiones seguras desde configs
       
       Ejemplos:
       - "angulo_rodilla < 90"
       - "distancia_pies < 0.12"
       - "RIGHT_KNEE.y < RIGHT_ANKLE.y"
       """
       
       def evaluar(self, expresion, contexto):
           # Parsear expresión
           # Validar seguridad (sin eval malicioso)
           # Ejecutar con contexto
   ```

2. **Sistema de Contexto**
   ```python
   def crear_contexto(self, landmarks, metricas):
       """
       Crea diccionario con:
       - Landmarks: RIGHT_HIP, LEFT_KNEE, etc.
       - Métricas: angulo_rodilla, distancia_pies, etc.
       - Constantes: PI, etc.
       """
   ```

3. **Testing de Seguridad**
   - Validar que no se pueden ejecutar comandos
   - Validar que solo accede a contexto provisto
   - Tests de expresiones complejas

#### Entregables:
- ✅ `utils/expression_evaluator.py` (150-200 líneas)
- ✅ Tests de seguridad
- ✅ Documentación de sintaxis soportada

---

## 🔄 FASE 3: MIGRACIÓN DE EJERCICIOS (3-4 días)

### Día 9: Migración de Sentadilla (Piloto)

#### Tareas:
1. **Crear Clase Híbrida**
   ```python
   class Sentadilla(EjercicioBase):
       def __init__(self):
           config_path = "ejercicios/configs/sentadilla.json"
           super().__init__(config_path)
       
       def procesar_pose(self, landmarks):
           if self.config:
               # Usar sistema nuevo
               return self.procesar_pose_desde_config(landmarks)
           else:
               # Usar código legacy (backup)
               return self.procesar_pose_legacy(landmarks)
   ```

2. **Validación Exhaustiva**
   - Comparar resultados nuevo vs legacy
   - Testing con videos de prueba
   - Métricas de precisión

3. **Documentación de Proceso**
   - Pasos seguidos
   - Problemas encontrados
   - Soluciones aplicadas
   - Tiempos reales

#### Entregables:
- ✅ `sentadilla.py` migrado
- ✅ `configs/sentadilla.json` completo
- ✅ Tests comparativos
- ✅ Guía de migración

---

### Día 10-11: Migración de Estocada, Step-Up, ConSalto

#### Tareas (por ejercicio):
1. **Análisis Específico**
   - Identificar peculiaridades
   - Mapear estados únicos
   - Documentar diferencias con sentadilla

2. **Crear Configuración JSON**
   - Copiar template de sentadilla
   - Ajustar landmarks
   - Ajustar métricas
   - Ajustar validaciones

3. **Refactorizar Clase Python**
   - Implementar modo híbrido
   - Mantener código legacy como fallback
   - Testing exhaustivo

4. **Validación Cruzada**
   - Probar con usuarios reales
   - Comparar detección de errores
   - Ajustar umbrales si es necesario

#### Entregables (por ejercicio):
- ✅ `ejercicio.py` migrado
- ✅ `configs/ejercicio.json` completo
- ✅ Tests pasando

---

### Día 12: Migración de Sumo + Limpieza

#### Tareas:
1. **Migrar Último Ejercicio**
   - Aplicar proceso estandarizado
   - Testing completo

2. **Limpieza de Código Legacy**
   - Decidir si eliminar código viejo
   - Archivar en branch `legacy`
   - Actualizar imports

3. **Optimización Global**
   - Refactorizar código duplicado
   - Mejorar performance
   - Reducir complejidad ciclomática

#### Entregables:
- ✅ Todos los ejercicios migrados
- ✅ Código legacy removido/archivado
- ✅ Tests globales pasando

---

## 📚 FASE 4: DOCUMENTACIÓN Y HERRAMIENTAS (2-3 días)

### Día 13: Documentación Técnica

#### Tareas:
1. **Guía de Usuario**
   ```markdown
   - Cómo crear un nuevo ejercicio
   - Cómo modificar umbrales
   - Cómo ajustar mensajes
   - Cómo personalizar visualización
   ```

2. **Referencia de API**
   - ConfigLoader
   - ExpressionEvaluator
   - EjercicioBase híbrido
   - Schema JSON completo

3. **Ejemplos Prácticos**
   - Template de ejercicio nuevo
   - Casos de uso comunes
   - Troubleshooting

#### Entregables:
- ✅ `GUIA_CONFIGURACION.md`
- ✅ `API_REFERENCE.md`
- ✅ `TEMPLATE_EJERCICIO.json`

---

### Día 14: Herramientas de Desarrollo

#### Tareas:
1. **Validador de Configuración**
   ```bash
   python tools/validar_config.py ejercicios/configs/sentadilla.json
   # Output: ✅ Configuración válida
   ```

2. **Generador de Ejercicios**
   ```bash
   python tools/crear_ejercicio.py "Flexiones" --template sentadilla
   # Crea: ejercicios/flexiones.py + configs/flexiones.json
   ```

3. **Comparador de Configs**
   ```bash
   python tools/comparar_configs.py sentadilla.json estocada.json
   # Muestra diferencias clave
   ```

4. **Hot-Reload para Desarrollo**
   - Detectar cambios en JSON
   - Recargar sin reiniciar app
   - Útil para ajustar umbrales en tiempo real

#### Entregables:
- ✅ `tools/validar_config.py`
- ✅ `tools/crear_ejercicio.py`
- ✅ `tools/comparar_configs.py`
- ✅ Hot-reload integrado (opcional)

---

### Día 15: Testing Final y Refinamiento

#### Tareas:
1. **Testing de Integración**
   - Probar todos los ejercicios
   - Validar transiciones entre ejercicios
   - Testing de edge cases

2. **Testing de Performance**
   - Comparar FPS antes/después
   - Medir overhead de carga de JSON
   - Optimizar si es necesario

3. **Testing con Usuarios**
   - Beta testing con 3-5 usuarios
   - Recopilar feedback
   - Ajustar UX si es necesario

4. **Refinamiento Final**
   - Fix de bugs encontrados
   - Ajustes de configuración
   - Mejoras de usabilidad

#### Entregables:
- ✅ Todos los tests pasando
- ✅ Documentación actualizada
- ✅ Release notes
- ✅ Sistema listo para producción

---

## 📦 REQUISITOS TÉCNICOS

### Dependencias Nuevas
```txt
jsonschema==4.20.0     # Validación de JSON
pyyaml==6.0.1          # Soporte YAML opcional
watchdog==3.0.0        # Hot-reload (opcional)
```

### Estructura de Archivos
```
fullWindows_FitCheck/
├── ejercicios/
│   ├── configs/
│   │   ├── schema.json              # ⭐ NUEVO
│   │   ├── sentadilla.json          # ⭐ NUEVO
│   │   ├── estocada.json            # ⭐ NUEVO
│   │   ├── step_up.json             # ⭐ NUEVO
│   │   ├── consalto.json            # ⭐ NUEVO
│   │   └── sumo.json                # ⭐ NUEVO
│   ├── base.py                      # MODIFICADO
│   ├── sentadilla.py                # MODIFICADO (híbrido)
│   ├── estocada.py                  # MODIFICADO (híbrido)
│   ├── step_up.py                   # MODIFICADO (híbrido)
│   ├── consalto.py                  # MODIFICADO (híbrido)
│   └── sumo.py                      # MODIFICADO (híbrido)
├── utils/
│   ├── config_loader.py             # ⭐ NUEVO
│   ├── expression_evaluator.py     # ⭐ NUEVO
│   └── validators.py                # ⭐ NUEVO
├── tools/
│   ├── validar_config.py            # ⭐ NUEVO
│   ├── crear_ejercicio.py           # ⭐ NUEVO
│   └── comparar_configs.py          # ⭐ NUEVO
├── tests/
│   ├── test_config_loader.py        # ⭐ NUEVO
│   ├── test_expression_evaluator.py # ⭐ NUEVO
│   └── test_ejercicios_hibridos.py  # ⭐ NUEVO
└── docs/
    ├── GUIA_CONFIGURACION.md        # ⭐ NUEVO
    ├── API_REFERENCE.md             # ⭐ NUEVO
    └── MIGRACION_HIBRIDA.md         # ⭐ NUEVO
```

---

## ⚠️ RIESGOS Y MITIGACIONES

### Riesgo 1: Complejidad Excesiva
**Descripción:** Sistema demasiado complejo para casos simples  
**Probabilidad:** Media  
**Impacto:** Alto  
**Mitigación:**
- Mantener modo legacy como fallback
- Implementar progresivamente
- Documentación exhaustiva

### Riesgo 2: Performance
**Descripción:** Overhead de parsing JSON afecta FPS  
**Probabilidad:** Baja  
**Impacto:** Alto  
**Mitigación:**
- Cachear configs en memoria
- Cargar una sola vez al inicio
- Profiling antes/después

### Riesgo 3: Expresiones Inseguras
**Descripción:** Evaluación de expresiones permite código malicioso  
**Probabilidad:** Baja  
**Impacto:** Crítico  
**Mitigación:**
- No usar `eval()` directamente
- Parser seguro de expresiones
- Whitelist de operaciones
- Sandbox de contexto

### Riesgo 4: Backward Compatibility
**Descripción:** Romper código existente  
**Probabilidad:** Media  
**Impacto:** Alto  
**Mitigación:**
- Modo híbrido (nuevo + legacy)
- Tests exhaustivos de regresión
- Branch separado para testing

### Riesgo 5: Curva de Aprendizaje
**Descripción:** Equipo necesita aprender nuevo sistema  
**Probabilidad:** Alta  
**Impacto:** Medio  
**Mitigación:**
- Documentación clara con ejemplos
- Video tutoriales
- Template listo para copiar
- Workshops internos

---

## 🎯 CRITERIOS DE ÉXITO

### Funcionales
- ✅ Todos los ejercicios funcionan igual que antes
- ✅ Agregar nuevo ejercicio < 3 horas
- ✅ Modificar umbrales sin tocar Python
- ✅ Sin regresiones en detección de errores

### No Funcionales
- ✅ FPS mantiene 15 (sin degradación)
- ✅ Memoria: +10% máximo por configs
- ✅ Startup time: +500ms máximo
- ✅ Tests: >90% coverage

### Documentación
- ✅ Guía completa para crear ejercicio
- ✅ API documentada
- ✅ Ejemplos funcionales
- ✅ Troubleshooting guide

---

## 📊 MÉTRICAS DE PROGRESO

### KPIs por Fase

| Fase | Días | Archivos Nuevos | Líneas Código | Tests | Docs |
|------|------|-----------------|---------------|-------|------|
| Análisis | 3 | 2 | 0 | 0 | 3 |
| Core | 5 | 3 | ~600 | 15+ | 2 |
| Migración | 4 | 5 configs | ~200 | 25+ | 1 |
| Docs | 3 | 8 | ~400 | 5+ | 5 |
| **TOTAL** | **15** | **18** | **~1200** | **45+** | **11** |

### Checkpoints de Revisión

**Checkpoint 1 (Día 3):** Aprobar diseño de schema  
**Checkpoint 2 (Día 8):** Core funcional y testeado  
**Checkpoint 3 (Día 12):** Todos los ejercicios migrados  
**Checkpoint 4 (Día 15):** Release candidate listo  

---

## 🚀 POST-IMPLEMENTACIÓN

### Mes 1: Estabilización
- Monitorear bugs en producción
- Recopilar feedback de usuarios
- Ajustes menores de configuración

### Mes 2: Optimización
- Análisis de performance real
- Optimizar hot paths
- Mejorar herramientas de desarrollo

### Mes 3: Expansión
- Agregar 5+ ejercicios nuevos usando sistema
- Validar tiempo real de desarrollo
- Documentar aprendizajes

---

## 💰 ESTIMACIÓN DE ESFUERZO

### Desarrollador Senior (100%)
- **15 días laborables** × 8 horas = **120 horas**
- Incluye: análisis, desarrollo, testing, documentación

### Breakdown por Actividad
- Análisis y Diseño: 24h (20%)
- Desarrollo Core: 40h (33%)
- Migración: 32h (27%)
- Testing: 16h (13%)
- Documentación: 8h (7%)

### Recursos Adicionales (Opcionales)
- QA Tester (Día 13-15): 24h
- Technical Writer (Día 13-14): 16h
- **Total con recursos:** 160h

---

## 📅 CRONOGRAMA VISUAL

```
Semana 1: Fundación
├─ Día 1-3: Análisis ████████
└─ Día 4-5: ConfigLoader ████████

Semana 2: Core + Piloto
├─ Día 6-7: EjercicioBase ████████
├─ Día 8: ExpressionEvaluator ████████
└─ Día 9: Sentadilla Piloto ████████

Semana 3: Migración + Docs
├─ Día 10-12: Migración 4 ejercicios ████████
└─ Día 13-15: Docs + Testing ████████
```

---

## ✅ DECISIÓN: GO / NO-GO

### Recomendación: **GO CON CONDICIONES**

**Condiciones para GO:**
1. ✅ Aprobar presupuesto de 120-160 horas
2. ✅ Completar FASE 1 + FASE 2 actuales primero
3. ✅ Tener al menos 2 usuarios beta para testing
4. ✅ Backup completo de código actual
5. ✅ Plan de rollback definido

**Señales para NO-GO:**
- ❌ Solo tienes 1-3 ejercicios totales
- ❌ No planeas agregar más ejercicios
- ❌ Equipo < 2 personas
- ❌ Sin tiempo para mantenimiento (3+ meses)

---

## 📞 PRÓXIMOS PASOS INMEDIATOS

1. **Revisar este plan** con stakeholders
2. **Aprobar presupuesto** y timeline
3. **Crear branch** `feature/sistema-hibrido`
4. **Iniciar Día 1** de análisis
5. **Setup de tracking** de métricas

---

## 📝 NOTAS FINALES

Este plan es **flexible y adaptable**. Ajustar según:
- Complejidad real descubierta durante análisis
- Feedback de testing temprano
- Recursos disponibles
- Prioridades cambiantes

**Mantener comunicación constante y checkpoints frecuentes.**

---

**Preparado por:** GitHub Copilot  
**Fecha:** Octubre 2025  
**Versión:** 1.0  
**Estado:** Pendiente de Aprobación
