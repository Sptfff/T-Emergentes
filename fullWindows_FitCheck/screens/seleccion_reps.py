import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageSequence
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # ruta de seleccion_reps.py
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))  # sube a donde está main.py

class SeleccionRepsScreen(tk.Frame):
    def __init__(self, master, callback_entrenamiento, callback_volver, nombre_ejercicio):
        super().__init__(master)
        self.master = master
        self.callback_entrenamiento = callback_entrenamiento
        self.callback_volver = callback_volver
        self.nombre_ejercicio = nombre_ejercicio

        self.gif_frames = []
        self.current_frame = 0

        self.create_widgets()
        self.load_gif()
        self.animate_gif()

    def create_widgets(self):
        label_ejercicio = tk.Label(
            self,
            text=f"Ejercicio seleccionado: {self.nombre_ejercicio}",
            font=("Helvetica", 16, "bold")
        )
        label_ejercicio.pack(pady=(30, 10))

        self.gif_label = tk.Label(self)
        self.gif_label.pack(pady=10)

        self.label_error = tk.Label(self, text="", font=("Helvetica", 12), fg="red")
        self.label_error.pack()

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


    def get_gif_path(self):
        nombre_normalizado = (
            self.nombre_ejercicio.strip()
            .lower()
            .replace("-", " ")
            .replace("ups", "up")
        )

        ejercicio_a_gif = {
            "sentadilla tradicional": "sentadillas_tradicional.gif",
            "sentadilla con salto": "sentadillas_consalto.gif",
            "sentadilla sumo": "sentadillas_sumo.gif",
            "step up": "stepups.gif",
            "estocadas": "estocada.gif"
        }

        filename = ejercicio_a_gif.get(nombre_normalizado)
        if filename:
            path = os.path.join(PROJECT_ROOT, "videos", filename)
            print(f"Buscando GIF en: {path}")
            return path
        return None


    def load_gif(self):
        gif_path = self.get_gif_path()
        if not gif_path or not os.path.exists(gif_path):
            self.label_error.config(text="video no disponible para este ejercicio.")
            return

        try:
            gif = Image.open(gif_path)
            self.gif_frames = [
                ImageTk.PhotoImage(frame.copy().resize((300, 300)))
                for frame in ImageSequence.Iterator(gif)
            ]
            self.label_error.config(text="")  # Limpiar error si se carga correctamente
        except Exception as e:
            print(f"Error cargando el GIF: {e}")
            self.label_error.config(text="Error al cargar el video.")

    def animate_gif(self):
        if self.gif_frames:
            frame = self.gif_frames[self.current_frame]
            self.gif_label.configure(image=frame)
            self.gif_label.image = frame
            self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
            self.after(100, self.animate_gif)

    def continuar(self):
        self.callback_entrenamiento(int(self.spinbox.get()))

    def volver(self):
        self.callback_volver()
