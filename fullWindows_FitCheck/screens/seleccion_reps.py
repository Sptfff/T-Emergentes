import tkinter as tk
from tkinter import ttk

class SeleccionRepsScreen(tk.Frame):
    def __init__(self, master, callback_entrenamiento):
        super().__init__(master)
        self.master = master
        self.callback_entrenamiento = callback_entrenamiento

        self.create_widgets()

    def create_widgets(self):
        titulo = tk.Label(self, text="Selecciona la cantidad de repeticiones", font=("Helvetica", 18))
        titulo.pack(pady=40)

        self.spinbox = tk.Spinbox(
            self,
            from_=1,
            to=30,
            width=5,
            font=("Helvetica", 16),
            justify="center"
        )
        self.spinbox.pack(pady=20)

        boton_continuar = ttk.Button(self, text="Iniciar Entrenamiento", command=self.continuar)
        boton_continuar.pack(pady=30)

    def continuar(self):
        reps_seleccionadas = int(self.spinbox.get())
        self.callback_entrenamiento(reps_seleccionadas)
