import customtkinter as ctk
from PIL import Image, ImageTk
import os
from tkinter import messagebox
from urllib.parse import quote


from firebase_config import initialize_firebase
from utils.internet import hay_internet
from utils.excel_utils import seleccionar_excel, cargar_datos_excel
from utils.chrome_utils import abrir_chrome, conectar_driver
from ui.verificacion_key import ventana_codigo_verificacion
from ui.ventana_soporte import ventana_soporte
from utils.session import cargar_estado_sesion

import time
from selenium.webdriver.common.by import By

def ya_existe_key_activada():
    try:
        keys_ref = db.collection("keys")
        query = keys_ref.where("activated", "==", True).limit(1).stream()
        for _ in query:
            return True
        return False
    except Exception as e:
        print("Error al verificar key activada:", e)
        return False


# Inicializar Firebase
db = initialize_firebase()

# Variables globales
excel_path = None
nombre_usuario_global = "Usuario"
gmail_usuario_global = ""

# Funciones
def accion_abrir_chrome():
    try:
        abrir_chrome()
        ventana.after(2000, lambda: progressbar.set(0.33))
        progressbar.set(0.1)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def accion_seleccionar_excel():
    global excel_path
    path = seleccionar_excel()
    if path:
        excel_path = path
        label_excel.configure(text=os.path.basename(path), text_color="#ffffff")
        progressbar.set(0.66)

def accion_llenar_formulario():
    if not excel_path:
        messagebox.showwarning("Advertencia", "Primero selecciona un archivo Excel.")
        return

    try:
        df = cargar_datos_excel(excel_path)
        driver = conectar_driver()
        time.sleep(2)

        filas = driver.find_elements(By.CSS_SELECTOR,
            "#ContentPlaceHolder1_CUAcademicoDocente1_CUTranscripcionNotas1_GVEstudianteNotas tbody tr[valign='top']")
        total = len(filas)
        if total == 0:
            messagebox.showinfo("Información", "No se encontraron filas en la página web.")
            return

        for idx, fila in enumerate(filas):
            try:
                span_nombre = fila.find_element(By.CSS_SELECTOR, "span[id*='LBLNombreCompleto']")
                nombre_web = span_nombre.text.strip().upper()
            except:
                continue

            fila_excel = df[df['NOMBRE COMPLETO'].str.strip().str.upper() == nombre_web]
            if fila_excel.empty:
                print(f"❌ No hay datos en Excel para {nombre_web}")
                continue

            datos = fila_excel.iloc[0]
            faltas = datos['Faltas 1ºP']
            nota = datos['1º Parcial']

            def set_input(name_part, value):
                try:
                    campo = fila.find_element(By.CSS_SELECTOR, f"input[name*='{name_part}']")
                    if campo.get_attribute("disabled"):
                        return False
                    campo.clear()
                    campo.send_keys(str(value))
                    return True
                except:
                    return False

            set_input("TXTP1", nota)
            set_input("TXTF1", faltas)

            progressbar.set(0.66 + 0.34 * ((idx + 1) / total))
            
        descontar_uso_key_activada()
        messagebox.showinfo("Éxito", "Todos los datos fueron ingresados.")
        progressbar.set(1.0)
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error:\n{e}")

def verificar_conexion_periodica():
    conectado = hay_internet()

    icono_path = os.path.join("images", "con-internet.png" if conectado else "sin-internet.png")
    nueva_img = ctk.CTkImage(light_image=Image.open(icono_path).resize((25, 25), resample=Image.LANCZOS))
    internet_label.configure(image=nueva_img)
    internet_label.image = nueva_img

    if conectado:
        btn3.configure(state="normal", fg_color="#434343", hover_color="#232323")
    else:
        btn3.configure(state="disabled", fg_color="#999999", hover_color="#999999")

    ventana.after(5000, verificar_conexion_periodica)

def descontar_uso_key_activada():
    try:
        keys_ref = db.collection("keys").where("activated", "==", True).limit(1).stream()
        for key_doc in keys_ref:
            doc_ref = db.collection("keys").document(key_doc.id)
            data = key_doc.to_dict()
            usos_restantes = data.get("uses", 0)

            if usos_restantes > 0:
                doc_ref.update({"uses": usos_restantes - 1})
                print(f"✅ Se descontó un uso. Restantes: {usos_restantes - 1}")
            else:
                print("⚠️ La key ya no tiene usos disponibles.")
            break
    except Exception as e:
        print("Error al descontar uso:", e)


# Interfaz principal
ventana = ctk.CTk()
ventana.title("Formulario Automático Universidad")
ventana.geometry("480x360")
ventana.resizable(False, False)
ventana.configure(fg_color="#cc0605")

# Header
header_frame = ctk.CTkFrame(ventana, fg_color="#1d1d1b", height=100, corner_radius=0)
header_frame.pack(fill="x", side="top")

logo_path = os.path.join("edubo.png")
logo_img = Image.open(logo_path).resize((70, 20), resample=Image.LANCZOS)
logo = ImageTk.PhotoImage(logo_img)
logo_label = ctk.CTkLabel(header_frame, image=logo, text="")
logo_label.place(x=10, y=10)

