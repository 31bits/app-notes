import customtkinter as ctk
from PIL import Image, ImageTk
import sys
import os
from tkinter import messagebox

from firebase_config import initialize_firebase
from utils.internet import hay_internet
from utils.excel_utils import seleccionar_excel, cargar_datos_excel
from utils.chrome_utils import abrir_chrome, conectar_driver
from ui.verificacion_key import ventana_codigo_verificacion
from ui.ventana_soporte import ventana_soporte
from utils.session import cargar_estado_sesion

import time
from selenium.webdriver.common.by import By

# ---- Estado de habilitación ----
USES_OK = False
INTERNET_OK = False
key_uses_label = None

def _hacer_modal(m, parent):
    m.transient(parent)              # apilado sobre el padre
    m.lift()                         # traer al frente
    m.attributes('-topmost', True)   # asegurar top mientras aparece
    m.grab_set()                     # bloquea interacción con la app
    m.focus_set()
    m.protocol("WM_DELETE_WINDOW", m.destroy)  # cierre seguro
    m.wait_visibility()              # esperar a que se muestre
    parent.wait_window(m)            # bloquear hasta cerrar

def mostrar_modal_sin_usos():
    m = ctk.CTkToplevel(ventana)
    m.title("Sin usos disponibles")
    m.geometry("380x200")
    m.resizable(False, False)
    m.transient(ventana)
    m.grab_set()

    ctk.CTkLabel(
        m,
        text="Tu key ya no tiene usos disponibles.\nPídele más al administrador.",
        font=("Helvetica", 14),
        justify="center",
        wraplength=320
    ).pack(padx=20, pady=(20, 10))

    btns = ctk.CTkFrame(m, fg_color="transparent")
    btns.pack(pady=10)

    ctk.CTkButton(
        btns, text="Contactar soporte",
        command=lambda: (m.destroy(), ventana_soporte(ventana, nombre_usuario_global, gmail_usuario_global))
    ).pack(side="left", padx=6)

    ctk.CTkButton(btns, text="Cerrar", command=m.destroy).pack(side="left", padx=6)

    m.wait_visibility()
    m.focus_force()
    ventana.wait_window(m)
    _hacer_modal(m, ventana)


def mostrar_modal_sin_internet():
    m = ctk.CTkToplevel(ventana)
    m.title("Sin conexión")
    m.geometry("360x170")
    m.resizable(False, False)
    m.transient(ventana)
    m.grab_set()

    ctk.CTkLabel(
        m,
        text="Necesitas conexión a internet para continuar.",
        font=("Helvetica", 14),
        justify="center",
        wraplength=300
    ).pack(padx=20, pady=(20, 10))

    ctk.CTkButton(m, text="Entendido", command=m.destroy).pack(pady=10)

    m.wait_visibility()
    m.focus_force()
    ventana.wait_window(m)
    _hacer_modal(m, ventana)

def _apply_btn3_state():
    btn = globals().get('btn3')
    if not btn:
        return

    # Mantener apariencia
    btn.configure(fg_color="#434343", hover_color="#232323", state="normal")

    if USES_OK and INTERNET_OK:
        btn.configure(command=accion_llenar_formulario)
    elif not USES_OK:
        btn.configure(command=mostrar_modal_sin_usos)
    else:
        btn.configure(command=mostrar_modal_sin_internet)


def _set_key_label(texto):
    lbl = globals().get('key_uses_label')
    if lbl:
        lbl.configure(text=texto)

