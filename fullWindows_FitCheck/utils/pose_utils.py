import math

def calcular_angulo(p1, p2, p3):
    """
    Calcula el ángulo formado en p2 por los puntos p1 y p3.
    p1, p2, p3 son tuplas (x, y)
    """
    a = (p1[0] - p2[0], p1[1] - p2[1])
    b = (p3[0] - p2[0], p3[1] - p2[1])

    angulo_rad = math.acos(
        (a[0]*b[0] + a[1]*b[1]) / (math.sqrt(a[0]**2 + a[1]**2) * math.sqrt(b[0]**2 + b[1]**2) + 1e-6)
    )
    angulo_deg = math.degrees(angulo_rad)
    return angulo_deg
