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


class Flexion(Ejercicio_interfaz):
    def __init__(self):
        self.feedback = ""
        self.mensajes_audio = {
            "Cuerpo desalineado, manténlo recto.": "cuerpo_desalineado.mp3",
            "Baja más para completar la flexión.": "bajar_mas_flexion.mp3",
            "Evita que los codos se abran demasiado.": "codos_abiertos.mp3",
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
        codo_izquierdo = puntos_clave[13]
        codo_derecho = puntos_clave[14]
        muneca_izquierda = puntos_clave[15]
        muneca_derecha = puntos_clave[16]
        cadera_izquierda = puntos_clave[23]
        cadera_derecha = puntos_clave[24]

        mirando_izquierda = hombro_izquierdo[0] > hombro_derecho[0]

        if mirando_izquierda:
            hombro = hombro_derecho
            codo = codo_derecho
            muneca = muneca_derecha
            cadera = cadera_derecha
        else:
            hombro = hombro_izquierdo
            codo = codo_izquierdo
            muneca = muneca_izquierda
            cadera = cadera_izquierda

        angulo_brazo = calcular_angulo(hombro, codo, muneca)
        angulo_cuerpo = calcular_angulo(hombro, cadera, muneca)

        errores = []

        if angulo_cuerpo < 160:
            errores.append("Cuerpo desalineado, manténlo recto.")
        if angulo_brazo > 120:
            errores.append("Baja más para completar la flexión.")
        if abs(hombro[1] - codo[1]) > 40:
            errores.append("Evita que los codos se abran demasiado.")

        if errores:
            self.feedback = "\n".join(errores)
            for mensaje in errores:
                self.reproducir_audio(mensaje)
        else:
            self.feedback = "Buena tecnica!"
            self.reproducir_audio(self.feedback)

        progreso = 100 - min(100, max(0, angulo_brazo - 90))
        return self.feedback, progreso
