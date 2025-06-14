# fitcheck_app/screens/bienvenida.py
import tkinter as tk

class BienvenidaScreen(tk.Frame):
    def __init__(self, master, callback_entrenamiento):
        super().__init__(master, bg="black")
        self.callback_entrenamiento = callback_entrenamiento
        self.create_widgets()

    def create_widgets(self):
        # Título de bienvenida
        title = tk.Label(self, text="Bienvenido a FitCheck", font=("Helvetica", 24), fg="white", bg="black")
        title.pack(pady=40)

        # Botones de ejercicios
        ejercicios = ["Sentadillas", "Estocadas", "Step-Ups"]
        for ejercicio in ejercicios:
            boton = tk.Button(self, text=ejercicio, font=("Helvetica", 18),
                              width=20, command=lambda e=ejercicio: self.seleccionar_ejercicio(e))
            boton.pack(pady=10)

    def seleccionar_ejercicio(self, ejercicio):
        print(f"Ejercicio seleccionado: {ejercicio}")
        self.callback_entrenamiento(ejercicio)

