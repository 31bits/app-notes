import firebase_admin
from firebase_admin import credentials, firestore
import sys
import os

def ruta_recurso(rel_path):
    """Compatible con PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.join(os.path.abspath("."), rel_path)

def initialize_firebase():
    if not firebase_admin._apps:
        cred_path = ruta_recurso("key.json")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()
