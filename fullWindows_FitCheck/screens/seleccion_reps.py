import tkinter as tk
from tkinter import ttk

class SeleccionRepsScreen(tk.Frame):
    def __init__(self, master, callback_entrenamiento, callback_volver, nombre_ejercicio):
        super().__init__(master)
        self.master = master
        self.callback_entrenamiento = callback_entrenamiento
        self.callback_volver = callback_volver
        self.nombre_ejercicio = nombre_ejercicio

        self.create_widgets()

    def create_widgets(self):
        label_ejercicio = tk.Label(
            self,
            text=f"Ejercicio seleccionado: {self.nombre_ejercicio}",
            font=("Helvetica", 16, "bold")
        )
        label_ejercicio.pack(pady=(30, 10))

        titulo = tk.Label(self, text="Selecciona la cantidad de repeticiones", font=("Helvetica", 18))
        titulo.pack(pady=10)

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
        boton_continuar.pack(pady=20)

        boton_volver = ttk.Button(self, text="Volver", command=self.volver)
        boton_volver.pack(pady=10)

    def continuar(self):
        reps_seleccionadas = int(self.spinbox.get())
        self.callback_entrenamiento(reps_seleccionadas)

    def volver(self):
        self.callback_volver()
