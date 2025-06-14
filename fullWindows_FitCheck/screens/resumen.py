import tkinter as tk

class PantallaResumen(tk.Frame):
    def __init__(self, root, volver_callback, repeticiones, errores):
        super().__init__(root, bg="black")  # hereda como Frame
        self.volver_callback = volver_callback
        self.repeticiones = repeticiones
        self.errores = errores

        self._crear_widgets()

    def _crear_widgets(self):
        label_titulo = tk.Label(
            self, text="Resumen de la Sesión",
            font=("Helvetica", 24), fg="white", bg="black"
        )
        label_titulo.pack(pady=40)

        label_reps = tk.Label(
            self,
            text=f"Repeticiones completadas: {self.repeticiones}",
            font=("Helvetica", 20), fg="white", bg="black"
        )
        label_reps.pack(pady=20)

        consejos = {
            "pies_en_linea":"Separa un poco los pies",
            "pies_juntos": "Separa un poco los pies",
            "rodilla_delantera_pasada": "Adelantas mucho la rodilla delantera, no dejes que sobrepase a tu pie delantero",
            "espalda_inclinada": "Mantén la espalda más recta",
            "tobillos_no_apoyados": "Apoya bien los tobillos",
            "tronco_inclinado":"Mantén la espalda más recta",
            "tobillo_trasero_despegado":"Apoya bien los tobillos",
            "rodillas_hacia_adentro":"Evita que las rodillas se muevan hacia adentro",
            "rodillas_no_alineadas":"Alinea tus rodillas con los pies",
            "equilibrio_inestable":"Mantén el equilibrio",
            "pierna_trasera_sin_apoyo":"Apoya completamente la pierna trasera",
            "angulo_rodilla_excesivo":"Evita un angulo demasiado agudo de rodilla",
            "pie_trasero_no_apoyado":"Apoya el pie trasero en el suelo",
        }

        # Filtramos y ordenamos los errores
        errores_filtrados = [
            (clave, valor) for clave, valor in self.errores.items() if valor > 0
        ]
        errores_filtrados.sort(key=lambda x: x[1], reverse=True)  # Ordenamos por cantidad de repeticiones (valor)

        if errores_filtrados:
            label_consejo = tk.Label(
                self, text="Consejos para la próxima vez:",
                font=("Helvetica", 18, "bold"), fg="orange", bg="black"
            )
            label_consejo.pack(pady=20)

            for clave, cantidad in errores_filtrados:
                texto = f"- {consejos[clave]} (cometido en {cantidad} reps.)"
                label_error = tk.Label(
                    self, text=texto,
                    font=("Helvetica", 16), fg="white", bg="black"
                )
                label_error.pack(anchor="w", padx=60)

        boton_salir = tk.Button(
            self,
            text="Volver a seleccionar ejercicio",
            font=("Helvetica", 16),
            command=self.volver
        )
        boton_salir.pack(pady=40)

    def volver(self):
        self.destroy()
        self.volver_callback()
