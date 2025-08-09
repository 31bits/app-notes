import customtkinter as ctk
from PIL import Image, ImageTk
import os
import tkinter as tk
from utils.session import guardar_estado_sesion
import sys

def ruta_recurso(rel_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.join(os.path.abspath("."), rel_path)

def ventana_codigo_verificacion(ventana, db, btn1, btn2, btn3, actualizar_uso_key, set_nombre_usuario_callback):
   
    ventana_pin = ctk.CTkToplevel()
    ventana_pin.title("Iniciar sesión con código")

    base_w = 380
    base_h = 320   
    ventana_pin.geometry(f"{base_w}x{base_h}")
    ventana_pin.resizable(False, False)
    ventana_pin.configure(fg_color="#ffffff")
    ventana_pin.transient(ventana)

    try:
        ventana.update_idletasks()
        main_x = ventana.winfo_x()
        main_y = ventana.winfo_y()
        main_w = ventana.winfo_width()
        nueva_x = main_x + main_w + 10
        nueva_y = main_y + 50
        screen_w = ventana.winfo_screenwidth()
        screen_h = ventana.winfo_screenheight()
        if nueva_x + base_w > screen_w:
            nueva_x = max(20, main_x + (main_w - base_w)//2)
        if nueva_y + base_h > screen_h:
            nueva_y = max(20, main_y + 20)
        ventana_pin.geometry(f"{base_w}x{base_h}+{nueva_x}+{nueva_y}")
    except Exception:
        ventana_pin.geometry(f"{base_w}x{base_h}")

    main_container = ctk.CTkFrame(ventana_pin, fg_color="transparent")
    main_container.pack(fill="both", expand=True)

    BOTTOM_HEIGHT = 50  # <-- reduce para acercar el botón al contenido
    bottom_frame = ctk.CTkFrame(main_container, fg_color="transparent", height=BOTTOM_HEIGHT)
    bottom_frame.pack(side="bottom", fill="x", pady=(6, 8))
    bottom_frame.pack_propagate(False)

    # Inner frame simple (sin canvas). No expand vertical para evitar huecos.
    inner_frame = ctk.CTkFrame(main_container, fg_color="transparent")
    inner_frame.pack(side="top", fill="x", expand=False, padx=12, pady=(10, 6))

    # ------------------ ICONOS ------------------
    closed_icon = None
    open_icon = None
    try:
        closed_icon_path = ruta_recurso(os.path.join("images", "closed_key.png"))
        open_icon_path = ruta_recurso(os.path.join("images", "open_key.png"))
        closed_icon_img = Image.open(closed_icon_path).resize((60, 68))
        open_icon_img = Image.open(open_icon_path).resize((60, 68))
        closed_icon = ImageTk.PhotoImage(closed_icon_img)
        open_icon = ImageTk.PhotoImage(open_icon_img)
    except Exception:
        closed_icon = None
        open_icon = None

    # ------------------ CONTENIDO ------------------
    if closed_icon:
        icon_label = ctk.CTkLabel(inner_frame, image=closed_icon, text="")
        icon_label.image = closed_icon
    else:
        icon_label = ctk.CTkLabel(inner_frame, text="🔐", font=("Helvetica", 24))
    icon_label.pack(pady=(4, 2))

    titulo = ctk.CTkLabel(inner_frame, text="Código de verificación",
                          text_color="#000000", font=("Helvetica", 16, "bold"))
    titulo.pack(pady=(0, 2))

    subtitulo = ctk.CTkLabel(inner_frame, text="Ingresa tu código de 8 dígitos para iniciar sesión",
                             text_color="#555555", font=("Helvetica", 10))
    subtitulo.pack(pady=(0, 6))

    entry_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
    entry_frame.pack(pady=(2, 4))

    entries = []

    def on_key(event, index):
        char = event.char
        key = event.keysym

        if key == "BackSpace":
            if entries[index].get():
                entries[index].delete(0, 'end')
            else:
                if index > 0:
                    entries[index - 1].delete(0, 'end')
                    entries[index - 1].focus()
            return "break"

        if not char or len(char) != 1 or (not char.isalnum()):
            return "break"

        entries[index].delete(0, 'end')
        entries[index].insert(0, char)

        if index < 7:
            entries[index + 1].focus()
        return "break"

    for i in range(8):
        e = ctk.CTkEntry(entry_frame, width=34, height=36, font=("Helvetica", 14), justify="center")
        e.grid(row=0, column=i, padx=3)
        e.bind("<Key>", lambda event, index=i: on_key(event, index))
        entries.append(e)

    resultado_label = ctk.CTkLabel(inner_frame, text="", font=("Helvetica", 11))
    resultado_label.pack(pady=(4, 2))

    spacer = tk.Frame(inner_frame, height=2, bg="#ffffff")
    spacer.pack(fill="x")

    # ------------------ LÓGICA DE VERIFICACIÓN ------------------
    def verificar_codigo():
        codigo = ''.join(entry.get() for entry in entries).strip()
        if len(codigo) != 8:
            resultado_label.configure(text="Debe ingresar los 8 dígitos", text_color="red")
            return

        if db is None:
            resultado_label.configure(text="Error: base de datos no configurada", text_color="red")
            return

        try:
            doc_ref = db.collection("keys").document(codigo)
            doc = doc_ref.get()

            if not doc.exists:
                resultado_label.configure(text="❌ Código no válido", text_color="red")
                return

            data = doc.to_dict()
            activated = data.get("activated", False)
            uses = data.get("uses", 0)

            if uses <= 0:
                resultado_label.configure(text="❌ Código sin usos disponibles", text_color="red")
                return

            if not activated:
                doc_ref.update({"activated": True})

            resultado_label.configure(text="✅ Sesión iniciada correctamente", text_color="green")
            if open_icon:
                icon_label.configure(image=open_icon)
                icon_label.image = open_icon

            try:
                if btn1: btn1.configure(state="normal")
                if btn2: btn2.configure(state="normal")
                if btn3: btn3.configure(state="normal")
            except Exception:
                pass

            name = data.get("name", "Usuario")
            gmail = data.get("gmail", "")

            try:
                nombre_label = ctk.CTkLabel(ventana, text=f"👋 Bienvenido, {name}", text_color="#000000", font=("Helvetica", 14, "bold"))
                nombre_label.pack(pady=6)
            except Exception:
                pass

            guardar_estado_sesion(codigo, name, gmail)

            try:
                if callable(set_nombre_usuario_callback):
                    set_nombre_usuario_callback(name, gmail)
            except Exception:
                pass

            try:
                if callable(actualizar_uso_key):
                    actualizar_uso_key()
            except Exception:
                pass

            try:
                if hasattr(ventana, "set_nombre_usuario"):
                    ventana.set_nombre_usuario(name, gmail)
            except Exception:
                pass

        except Exception as e:
            resultado_label.configure(text=f"Error: {e}", text_color="red")

    # ------------------ BOTÓN ------------------
    btn_verificar = ctk.CTkButton(
        bottom_frame,
        text="INICIAR SESIÓN",
        font=("Helvetica", 14, "bold"),
        fg_color="#cc0605",
        hover_color="#a00404",
        text_color="#ffffff",
        width=170,
        height=40,
        command=verificar_codigo
    )
    btn_verificar.pack(pady=6)

    ventana_pin.update_idletasks()
    return ventana_pin