ctk.CTkLabel(
    header_frame,
    text="Formulario Automático Universidad",
    text_color="#ffffff",
    font=("Helvetica", 20, "bold")
).place(relx=0.5, rely=0.6, anchor="center")

#Datos de usuario
def set_nombre_usuario(nombre, gmail=""):
    global nombre_usuario_global, gmail_usuario_global
    nombre_usuario_global = nombre
    gmail_usuario_global = gmail

    # Elimina saludos anteriores
    for widget in header_frame.winfo_children():
        if isinstance(widget, ctk.CTkLabel) and "Bienvenido" in widget.cget("text"):
            widget.destroy()

    saludo_label = ctk.CTkLabel(
        header_frame,
        text=f"👤 ¡Bienvenido {nombre}!",
        text_color="#ffffff",
        font=("Helvetica", 14)
    )
    saludo_label.place(x=90, y=12)


datos_sesion = cargar_estado_sesion()
if datos_sesion and "name" in datos_sesion:
    ventana.set_nombre_usuario = set_nombre_usuario  # Enlaza la función con la ventana
    set_nombre_usuario(datos_sesion["name"], datos_sesion.get("gmail", ""))

# Body
body_frame = ctk.CTkFrame(ventana, fg_color="#cc0605")
body_frame.pack(expand=True, fill="both", padx=20, pady=(20, 10))
body_frame.grid_columnconfigure(0, weight=1)

btn1 = ctk.CTkButton(body_frame, text="🌐 ABRIR CHROME", text_color="#cc0605", font=("Helvetica", 12),
                     corner_radius=12, fg_color="#ffffff", hover_color="#b7b7b7", width=220, height=40,
                     command=accion_abrir_chrome)
btn1.grid(row=0, column=0, pady=6)

btn2 = ctk.CTkButton(body_frame, text="📂 SELECCIONAR EXCEL", text_color="#cc0605", font=("Helvetica", 12),
                     corner_radius=12, fg_color="#ffffff", hover_color="#b7b7b7", width=220, height=40,
                     command=accion_seleccionar_excel)
btn2.grid(row=1, column=0, pady=6)

label_excel = ctk.CTkLabel(body_frame, text="Ningún archivo seleccionado", text_color="#ffffff", font=("Helvetica", 14))
label_excel.grid(row=2, column=0, pady=4)

btn3 = ctk.CTkButton(body_frame, text="🚀 LLENAR FORMULARIO", font=("Helvetica", 12), corner_radius=12,
                     fg_color="#434343", hover_color="#232323", width=220, height=40,
                     command=accion_llenar_formulario)
btn3.grid(row=3, column=0, pady=10)

btn1.configure(state="disabled")
btn2.configure(state="disabled")
btn3.configure(state="disabled")

# Desbloquear botones si hay key activada en la base
if ya_existe_key_activada():
    btn1.configure(state="normal")
    btn2.configure(state="normal")
    btn3.configure(state="normal")
else:
    btn1.configure(state="disabled")
    btn2.configure(state="disabled")
    btn3.configure(state="disabled")


# Barra inferior
action_frame = ctk.CTkFrame(ventana, fg_color="#cc0605")
action_frame.pack(fill="x", side="bottom", pady=(2, 5))
progressbar = ctk.CTkProgressBar(action_frame, orientation="horizontal", width=350, progress_color="#ffffff")
progressbar.pack(pady=5)
progressbar.set(0)

# Botón de verificación
key_icon_path = os.path.join("images", "key_icon.png")
key_img = Image.open(key_icon_path).resize((25, 25), resample=Image.LANCZOS)
key_photo = ImageTk.PhotoImage(key_img)

key_button = ctk.CTkButton(header_frame, image=key_photo, text="", width=25, height=25,
                           fg_color="transparent", hover_color="#333333",
                           command=lambda: ventana_codigo_verificacion(ventana, db, btn1, btn2, btn3))
key_button.image = key_photo
key_button.place(relx=1.0, x=-20, y=10, anchor="ne")

# Ícono adicional 
extra_icon_path = os.path.join("images", "Medium.png")  # Asegúrate de tener este ícono en la carpeta images
extra_icon_img = Image.open(extra_icon_path).resize((50, 30), resample=Image.LANCZOS)
extra_photo = ctk.CTkImage(light_image=extra_icon_img)

extra_button = ctk.CTkButton(
    header_frame,
    image=extra_photo,
    text="",
    width=25,
    height=25,
    fg_color="transparent",
    hover_color="#333333",
    command=lambda: ventana_soporte(ventana, nombre_usuario_global, gmail_usuario_global)
)

extra_button.image = extra_photo
extra_button.place(relx=1.0, x=-90, y=7, anchor="ne")

# Ícono conexión
internet_icon_path = os.path.join("images", "con-internet.png" if hay_internet() else "sin-internet.png")
internet_icon_img = Image.open(internet_icon_path).resize((7, 10), resample=Image.LANCZOS)
internet_photo = ctk.CTkImage(light_image=internet_icon_img)

internet_label = ctk.CTkLabel(header_frame, image=internet_photo, text="")
internet_label.image = internet_photo
internet_label.place(relx=1.0, x=-60, y=7, anchor="ne")

verificar_conexion_periodica()
ventana.mainloop()
