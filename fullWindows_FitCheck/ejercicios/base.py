class EjercicioBase:
    def __init__(self):
        self.repeticiones = 0
        self.estado_actual = None  # Por ejemplo, "bajando" o "subiendo"
        self.progreso = 0.0        # Para barra de progreso (0 a 1)

    def procesar_pose(self, landmarks):
        """
        Procesar landmarks recibidos y actualizar el estado del ejercicio,
        progreso y repeticiones.
        Este método debe ser implementado por cada ejercicio específico.
        """
        raise NotImplementedError("Debe implementar procesar_pose en la subclase")

    def get_repeticiones(self):
        return self.repeticiones

    def get_progreso(self):
        return self.progreso
