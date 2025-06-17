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
            # sentadilla tradicional
            "pies_juntos": "Abre más los pies para mejorar estabilidad",
            "espalda_inclinada": "Endereza la espalda, mantén el pecho erguido",
            "tobillos_no_apoyados": "Apoya firmemente los talones en el suelo",
            "rodillas_hacia_adentro": "Empuja las rodillas hacia afuera",
            "rodillas_no_alineadas": "Alinea rodillas con la dirección de los pies",

            # sentadilla con salto
            "sin_salto": "Impúlsate hacia arriba, ¡salta con energía!",
            "salto_insuficiente": "Salta con más fuerza y controla la caída",

            # sentadilla sumo
            "rodillas_no_abiertas": "Abre más las piernas, te servirá para bajar más profundo",


            # step-ups 
            "rodilla_delantera_pasada": "Evita que la rodilla delantera sobrepase el pie",
            "equilibrio_inestable": "Activa el core y estabiliza el cuerpo",
            "pierna_trasera_sin_apoyo": "Usa ambas piernas, apoya bien la trasera",
            "angulo_rodilla_excesivo": "Evita doblar demasiado la rodilla, controla el movimiento",
            "pie_trasero_no_apoyado": "Mantén el pie trasero en contacto con el suelo",

            # estocada
            "pies_en_linea": "Separa más los pies para ganar equilibrio",
            "tronco_inclinado": "Mantén el torso erguido y la mirada al frente",
            "tobillo_trasero_despegado": "Apoya bien el pie trasero para mayor estabilidad",
            "paso_corto": "Da un paso más largo para mejorar la forma",
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
