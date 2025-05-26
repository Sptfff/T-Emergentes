import cv2
import mediapipe as mp
import math

class DetectorPostura:  
    def __init__(self):
        self.pose = mp.solutions.pose.Pose()
        self.dibujo = mp.solutions.drawing_utils

    def encontrar_postura(self, imagen):
        img_rgb = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
        self.resultados = self.pose.process(img_rgb)
        if self.resultados.pose_landmarks:
            self.dibujo.draw_landmarks(
                imagen,
                self.resultados.pose_landmarks,
                mp.solutions.pose.POSE_CONNECTIONS
            )
        return imagen

    def obtener_puntos_clave(self, imagen):
        lista_puntos = []
        if self.resultados.pose_landmarks:
            for id, lm in enumerate(self.resultados.pose_landmarks.landmark):
                h, w, _ = imagen.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lista_puntos.append((id, cx, cy))
        return lista_puntos

def calcular_angulo(p1, p2, p3):
    """
    Calcula el ángulo entre tres puntos.
    """
    x1, y1 = p1[1], p1[2]
    x2, y2 = p2[1], p2[2]
    x3, y3 = p3[1], p3[2]

    angulo = math.degrees(math.atan2(y3 - y2, x3 - x2) -
                           math.atan2(y1 - y2, x1 - x2))
    if angulo < 0:
        angulo += 360
    return angulo
