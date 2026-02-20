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

def login_usuario(email, password):
    conn = crear_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM usuarios WHERE email = ?", (email,))
    usuario = cursor.fetchone()
    conn.close()

    if usuario and usuario[1] == hash_password(password):
        return usuario[0]
    return None

def crear_paciente(usuario_id, nombre, edad, diagnostico):
    conn = crear_conexion()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO pacientes (usuario_id, nombre, edad, diagnostico)
    VALUES (?, ?, ?, ?)
    """, (usuario_id, nombre, edad, diagnostico))
    conn.commit()
    conn.close()

def obtener_pacientes(usuario_id):
    conn = crear_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM pacientes WHERE usuario_id = ?", (usuario_id,))
    datos = cursor.fetchall()
    conn.close()
    return datos

def guardar_evaluacion(paciente_id, angulo, asimetria):
    riesgo = evaluar_riesgo(asimetria)
    fecha = datetime.now().strftime("%Y-%m-%d")

    conn = crear_conexion()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO evaluaciones (paciente_id, fecha, angulo, asimetria, riesgo)
    VALUES (?, ?, ?, ?, ?)
    """, (paciente_id, fecha, angulo, asimetria, riesgo))
    conn.commit()
    conn.close()

def obtener_historial(paciente_id):
    conn = crear_conexion()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT fecha, angulo, asimetria, riesgo
    FROM evaluaciones
    WHERE paciente_id = ?
    """, (paciente_id,))
    datos = cursor.fetchall()
    conn.close()
    return datos

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

if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None

menu = st.sidebar.selectbox("Menú", ["Login", "Registro"])

if st.session_state.usuario_id is None:

    if menu == "Registro":
        st.subheader("Registro Profesional")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Registrar"):
            registrar_usuario(email, password)
            st.success("Usuario registrado")

    elif menu == "Login":
        st.subheader("Ingreso Profesional")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Ingresar"):
            usuario_id = login_usuario(email, password)
            if usuario_id:
                st.session_state.usuario_id = usuario_id
                st.success("Login exitoso")
            else:
                st.error("Credenciales incorrectas")

else:
    st.sidebar.write("Sesión activa")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.usuario_id = None
        st.experimental_rerun()

    opcion = st.sidebar.selectbox("Panel", ["Pacientes", "Nueva Evaluación"])

    if opcion == "Pacientes":
        st.subheader("Crear Paciente")
        nombre = st.text_input("Nombre")
        edad = st.number_input("Edad", 10, 80)
        diagnostico = st.text_input("Diagnóstico")

        if st.button("Guardar paciente"):
            crear_paciente(st.session_state.usuario_id, nombre, edad, diagnostico)
            st.success("Paciente creado")

        st.subheader("Listado de Pacientes")
        pacientes = obtener_pacientes(st.session_state.usuario_id)
        st.write(pacientes)

    elif opcion == "Nueva Evaluación":
        pacientes = obtener_pacientes(st.session_state.usuario_id)
        if pacientes:
            paciente_dict = {p[1]: p[0] for p in pacientes}
            seleccionado = st.selectbox("Seleccionar paciente", paciente_dict.keys())

            angulo = st.number_input("Ángulo")
            asimetria = st.number_input("Asimetría (%)")

            if st.button("Evaluar"):
                guardar_evaluacion(paciente_dict[seleccionado], angulo, asimetria)
                st.success("Evaluación guardada")

            st.subheader("Historial")
            historial = obtener_historial(paciente_dict[seleccionado])
            if historial:
                df = pd.DataFrame(historial, columns=["Fecha", "Ángulo", "Asimetría", "Riesgo"])
                st.dataframe(df)
