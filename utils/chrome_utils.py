import subprocess
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def abrir_chrome():
    ruta_chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(ruta_chrome):
        raise FileNotFoundError("Chrome no se encontró en la ruta especificada.")
    comando = f'"{ruta_chrome}" --remote-debugging-port=9222 --user-data-dir="C:\\chrome-temp"'
    subprocess.Popen(comando, shell=True)

def conectar_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
    return webdriver.Chrome(options=chrome_options)
