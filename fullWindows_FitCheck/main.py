import tkinter as tk
from screens.bienvenida import BienvenidaScreen
from screens.seleccion_reps import SeleccionRepsScreen  
from screens.entrenamiento import EntrenamientoScreen
from screens.resumen import PantallaResumen

class FitCheckApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FitCheck")
        self.root.geometry("800x600")
        self.pantalla_actual = None

        self.ejercicio_seleccionado = None
        self.repeticiones_objetivo = None

        self.mostrar_bienvenida()

    def mostrar_bienvenida(self):
        self._cambiar_pantalla(
            BienvenidaScreen(self.root, self.mostrar_seleccion_reps)
        )

    def mostrar_seleccion_reps(self, ejercicio):
        self.ejercicio_seleccionado = ejercicio
        self._cambiar_pantalla(
            SeleccionRepsScreen(
                self.root,
                self.iniciar_entrenamiento,
                self.mostrar_bienvenida,
                ejercicio
            )
        )

    def iniciar_entrenamiento(self, reps_seleccionadas):
        self.repeticiones_objetivo = reps_seleccionadas
        self._cambiar_pantalla(
            EntrenamientoScreen(
                self.root,
                self.ejercicio_seleccionado,
                self.mostrar_resumen,
                self.repeticiones_objetivo
            )
        )

    def mostrar_resumen(self, repeticiones, errores_contador):
        self._cambiar_pantalla(
            PantallaResumen(
                self.root,
                self.mostrar_bienvenida,
                repeticiones,
                errores_contador
            )
        )

    def _cambiar_pantalla(self, nueva_pantalla):
        if self.pantalla_actual:
            self.pantalla_actual.destroy()
        self.pantalla_actual = nueva_pantalla
        self.pantalla_actual.pack(fill="both", expand=True)

def main():
    root = tk.Tk()
    app = FitCheckApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
