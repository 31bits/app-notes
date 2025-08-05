import customtkinter as ctk
from PIL import Image, ImageTk
import os
from utils.session import guardar_estado_sesion
import sys

def ruta_recurso(rel_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.join(os.path.abspath("."), rel_path)

def ventana_codigo_verificacion(ventana, db, btn1, btn2, btn3):
    ventana_pin = ctk.CTkToplevel()
    ventana_pin.title("Iniciar sesión con código")
    ventana_pin.geometry("380x300")
    ventana_pin.resizable(False, False)
    ventana_pin.configure(fg_color="#ffffff")

    try:
        ventana.update_idletasks()
        main_x = ventana.winfo_x()
        main_y = ventana.winfo_y()
        main_w = ventana.winfo_width()
        nueva_x = main_x + main_w + 10
        nueva_y = main_y + 50
        ventana_pin.geometry(f"+{nueva_x}+{nueva_y}")
    except Exception as e:
        print(f"No se pudo posicionar al costado: {e}")

    # Iconos
    closed_icon_path = ruta_recurso(os.path.join("images", "closed_key.png"))
    open_icon_path = ruta_recurso(os.path.join("images", "open_key.png"))

    closed_icon_img = Image.open(closed_icon_path).resize((70, 80))
    open_icon_img = Image.open(open_icon_path).resize((70, 80))

    closed_icon = ImageTk.PhotoImage(closed_icon_img)
    open_icon = ImageTk.PhotoImage(open_icon_img)

    icon_label = ctk.CTkLabel(ventana_pin, image=closed_icon, text="")
    icon_label.image = closed_icon
    icon_label.pack(pady=(20, 10))

    titulo = ctk.CTkLabel(ventana_pin, text="Código de verificación", text_color="#000000", font=("Helvetica", 20, "bold"))
    titulo.pack()

    subtitulo = ctk.CTkLabel(ventana_pin, text="Ingresa tu código de 8 dígitos para iniciar sesión", text_color="#555555", font=("Helvetica", 14))
    subtitulo.pack(pady=(0, 10))

    entry_frame = ctk.CTkFrame(ventana_pin, fg_color="transparent")
    entry_frame.pack(pady=10)

    entries = []

    def on_key(event, index):
        char = event.char
        key = event.keysym

        if key == "BackSpace":
            entries[index].delete(0, 'end')
            if index > 0 and entries[index].get() == '':
                entries[index - 1].focus()
            return

        if not char.isalnum() or len(char) != 1:
            return "break"

        entries[index].delete(0, 'end')
        entries[index].insert(0, char)

        if index < 7:
            entries[index + 1].focus()
        return "break"

    for i in range(8):
        e = ctk.CTkEntry(entry_frame, width=30, height=40, font=("Helvetica", 18), justify="center")
        e.grid(row=0, column=i, padx=3)
        e.bind("<Key>", lambda event, index=i: on_key(event, index))
        entries.append(e)

    resultado_label = ctk.CTkLabel(ventana_pin, text="", font=("Helvetica", 14))
    resultado_label.pack(pady=10)

    def verificar_codigo():
        codigo = ''.join(entry.get() for entry in entries).strip()
        if len(codigo) != 8:
            resultado_label.configure(text="Debe ingresar los 8 dígitos", text_color="red")
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

            # Activar solo si es la primera vez
            if not activated:
                doc_ref.update({"activated": True})

            # Inicio de sesión exitoso
            resultado_label.configure(text="✅ Sesión iniciada correctamente", text_color="green")
            icon_label.configure(image=open_icon)
            icon_label.image = open_icon

            btn1.configure(state="normal")
            btn2.configure(state="normal")
            btn3.configure(state="normal")

            name = data.get("name", "Usuario")
            gmail = data.get("gmail", "")

            # Mostrar nombre en ventana principal
            nombre_label = ctk.CTkLabel(
                ventana, 
                text=f"👋 Bienvenido, {name}", 
                text_color="#000000", 
                font=("Helvetica", 16, "bold")
            )
            nombre_label.pack(pady=10)

            guardar_estado_sesion(codigo, name, gmail)


            # Refrescar nombre en ventana principal si está definido
            if hasattr(ventana, "set_nombre_usuario"):
                ventana.set_nombre_usuario(name, gmail)


        except Exception as e:
            resultado_label.configure(text=f"Error: {e}", text_color="red")

    btn_verificar = ctk.CTkButton(
        ventana_pin,
        text="INICIAR SESIÓN",
        font=("Helvetica", 14, "bold"),
        fg_color="#cc0605",
        hover_color="#a00404",
        text_color="#ffffff",
        width=160,
        height=45,
        command=verificar_codigo
    )
    btn_verificar.pack(pady=5)
