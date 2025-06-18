import tkinter as tk
import threading
import cv2
from PIL import Image, ImageTk
import mediapipe as mp
import time

from ejercicios.sumo import SentadillaSumo
from ejercicios.sentadilla import Sentadilla
from ejercicios.estocada import Estocada
from ejercicios.step_up import StepUp
from ejercicios.consalto import SentadillaConSalto

class EntrenamientoScreen(tk.Frame):
    def __init__(self, master, ejercicio, callback_resumen=None, repeticiones_objetivo=10):
        super().__init__(master)
        self.master = master
        self.ejercicio = ejercicio
        self.repeticiones_objetivo = repeticiones_objetivo
        self.repeticiones = 0
        self.progress = 0
        self.running = False
        self.persona_detectada = False
        self.callback_resumen = callback_resumen
        self.mensaje_guia = ""

        if self.ejercicio == "Sentadilla tradicional":
            self.ejercicio_obj = Sentadilla()
        elif self.ejercicio == "Estocadas":
            self.ejercicio_obj = Estocada()
        elif self.ejercicio == "Step-Ups":
            self.ejercicio_obj = StepUp()
        elif self.ejercicio == "Sentadilla con salto":
            self.ejercicio_obj = SentadillaConSalto()
        elif self.ejercicio == "Sentadilla sumo":
            self.ejercicio_obj = SentadillaSumo()
        else:
            raise ValueError(f"Ejercicio desconocido: {self.ejercicio}")

        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        #self.cap = cv2.VideoCapture(0)
        self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.ultima_repeticion_time = time.time()  # Tiempo de la última repetición detectada
        self.inactividad_max = 15  # segundos máximos sin repetir
        self.advertencia_tiempo = 5  # segundos para empezar a mostrar contador regresivo

        self.create_widgets()

        self.thread_video = threading.Thread(target=self.video_loop, daemon=True)
        self.thread_video.start()

    def create_widgets(self):
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True)

        top_frame = tk.Frame(main_frame)
        top_frame.pack(pady=10)
        center_top = tk.Frame(top_frame)
        center_top.pack()
        self.video_frame = tk.Label(center_top)
        self.video_frame.grid(row=0, column=0, padx=10)

        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(pady=20)

        self.estado_label = tk.Label(
            bottom_frame,
            text="Esperando persona detectada...",
            fg="red",
            font=("Helvetica", 16)
        )
        self.estado_label.pack(pady=5)

        # Frame para botones y contador de inactividad
        self.botones_frame = tk.Frame(bottom_frame)
        self.botones_frame.pack()

        self.boton_empezar = tk.Button(
            self.botones_frame, text="Empezar", bg="blue", fg="white",
            font=("Helvetica", 14), command=self.iniciar_entrenamiento
        )
        self.boton_detener = tk.Button(
            self.botones_frame, text="Detener", bg="gold",
            font=("Helvetica", 14), command=self.detener_entrenamiento
        )
        self.boton_continuar = tk.Button(
            self.botones_frame, text="Continuar", bg="blue", fg="white",
            font=("Helvetica", 14), command=self.continuar_entrenamiento
        )
        self.boton_finalizar = tk.Button(
            self.botones_frame, text="Finalizar", bg="red", fg="white",
            font=("Helvetica", 14), command=self.finalizar_entrenamiento
        )

        # Label para mostrar el contador de inactividad a la derecha de los botones
        self.inactividad_label = tk.Label(
            self.botones_frame,
            text="",
            fg="red",
            font=("Helvetica", 16, "bold")
        )
        self.actualizar_botones()

    def actualizar_botones(self):
        # Limpiar botones
        for widget in self.botones_frame.winfo_children():
            widget.pack_forget()

        self.estado_label.pack(pady=5)

        if not self.persona_detectada:
            self.boton_empezar.config(state="disabled")
            self.boton_empezar.pack(pady=10)
            # También limpiar contador inactividad cuando no hay persona
            self.inactividad_label.config(text="")
            return

        self.boton_empezar.config(state="normal")

        if self.running:
            self.boton_detener.pack(side="left", padx=10)
            self.boton_finalizar.pack(side="left", padx=10)
        elif self.repeticiones > 0:
            self.boton_continuar.pack(side="left", padx=10)
            self.boton_finalizar.pack(side="left", padx=10)
        else:
            self.boton_empezar.pack(pady=10)

        # Mostrar label inactividad siempre a la derecha de los botones
        self.inactividad_label.pack(side="left", padx=20)

    def iniciar_entrenamiento(self):
        self.running = True
        self.repeticiones = 0
        self.ultima_repeticion_time = time.time()
        self.safe_update_estado(f"Repeticiones: {self.repeticiones}/{self.repeticiones_objetivo}", "black")
        self.actualizar_botones()

    def detener_entrenamiento(self):
        self.running = False
        self.actualizar_botones()
        # Limpiar contador inactividad al detener
        self.safe_update_inactividad_label("")

    def continuar_entrenamiento(self):
        self.running = True
        self.actualizar_botones()

    def finalizar_entrenamiento(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()
        if self.callback_resumen:
            self.callback_resumen(self.repeticiones, self.ejercicio_obj.errores_contador)

    def video_loop(self):
        fps_limit = 15
        prev_time = 0

        while True:
            current_time = time.time()
            if current_time - prev_time < 1 / fps_limit:
                time.sleep(0.01)
                continue
            prev_time = current_time

            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb)

            if results.pose_landmarks:
                if not self.persona_detectada:
                    self.persona_detectada = True

                mp.solutions.drawing_utils.draw_landmarks(
                    frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)

                if self.running:
                    frame = self.detectar_ejercicio(results.pose_landmarks, frame)
                else:
                    self.safe_update_estado("Persona detectada con éxito", "green")
            else:
                if self.persona_detectada:
                    self.persona_detectada = False
                if not self.running:
                    self.safe_update_estado("Esperando persona detectada...", "red")

            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)
            self.safe_update_video(imgtk)

            self.master.after(0, self.actualizar_botones)

    def detectar_ejercicio(self, pose_landmarks, frame):
        landmarks = {self.mp_pose.PoseLandmark(i).name: lm for i, lm in enumerate(pose_landmarks.landmark)}

        self.ejercicio_obj.procesar_pose(landmarks)
        frame = self.ejercicio_obj.dibujar_feedback(frame, landmarks)

        repeticiones_antes = self.repeticiones
        self.repeticiones = self.ejercicio_obj.repeticiones
        self.progress = self.ejercicio_obj.progreso * 100
        self.mensaje_guia = self.ejercicio_obj.mensaje_guia

        if self.repeticiones > repeticiones_antes:
            self.ultima_repeticion_time = time.time()

        self.safe_update_estado(f"Repeticiones: {self.repeticiones}/{self.repeticiones_objetivo}", "black")

        tiempo_desde_ultima = time.time() - self.ultima_repeticion_time
        tiempo_restante = self.inactividad_max - tiempo_desde_ultima

        if tiempo_restante <= self.advertencia_tiempo and tiempo_restante > 0:
            self.safe_update_inactividad_label(f"Inactividad: {int(tiempo_restante)}s")
        else:
            self.safe_update_inactividad_label("")

        if tiempo_desde_ultima >= self.inactividad_max:
            self.running = False
            if self.cap.isOpened():
                self.cap.release()
            if self.callback_resumen:
                self.callback_resumen(self.repeticiones, self.ejercicio_obj.errores_contador)

        if self.repeticiones >= self.repeticiones_objetivo:
            self.running = False
            if self.cap.isOpened():
                self.cap.release()
            if self.callback_resumen:
                self.callback_resumen(self.repeticiones, self.ejercicio_obj.errores_contador)

        return frame

    def safe_update_estado(self, texto, color):
        def update():
            self.estado_label.config(text=texto, fg=color)
        self.master.after(0, update)

    def safe_update_inactividad_label(self, texto):
        def update():
            self.inactividad_label.config(text=texto)
        self.master.after(0, update)

    def safe_update_video(self, imgtk):
        def update():
            self.video_frame.imgtk = imgtk
            self.video_frame.configure(image=imgtk)
        self.master.after(0, update)

    def destroy(self):
        if self.cap.isOpened():
            self.cap.release()
        super().destroy()
