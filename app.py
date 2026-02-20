
import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import pandas as pd

# -------------------
# BASE DE DATOS
# -------------------

def crear_conexion():
    return sqlite3.connect("fisiosport.db", check_same_thread=False)

def crear_tablas():
    conn = crear_conexion()
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
        usuario_id INTEGER,
        nombre TEXT,
        edad INTEGER,
        diagnostico TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER,
        fecha TEXT,
        angulo REAL,
        asimetria REAL,
        riesgo TEXT
    )
    """)

    conn.commit()
    conn.close()

crear_tablas()

# -------------------
# FUNCIONES
# -------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def registrar_usuario(email, password):
    conn = crear_conexion()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO usuarios (email, password) VALUES (?, ?)",
                   (email, hash_password(password)))
    conn.commit()
    conn.close()

def evaluar_riesgo(asimetria):
    if asimetria > 10:
        return "Alto"
    elif asimetria > 5:
        return "Moderado"
    else:
        return "Bajo"

# -------------------
# INTERFAZ
# -------------------

st.set_page_config(page_title="FisioSport AI", layout="wide")
st.title("🏥 FisioSport AI - Plataforma Clínica")

menu = st.sidebar.selectbox("Menú", ["Registro", "Nueva Evaluación"])

if menu == "Registro":
    st.subheader("Registro Profesional")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Registrar"):
        registrar_usuario(email, password)
        st.success("Usuario registrado")

elif menu == "Nueva Evaluación":
    st.subheader("Evaluación Clínica")
    paciente = st.text_input("Nombre Paciente")
    edad = st.number_input("Edad", 10, 60)
    angulo = st.number_input("Ángulo")
    asimetria = st.number_input("Asimetría (%)")

    if st.button("Evaluar"):
        riesgo = evaluar_riesgo(asimetria)
        st.metric("Nivel de Riesgo", riesgo)