def ruta_recurso(rel_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.join(os.path.abspath("."), rel_path)

def ya_existe_key_activada():
    try:
        datos_sesion = cargar_estado_sesion()
        if not datos_sesion or "key" not in datos_sesion:
            return False
        doc = db.collection("keys").document(datos_sesion["key"]).get()
        if not doc.exists:
            return False
        data = doc.to_dict() or {}
        return bool(data.get("activated", False))
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
    if not INTERNET_OK:
        mostrar_modal_sin_internet()

        return
    if not USES_OK:
        mostrar_modal_sin_usos()
        return

    actualizar_uso_key()
    if not USES_OK:
        messagebox.showwarning("Sin usos", "Tu key no tiene usos disponibles.")
        return
    
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

        # Verificar si el botón fue desactivado (porque se quedó sin usos)
        if btn3.cget("state") == "disabled":
            messagebox.showinfo("Límite alcanzado", "Se ingresaron los datos, pero ya no tienes más usos disponibles.")
        else:
            messagebox.showinfo("Éxito", "Todos los datos fueron ingresados.")

        progressbar.set(1.0)

    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error:\n{e}")

def verificar_conexion_periodica():
    global INTERNET_OK
    conectado = hay_internet()

    icono_path = ruta_recurso(os.path.join("images", "con-internet.png" if conectado else "sin-internet.png"))
    nueva_img = ctk.CTkImage(light_image=Image.open(icono_path).resize((25, 25), resample=Image.LANCZOS))
    internet_label.configure(image=nueva_img)
    internet_label.image = nueva_img

    INTERNET_OK = conectado
    _apply_btn3_state()

    ventana.after(5000, verificar_conexion_periodica)


def actualizar_uso_key():
    global USES_OK
    try:
        datos_sesion = cargar_estado_sesion()
        if not datos_sesion or "key" not in datos_sesion:
            _set_key_label("🔑")
            USES_OK = False
            _apply_btn3_state()
            return

        key_code = datos_sesion["key"]
        doc = db.collection("keys").document(key_code).get()
        if not doc.exists:
            _set_key_label("🔑")
            USES_OK = False
            _apply_btn3_state()
            return

        data = doc.to_dict() or {}
        usos_restantes = int(data.get("uses", 0))
        _set_key_label(f"🔑: {usos_restantes}")

        USES_OK = bool(data.get("activated", False)) and usos_restantes > 0
        _apply_btn3_state()

    except Exception as e:
        print("Error al obtener usos:", e)
        _set_key_label("🔑")
        USES_OK = False
        _apply_btn3_state()


def descontar_uso_key_activada():
    global USES_OK
    try:
        datos_sesion = cargar_estado_sesion()
        print("🔑 Sesión cargada:", datos_sesion)
        if not datos_sesion or "key" not in datos_sesion:
            print("⚠️ No se encontró código de sesión.")
            return

        key_code = datos_sesion["key"]
        doc_ref = db.collection("keys").document(key_code)
        doc = doc_ref.get()
        if not doc.exists:
            print("⚠️ La key no existe en Firebase.")
            return

        data = doc.to_dict() or {}
        usos_restantes = int(data.get("uses", 0))
        print("📄 Datos de la key usada:", data)

        if usos_restantes > 0:
            nuevos_usos = usos_restantes - 1
            doc_ref.update({"uses": nuevos_usos})
            print(f"✅ Se descontó un uso. Restantes: {nuevos_usos}")
            _set_key_label(f"🔑: {nuevos_usos}")

            USES_OK = bool(data.get("activated", False)) and nuevos_usos > 0
            _apply_btn3_state()
        else:
            print("⚠️ La key ya no tiene usos disponibles.")
            _set_key_label("🔑: 0")
            USES_OK = False
            _apply_btn3_state()

    except Exception as e:
        print("Error al descontar uso:", e)
        _set_key_label("🔑: --")
        USES_OK = False
        _apply_btn3_state()


# Interfaz principal
ventana = ctk.CTk()
ventana.title("Formulario Automático Universidad")
ventana.geometry("480x360")
ventana.resizable(False, False)
ventana.configure(fg_color="#cc0605")

# Header
header_frame = ctk.CTkFrame(ventana, fg_color="#1d1d1b", height=100, corner_radius=0)
header_frame.pack(fill="x", side="top")

logo_path = ruta_recurso("images/edubo.png")
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

# Desbloquear botones si hay key activada en la base
if ya_existe_key_activada():
    btn1.configure(state="normal")
    btn2.configure(state="normal")
else:
    btn1.configure(state="disabled")
    btn2.configure(state="disabled")

# Estado inicial de Internet + usos
INTERNET_OK = hay_internet()
_apply_btn3_state()

# Barra inferior
action_frame = ctk.CTkFrame(ventana, fg_color="#cc0605")
action_frame.pack(fill="x", side="bottom", pady=(2, 5))
progressbar = ctk.CTkProgressBar(action_frame, orientation="horizontal", width=350, progress_color="#ffffff")
progressbar.pack(pady=5)
progressbar.set(0)

# Botón de verificación
key_icon_path = ruta_recurso(os.path.join("images", "key_icon.png"))
key_img = Image.open(key_icon_path).resize((25, 25), resample=Image.LANCZOS)
key_photo = ImageTk.PhotoImage(key_img)

key_button = ctk.CTkButton(header_frame, image=key_photo, text="", width=25, height=25,
                           fg_color="transparent", hover_color="#333333",
                           command=lambda: ventana_codigo_verificacion(ventana, db, btn1, btn2, btn3, actualizar_uso_key, set_nombre_usuario))
key_button.image = key_photo
key_button.place(relx=1.0, x=-20, y=10, anchor="ne")



# Etiqueta para mostrar usos restantes
key_uses_label = ctk.CTkLabel(header_frame, text="🔑", text_color="#ffffff", font=("Helvetica", 12))
key_uses_label.place(relx=1.0, x=-130, y=7, anchor="ne")
actualizar_uso_key()


# Ícono adicional 
extra_icon_path = ruta_recurso(os.path.join("images", "Medium.png"))  # Asegúrate de tener este ícono en la carpeta images
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
internet_icon_path = ruta_recurso(os.path.join("images", "con-internet.png" if hay_internet() else "sin-internet.png"))
internet_icon_img = Image.open(internet_icon_path).resize((7, 10), resample=Image.LANCZOS)
internet_photo = ctk.CTkImage(light_image=internet_icon_img)

internet_label = ctk.CTkLabel(header_frame, image=internet_photo, text="")
internet_label.image = internet_photo
internet_label.place(relx=1.0, x=-60, y=7, anchor="ne")

verificar_conexion_periodica()
ventana.mainloop()
