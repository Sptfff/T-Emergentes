import math
from detector.pose_detector import calcular_angulo
from ejercicios.ejercicio_interfaz import Ejercicio_interfaz

class Sentadilla(Ejercicio_interfaz):
    def __init__(self):
        self.feedback = ""

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

        # Determinar hacia dónde mira el cuerpo
        # Si hombro izquierdo está más a la derecha, entonces mira hacia la izquierda (perfil derecho)
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

        # Calcular ángulos
        angulo_rodilla = calcular_angulo(cadera, rodilla, tobillo)
        angulo_tronco = calcular_angulo(hombro, cadera, rodilla)
        angulo_cadera = calcular_angulo(rodilla, cadera, otra_cadera)

        # Calcular alturas para verificar talones levantados
        altura_talon = talon[1]
        altura_punta_pie = punta_pie[1]

        errores = []

        if angulo_cadera < 100:
            errores.append("Cuidado con la retroversion pelvica.")

        if angulo_rodilla > 120:
            errores.append("Debes bajar mas para completar la sentadilla.")

        if angulo_tronco < 60:
            errores.append("Mantén el torso mas erguido.")

        if altura_talon < altura_punta_pie - 20:
            errores.append("No levantes los talones del suelo.")

        if errores:
            self.feedback = "\n".join(errores)
        else:
            self.feedback = "Buena tecnica!"

        progreso = 100 - min(100, max(0, angulo_rodilla - 90))
        return self.feedback, progreso

