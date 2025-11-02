import tkinter as tk
from tkinter import messagebox
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
from utils.camera_manager import CameraManager
from utils.audio_manager import AudioManager
from utils.logger import get_logger
from config import (
    INACTIVIDAD_MAX,
    ADVERTENCIA_TIEMPO,
    FPS_LIMIT,
    MODEL_COMPLEXITY,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    AUDIO_HABILITADO
)

logger = get_logger()

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

        # Inicializar MediaPipe
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=MODEL_COMPLEXITY,
            enable_segmentation=False,
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE
        )
        
        # Inicializar cámara con detección automática
        logger.info(f"Inicializando entrenamiento: {ejercicio}")
        self.camera_manager = CameraManager()
        self.cap, camera_index, camera_backend = self.camera_manager.initialize_camera()
        
        if self.cap is None:
            logger.error("No se pudo inicializar la cámara")
            messagebox.showerror(
                "Error de Cámara",
                "No se pudo detectar ninguna cámara.\n\n"
                "Verifica que:\n"
                "• La cámara esté conectada\n"
                "• Ninguna otra aplicación la esté usando\n"
                "• Los drivers estén instalados"
            )
            self.master.after(100, self.master.destroy)
            return

        self.ultima_repeticion_time = time.time()  # Tiempo de la última repetición detectada
        self.inactividad_max = INACTIVIDAD_MAX  # segundos máximos sin repetir
        self.advertencia_tiempo = ADVERTENCIA_TIEMPO  # segundos para empezar a mostrar contador regresivo

        # Contador de inicio
        self.iniciando = False
        self.tiempo_inicio_contador = 0
        self.duracion_countdown = 3  # 3 segundos de cuenta regresiva

        # Inicializar gestor de audio
        self.audio_manager = AudioManager(habilitado=AUDIO_HABILITADO)
        
        # Asignar audio manager al ejercicio
        self.ejercicio_obj.set_audio_manager(self.audio_manager)
        
        logger.info(f"Sistema de audio {'habilitado' if AUDIO_HABILITADO else 'deshabilitado'}")

        self.create_widgets()

        self.thread_video = threading.Thread(target=self.video_loop, daemon=True)
        self.thread_video.start()

    def create_widgets(self):
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True)

        # Frame superior para mensajes (fuera del video)
        mensaje_frame = tk.Frame(main_frame, bg="#2c3e50", height=80)
        mensaje_frame.pack(fill="x", padx=10, pady=(10, 5))
        mensaje_frame.pack_propagate(False)
        
        self.mensaje_guia_label = tk.Label(
            mensaje_frame,
            text="",
            font=("Helvetica", 18, "bold"),
            fg="#ecf0f1",
            bg="#2c3e50",
            wraplength=800,
            justify="center"
        )
        self.mensaje_guia_label.pack(expand=True)

        # Frame central para video + barra de progreso
        center_frame = tk.Frame(main_frame)
        center_frame.pack(pady=10)
        
        # Video a la izquierda
        self.video_frame = tk.Label(center_frame)
        self.video_frame.grid(row=0, column=0, padx=10)
        
        # Barra de progreso a la derecha (Canvas)
        barra_frame = tk.Frame(center_frame, bg="#34495e")
        barra_frame.grid(row=0, column=1, padx=10, sticky="ns")
        
        tk.Label(barra_frame, text="Progreso", font=("Helvetica", 12, "bold"),
                bg="#34495e", fg="white").pack(pady=5)
        
        self.barra_canvas = tk.Canvas(barra_frame, width=80, height=400, 
                                      bg="#34495e", highlightthickness=0)
        self.barra_canvas.pack(pady=10)
        
        self.porcentaje_label = tk.Label(barra_frame, text="0%", 
                                         font=("Helvetica", 16, "bold"),
                                         bg="#34495e", fg="white")
        self.porcentaje_label.pack(pady=5)

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
        """Inicia el countdown de 3 segundos antes de empezar"""
        self.iniciando = True
        self.tiempo_inicio_contador = time.time()
        self.safe_update_estado("Preparate...", "orange")
        self.actualizar_botones()
        
        # Enviar audio de preparación
        if hasattr(self, 'audio_manager') and self.audio_manager:
            self.audio_manager.agregar_info("Preparate")

    def detener_entrenamiento(self):
        self.running = False
        self.actualizar_botones()
        # Limpiar contador inactividad al detener
        self.safe_update_inactividad_label("")

    def continuar_entrenamiento(self):
        self.running = True
        self.actualizar_botones()

    def finalizar_entrenamiento(self):
        """Finaliza el entrenamiento y libera recursos"""
        logger.info(f"Finalizando entrenamiento: {self.repeticiones} repeticiones")
        self.running = False
        
        try:
            self.camera_manager.release()
        except Exception as e:
            logger.error(f"Error al liberar cámara: {e}")
        
        if self.callback_resumen:
            self.callback_resumen(self.repeticiones, self.ejercicio_obj.errores_contador)

    def video_loop(self):
        """Loop principal de procesamiento de video con control de FPS"""
        fps_limit = FPS_LIMIT
        prev_time = 0

        while True:
            try:
                current_time = time.time()
                if current_time - prev_time < 1 / fps_limit:
                    time.sleep(0.01)
                    continue
                prev_time = current_time

                ret, frame = self.camera_manager.read()
                if not ret or frame is None:
                    logger.warning("No se pudo leer frame de la cámara")
                    time.sleep(0.1)
                    continue

                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.pose.process(rgb)

                if results.pose_landmarks:
                    if not self.persona_detectada:
                        self.persona_detectada = True
                        logger.info("Persona detectada en cámara")

                    mp.solutions.drawing_utils.draw_landmarks(
                        frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)

                    # Manejar countdown de inicio
                    if self.iniciando:
                        tiempo_transcurrido = time.time() - self.tiempo_inicio_contador
                        tiempo_restante = self.duracion_countdown - tiempo_transcurrido
                        
                        if tiempo_restante > 0:
                            # Mostrar countdown en pantalla
                            numero = int(tiempo_restante) + 1
                            cv2.putText(frame, str(numero), 
                                       (frame.shape[1]//2 - 50, frame.shape[0]//2), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 255, 0), 10)
                            self.safe_update_estado(f"Comenzando en {numero}...", "orange")
                        else:
                            # Countdown terminado, iniciar entrenamiento
                            self.iniciando = False
                            self.running = True
                            self.repeticiones = 0
                            self.ultima_repeticion_time = time.time()
                            self.safe_update_estado(f"Repeticiones: {self.repeticiones}/{self.repeticiones_objetivo}", "black")
                            logger.info("Entrenamiento iniciado después de countdown")
                            
                            # Audio de inicio
                            if hasattr(self, 'audio_manager') and self.audio_manager:
                                self.audio_manager.agregar_info("Comienza")
                    
                    elif self.running:
                        frame = self.detectar_ejercicio(results.pose_landmarks, frame)
                    else:
                        self.safe_update_estado("Persona detectada con éxito", "green")
                else:
                    if self.persona_detectada:
                        self.persona_detectada = False
                        logger.info("Persona ya no detectada")
                    
                    # Si estaba en countdown y se pierde la persona, cancelar
                    if self.iniciando:
                        self.iniciando = False
                        self.safe_update_estado("Countdown cancelado - Persona no detectada", "red")
                    
                    if not self.running and not self.iniciando:
                        self.safe_update_estado("Esperando persona detectada...", "red")

                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                imgtk = ImageTk.PhotoImage(image=img)
                self.safe_update_video(imgtk)

                self.master.after(0, self.actualizar_botones)
                
            except Exception as e:
                logger.error(f"Error en video_loop: {e}")
                time.sleep(0.1)

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
        
        # Actualizar UI externa (mensaje y barra)
        self.safe_update_mensaje_guia(self.mensaje_guia)
        self.safe_update_barra_progreso(self.ejercicio_obj.progreso)

        tiempo_desde_ultima = time.time() - self.ultima_repeticion_time
        tiempo_restante = self.inactividad_max - tiempo_desde_ultima

        if tiempo_restante <= self.advertencia_tiempo and tiempo_restante > 0:
            self.safe_update_inactividad_label(f"Inactividad: {int(tiempo_restante)}s")
        else:
            self.safe_update_inactividad_label("")

        if tiempo_desde_ultima >= self.inactividad_max:
            logger.warning(f"Tiempo de inactividad excedido: {tiempo_desde_ultima:.1f}s")
            self.running = False
            self.camera_manager.release()
            if self.callback_resumen:
                self.callback_resumen(self.repeticiones, self.ejercicio_obj.errores_contador)

        if self.repeticiones >= self.repeticiones_objetivo:
            logger.info(f"Objetivo alcanzado: {self.repeticiones}/{self.repeticiones_objetivo}")
            self.running = False
            self.camera_manager.release()
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
    
    def safe_update_mensaje_guia(self, texto):
        """Actualiza el mensaje guía en el label superior (fuera del video)"""
        def update():
            if texto:
                self.mensaje_guia_label.config(text=texto, fg="#e74c3c")  # Rojo para errores
            else:
                self.mensaje_guia_label.config(text="Realizando ejercicio...", fg="#ecf0f1")
        self.master.after(0, update)
    
    def safe_update_barra_progreso(self, progreso):
        """Actualiza la barra de progreso en el canvas lateral"""
        def update():
            self.barra_canvas.delete("all")
            
            # Dimensiones del canvas
            canvas_width = 80
            canvas_height = 400
            barra_width = 40
            barra_height = 360
            
            # Centrar barra
            x_offset = (canvas_width - barra_width) // 2
            y_offset = 20
            
            # Dibujar contorno
            self.barra_canvas.create_rectangle(
                x_offset, y_offset,
                x_offset + barra_width, y_offset + barra_height,
                outline="white", width=3
            )
            
            # Calcular altura del relleno
            altura_relleno = int(progreso * barra_height)
            
            if altura_relleno > 0:
                # Calcular color según progreso (rojo -> amarillo -> verde)
                if progreso < 0.5:
                    r = 255
                    g = int(255 * (progreso * 2))
                    b = 0
                else:
                    r = int(255 * (2 - progreso * 2))
                    g = 255
                    b = 0
                
                color_hex = f'#{r:02x}{g:02x}{b:02x}'
                
                # Dibujar relleno desde abajo hacia arriba
                y_inicio = y_offset + barra_height - altura_relleno
                self.barra_canvas.create_rectangle(
                    x_offset + 2, y_inicio,
                    x_offset + barra_width - 2, y_offset + barra_height - 2,
                    fill=color_hex, outline=""
                )
            
            # Actualizar porcentaje
            porcentaje = int(progreso * 100)
            self.porcentaje_label.config(text=f"{porcentaje}%")
        
        self.master.after(0, update)

    def safe_update_video(self, imgtk):
        def update():
            self.video_frame.imgtk = imgtk
            self.video_frame.configure(image=imgtk)
        self.master.after(0, update)

    def destroy(self):
        """Limpia recursos al destruir la pantalla"""
        logger.info("Destruyendo pantalla de entrenamiento")
        try:
            # Detener sistema de audio
            if hasattr(self, 'audio_manager') and self.audio_manager:
                logger.info("Deteniendo sistema de audio...")
                self.audio_manager.detener()
            
            # Liberar cámara
            self.camera_manager.release()
        except Exception as e:
            logger.error(f"Error al destruir: {e}")
        super().destroy()
