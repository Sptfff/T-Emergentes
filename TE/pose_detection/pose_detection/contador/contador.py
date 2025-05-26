class ContadorRepeticiones:
    def __init__(self, umbral_bajo=90, umbral_alto=160):
        self.contador = 0
        self.direccion = 0  # 0: bajando, 1: subiendo
        self.umbral_bajo = umbral_bajo
        self.umbral_alto = umbral_alto

    def actualizar(self, angulo):
        """
        Actualiza el contador en función del ángulo de la rodilla.
        """
        if angulo < self.umbral_bajo and self.direccion == 0:
            self.direccion = 1  # Bajó completamente
        if angulo > self.umbral_alto and self.direccion == 1:
            self.direccion = 0  # Subió completamente
            self.contador += 1
        return self.contador
