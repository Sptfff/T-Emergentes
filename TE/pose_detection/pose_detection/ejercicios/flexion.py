import math
from detector.pose_detector import calcular_angulo
from playsound import playsound
import threading
import os

from ejercicios.ejercicio_interfaz import Ejercicio_interfaz

class Flexion(Ejercicio_interfaz):
    def __init__(self):
        self.feedback = ""
        self.audio_path = "audios_feedback"
        self.mensajes_audio = {
            "Cuerpo desalineado, manténlo recto.": "cuerpo_desalineado.mp3",
            "Baja más para completar la flexión.": "bajar_mas_flexion.mp3",
            "Evita que los codos se abran demasiado.": "codos_abiertos.mp3",
            "Buena tecnica!": "buena_tecnica.mp3"
        }

    def reproducir_audio(self, mensaje):
        archivo = self.mensajes_audio.get(mensaje)
        if archivo:
            ruta = os.path.join(self.audio_path, archivo)
            if os.path.exists(ruta):
                print(f"Reproduciendo: {ruta}")
                threading.Thread(target=playsound, args=(ruta,), daemon=True).start()

    def verificar(self, puntos_clave):
        hombro_izquierdo = puntos_clave[11]
        codo_izquierdo = puntos_clave[13]
        muñeca_izquierda = puntos_clave[15]
        cadera_izquierda = puntos_clave[23]
        rodilla_izquierda = puntos_clave[25]
        tobillo_izquierdo = puntos_clave[27]

        hombro_derecho = puntos_clave[12]
        codo_derecho = puntos_clave[14]
        muñeca_derecha = puntos_clave[16]
        cadera_derecha = puntos_clave[24]
        rodilla_derecha = puntos_clave[26]
        tobillo_derecho = puntos_clave[28]

        # Elegimos un lado como referencia (derecho si se ve bien de perfil)
        hombro = hombro_derecho
        codo = codo_derecho
        muñeca = muñeca_derecha
        cadera = cadera_derecha
        rodilla = rodilla_derecha
        tobillo = tobillo_derecho

        errores = []

        # Ángulo del codo
        angulo_codo = calcular_angulo(hombro, codo, muñeca)

        # Rectitud del cuerpo: hombro - cadera - tobillo
        angulo_cuerpo = calcular_angulo(hombro, cadera, tobillo)

        # Verificaciones:
        if angulo_cuerpo < 160:  # Muy curvado
            errores.append("Cuerpo desalineado, manténlo recto.")

        if angulo_codo > 130:  # No ha bajado suficiente
            errores.append("Baja más para completar la flexión.")

        # (Opcional: podrías agregar si los codos se abren lateralmente con una lógica más compleja)

        # Generar feedback
        if errores:
            self.feedback = "\n".join(errores)
            for mensaje in errores:
                self.reproducir_audio(mensaje)
        else:
            self.feedback = "Buena tecnica!"
            self.reproducir_audio(self.feedback)

        # Como ejemplo, progreso depende de cuán cerca esté el ángulo del codo a 90°
        progreso = max(0, min(100, 100 - abs(angulo_codo - 90)))
        return self.feedback, progreso
