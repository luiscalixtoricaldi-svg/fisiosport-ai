import streamlit as st
import sqlite3
import hashlib
import numpy as np
import pandas as pd

# ==============================
# CONFIGURACIÓN
# ==============================
st.set_page_config(page_title="FisioSport AI", layout="wide")

# ==============================
# BASE DE DATOS
# ==============================
conn = sqlite3.connect("fisiosport.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    lesion TEXT,
    fase TEXT
)
""")

conn.commit()

# ==============================
# FUNCIONES SEGURIDAD
# ==============================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def registrar_usuario(email, password):
    try:
        cursor.execute(
            "INSERT INTO usuarios (email, password) VALUES (?, ?)",
            (email, hash_password(password))
        )
