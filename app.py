import streamlit as st
import sqlite3
import hashlib
import os
# --------------------------------
import sqlite3
import hashlib

# ---------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------

st.set_page_config(page_title="FisioSport AI", page_icon="🏥")

# ---------------------------
# FUNCIONES BASE DE DATOS
# ---------------------------

def crear_conexion():
    conn = sqlite3.connect("fisiosport.db", check_same_thread=False)
    return conn

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

    conn.commit()
    conn.close()

crear_tablas()

# ---------------------------
# SEGURIDAD
# ---------------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------------
# FUNCIONES USUARIO
# ---------------------------

def registrar_usuario(email, password):
    try:
        conn = crear_conexion()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO usuarios (email, password) VALUES (?, ?)",
            (email, hash_password(password))
        )

        conn.commit()
        conn.close()
        return True

    except sqlite3.IntegrityError:
        return False


def login_usuario(email, password):
    conn = crear_conexion()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM usuarios WHERE email=? AND password=?",
        (email, hash_password(password))
    )

    data = cursor.fetchone()
    conn.close()

    return data


# ---------------------------
# SESIÓN
# ---------------------------

if "usuario" not in st.session_state:
    st.session_state.usuario = None


# ---------------------------
# INTERFAZ
# ---------------------------

st.title("🏥 FisioSport AI")

menu = ["Login", "Registro"]
opcion = st.sidebar.selectbox("Menú", menu)

# ---------------------------
# REGISTRO
# ---------------------------

if opcion == "Registro":

    st.subheader("Crear cuenta")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Registrar"):

        if email == "" or password == "":
            st.warning("Completa todos los campos")
        else:
            resultado = registrar_usuario(email, password)

            if resultado:
                st.success("Usuario registrado correctamente")
            else:
                st.error("Este email ya está registrado")


# ---------------------------
# LOGIN
# ---------------------------

if opcion == "Login":

    st.subheader("Iniciar sesión")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Entrar"):

        usuario = login_usuario(email, password)

        if usuario:
            st.session_state.usuario = email
            st.success("Login correcto")
            st.rerun()
        else:
            st.error("Credenciales incorrectas")


# ---------------------------
# PANEL PRINCIPAL
# ---------------------------

if st.session_state.usuario:

    st.sidebar.success(f"Conectado: {st.session_state.usuario}")

    if st.sidebar.button("Cerrar sesión"):
        st.session_state.usuario = None
        st.rerun()

    st.header("Panel Clínico")
    st.write("Bienvenido a FisioSport AI.")
    st.write("Aquí iremos agregando pacientes y análisis clínico.")
