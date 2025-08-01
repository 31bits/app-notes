import customtkinter as ctk
from PIL import Image
import os
import webbrowser
from urllib.parse import quote

def ventana_soporte(ventana, nombre_usuario, gmail_usuario):
    ventana_soporte = ctk.CTkToplevel()
    ventana_soporte.title("Soporte Técnico")
    ventana_soporte.geometry("300x300")  # ⬅️ tamaño fijo
    ventana_soporte.resizable(False, False)
    ventana_soporte.configure(fg_color="#ffffff")

    try:
        ventana.update_idletasks()
        main_x = ventana.winfo_x()
        main_y = ventana.winfo_y()
        main_w = ventana.winfo_width()
        nueva_x = main_x + main_w + 10
        nueva_y = main_y + 50
        ventana_soporte.geometry(f"+{nueva_x}+{nueva_y}")
    except Exception as e:
        print(f"No se pudo posicionar al costado: {e}")

    # Ícono de soporte
    icono_path = os.path.join("images", "Medium.png")
    soporte_img = Image.open(icono_path).resize((100, 100))
    soporte_photo = ctk.CTkImage(light_image=soporte_img, size=(100, 100))
    label_icono = ctk.CTkLabel(ventana_soporte, image=soporte_photo, text="")
    label_icono.image = soporte_photo
    label_icono.pack(pady=10)

    # Texto fijo
    label_contacto = ctk.CTkLabel(
        ventana_soporte,
        text="Contáctanos si necesitas más llaves\n+591 63851280",
        text_color="#000000",
        font=("Helvetica", 16, "bold"),
        wraplength=350,
        justify="center"
    )
    label_contacto.pack(pady=10)

    # Botón WhatsApp
    def abrir_whatsapp():
        numero = "59163851280"
        mensaje = f"Hola, soy {nombre_usuario} y mi email es {gmail_usuario}. Solicito una nueva llave de acceso."
        url = f"https://wa.me/{numero}?text={quote(mensaje)}"
        webbrowser.open(url)

    whatsapp_icon_path = os.path.join("images", "whatsapp.png")
    whatsapp_img = Image.open(whatsapp_icon_path).resize((40, 40))
    whatsapp_photo = ctk.CTkImage(light_image=whatsapp_img, size=(40, 40))

    boton_whatsapp = ctk.CTkButton(
        ventana_soporte,
        image=whatsapp_photo,
        text="",
        width=40,
        height=40,
        fg_color="transparent",
        hover_color="#d4f8df",
        command=abrir_whatsapp
    )
    boton_whatsapp.image = whatsapp_photo
    boton_whatsapp.pack(pady=5)
