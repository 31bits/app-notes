import json
import os

SESSION_FILE = "session.json"

# utils/session.py
def guardar_estado_sesion(codigo, name, gmail):
    with open(SESSION_FILE, "w") as f:
        json.dump({
            "key": codigo,
            "name": name,
            "gmail": gmail
        }, f)

def cargar_estado_sesion():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    return {}
