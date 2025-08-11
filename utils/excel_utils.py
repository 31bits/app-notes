import os
from tkinter import filedialog
import pandas as pd

def seleccionar_excel():
    path = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx")])
    return path

def cargar_datos_excel(path):
    df = pd.read_excel(path)
    required_cols = {'NOMBRE', 'Faltas', 'Parcial'}
    if not required_cols.issubset(df.columns):
        raise ValueError("Columnas faltantes en el Excel")
    return df
