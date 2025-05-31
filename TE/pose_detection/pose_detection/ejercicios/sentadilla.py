import math
import os
import threading
import queue
import time
import pygame

from detector.pose_detector import calcular_angulo
from ejercicios.ejercicio_interfaz import Ejercicio_interfaz


class ReproductorAudio:
    def __init__(self, carpeta_audio):
        pygame.mixer.init()
        self.audio_path = carpeta_audio
        self.cola = queue.Queue()
        self.hilo = threading.Thread(target=self.reproducir_en_cola, daemon=True)
        self.hilo.start()

    def agregar_audio(self, archivo):
        ruta = os.path.join(self.audio_path, archivo)
        if os.path.exists(ruta):
            self.cola.put(ruta)
        else:
            print(f"[ERROR] Archivo no encontrado: {ruta}")

    def reproducir_en_cola(self):
        while True:
            ruta = self.cola.get()
            try:
                pygame.mixer.music.load(ruta)
                pygame.mixer.music.play()
                print(f"[DEBUG] Reproduciendo: {ruta}")
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            except Exception as e:
                print(f"[ERROR] Error al reproducir {ruta}: {e}")
            self.cola.task_done()


class Sentadilla(Ejercicio_interfaz):
    def __init__(self):
        self.feedback = ""
        self.mensajes_audio = {
            "Cuidado con la retroversion pelvica.": "retroversion_pelvica.mp3",
            "Debes bajar mas para completar la sentadilla.": "bajar_mas.mp3",
            "Mantén el torso mas erguido.": "torso_erguido.mp3",
            "No levantes los talones del suelo.": "no_levantes_talones.mp3",
            "Buena tecnica!": "buena_tecnica.mp3"
        }
        ruta_audio = os.path.join(os.path.dirname(__file__), "audios_feedback")
        self.reproductor = ReproductorAudio(ruta_audio)

    def reproducir_audio(self, mensaje):
        archivo = self.mensajes_audio.get(mensaje)
        if archivo:
            self.reproductor.agregar_audio(archivo)

    def verificar(self, puntos_clave):
        hombro_izquierdo = puntos_clave[11]
        hombro_derecho = puntos_clave[12]
        cadera_izquierda = puntos_clave[23]
        rodilla_izquierda = puntos_clave[25]
        tobillo_izquierdo = puntos_clave[27]
        cadera_derecha = puntos_clave[24]
        rodilla_derecha = puntos_clave[26]
        tobillo_derecho = puntos_clave[28]
        talon_izquierdo = puntos_clave[29]
        talon_derecho = puntos_clave[30]
        punta_pie_izquierda = puntos_clave[31]
        punta_pie_derecha = puntos_clave[32]

        mirando_izquierda = hombro_izquierdo[0] > hombro_derecho[0]

        if mirando_izquierda:
            cadera = cadera_derecha
            rodilla = rodilla_derecha
            tobillo = tobillo_derecho
            hombro = hombro_derecho
            talon = talon_derecho
            punta_pie = punta_pie_derecha
            otra_cadera = cadera_izquierda
        else:
            cadera = cadera_izquierda
            rodilla = rodilla_izquierda
            tobillo = tobillo_izquierdo
            hombro = hombro_izquierdo
            talon = talon_izquierdo
            punta_pie = punta_pie_izquierda
            otra_cadera = cadera_derecha

        angulo_rodilla = calcular_angulo(cadera, rodilla, tobillo)
        angulo_tronco = calcular_angulo(hombro, cadera, rodilla)
        angulo_cadera = calcular_angulo(rodilla, cadera, otra_cadera)

        altura_talon = talon[1]
        altura_punta_pie = punta_pie[1]

        errores = []

        if angulo_cadera < 150:
            errores.append("Cuidado con la retroversion pelvica.")
        if angulo_rodilla > 120:
            errores.append("Debes bajar mas para completar la sentadilla.")
        if angulo_tronco < 60:
            errores.append("Mantén el torso mas erguido.")
        if altura_talon < altura_punta_pie - 20:
            errores.append("No levantes los talones del suelo.")

        if errores:
            self.feedback = "\n".join(errores)
            for mensaje in errores:
                self.reproducir_audio(mensaje)
        else:
            self.feedback = "Buena tecnica!"
            self.reproducir_audio(self.feedback)

        progreso = 100 - min(100, max(0, angulo_rodilla - 90))
        return self.feedback, progreso
