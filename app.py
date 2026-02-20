import streamlit as st
import sqlite3
import hashlib
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import os

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="FisioSport AI", layout="wide")

# =========================
# BASE DE DATOS
# =========================
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

# =========================
# FUNCIONES
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def registrar_usuario(email, password):
    try:
        cursor.execute("INSERT INTO usuarios (email, password) VALUES (?, ?)",
                       (email, hash_password(password)))
        conn.commit()
        return True
    except:
        return False

def login_usuario(email, password):
    cursor.execute("SELECT * FROM usuarios WHERE email=? AND password=?",
                   (email, hash_password(password)))
    return cursor.fetchone()

def recomendar_ejercicio(lesion, fase):
    if lesion == "Rodilla" and fase == "Aguda":
        return ["Isométricos de cuádriceps", "Elevaciones de pierna recta"]
    if lesion == "Rodilla" and fase == "Subaguda":
        return ["Sentadilla parcial", "Step-up bajo"]
    if lesion == "Hombro" and fase == "Aguda":
        return ["Péndulo de Codman", "Isométricos de manguito"]
    if lesion == "Hombro" and fase == "Subaguda":
        return ["Rotaciones externas con banda", "Elevaciones frontales"]
    return ["Ejercicios personalizados"]

# =========================
# ANGULO BIOMECÁNICO
# =========================
def calcular_angulo(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    ba = a - b
    bc = c - b

    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.degrees(np.arccos(cos_angle))
    return round(angle, 2)

# =========================
# LOGIN
# =========================
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.title("🔐 FisioSport AI - Login")

    opcion = st.radio("Selecciona opción", ["Login", "Registrar"])

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if opcion == "Registrar":
        if st.button("Registrar"):
            if registrar_usuario(email, password):
                st.success("Usuario registrado")
            else:
                st.error("Usuario ya existe")

    if opcion == "Login":
        if st.button("Ingresar"):
            if login_usuario(email, password):
                st.session_state.usuario = email
                st.success("Bienvenido")
            else:
                st.error("Credenciales incorrectas")

else:
    st.sidebar.title("FisioSport AI")
    menu = st.sidebar.radio("Menú", [
        "Registro Paciente",
        "Recomendación Ejercicios",
        "Evaluación Biomecánica",
        "Base de Datos Pacientes"
    ])

    # =========================
    # REGISTRO PACIENTE
    # =========================
    if menu == "Registro Paciente":
        st.header("Registro de Paciente")

        nombre = st.text_input("Nombre")
        lesion = st.selectbox("Lesión", ["Rodilla", "Hombro"])
        fase = st.selectbox("Fase", ["Aguda", "Subaguda"])

        if st.button("Guardar"):
            cursor.execute("INSERT INTO pacientes (nombre, lesion, fase) VALUES (?, ?, ?)",
                           (nombre, lesion, fase))
            conn.commit()
            st.success("Paciente registrado")

    # =========================
    # RECOMENDACIONES
    # =========================
    if menu == "Recomendación Ejercicios":
        st.header("Recomendación Automática")

        lesion = st.selectbox("Lesión", ["Rodilla", "Hombro"])
        fase = st.selectbox("Fase", ["Aguda", "Subaguda"])

        if st.button("Generar"):
            ejercicios = recomendar_ejercicio(lesion, fase)
            st.write("Ejercicios recomendados:")
            for e in ejercicios:
                st.success(e)

    # =========================
    # BIOMECÁNICA
    # =========================
    if menu == "Evaluación Biomecánica":
        st.header("Análisis de Ángulo (Ejemplo Rodilla)")

        cadera = st.number_input("Coordenada Cadera (ejemplo 100)")
        rodilla = st.number_input("Coordenada Rodilla (ejemplo 150)")
        tobillo = st.number_input("Coordenada Tobillo (ejemplo 200)")

        if st.button("Calcular Ángulo"):
            angulo = calcular_angulo(
                (cadera, cadera),
                (rodilla, rodilla),
                (tobillo, tobillo)
            )
            st.success(f"Ángulo estimado: {angulo}°")

    # =========================
    # BASE DE DATOS
    # =========================
    if menu == "Base de Datos Pacientes":
        st.header("Pacientes Registrados")

        df = pd.read_sql_query("SELECT * FROM pacientes", conn)
        st.dataframe(df)

    if st.sidebar.button("Cerrar sesión"):
        st.session_state.usuario = None
        st.experimental_rerun()
