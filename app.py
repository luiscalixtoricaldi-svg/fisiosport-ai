import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import io

st.set_page_config(page_title="FisioSport AI", page_icon="🏥")

# ---------------- DATABASE ----------------

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
        usuario_email TEXT,
        nombre TEXT,
        edad INTEGER,
        lesion TEXT,
        dolor INTEGER,
        fase TEXT,
        observaciones TEXT,
        fecha TEXT
    )
    """)

    conn.commit()
    conn.close()

crear_tablas()

# ---------------- SEGURIDAD ----------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- USUARIOS ----------------

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

# ---------------- PACIENTES ----------------

def registrar_paciente(usuario_email, nombre, edad, lesion, dolor, fase, obs, fecha):
    conn = crear_conexion()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO pacientes 
    (usuario_email, nombre, edad, lesion, dolor, fase, observaciones, fecha)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (usuario_email, nombre, edad, lesion, dolor, fase, obs, fecha))
    conn.commit()
    conn.close()

def obtener_pacientes(usuario_email):
    conn = crear_conexion()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT nombre, edad, lesion, dolor, fase, fecha
    FROM pacientes
    WHERE usuario_email = ?
    ORDER BY fecha DESC
    """, (usuario_email,))
    datos = cursor.fetchall()
    conn.close()
    return datos

# ---------------- MOTOR IA REGLAS ----------------

def recomendar_ejercicios(lesion, dolor, fase):
    lesion = lesion.lower()

    if "lca" in lesion:
        if fase == "Aguda":
            return "Isométricos de cuádriceps + control inflamatorio"
        elif fase == "Subaguda":
            return "Propiocepción + fortalecimiento cadena cerrada"
        else:
            return "Pliometría progresiva"

    if "tendinitis" in lesion:
        if dolor >= 7:
            return "Isométricos 5x45s"
        else:
            return "Excéntricos progresivos"

    if "hombro" in lesion:
        return "Fortalecimiento escapular + rotadores externos"

    return "Movilidad + fortalecimiento progresivo"

# ---------------- MODELO ML ----------------

def entrenar_modelo():
    X = np.array([[2,0],[8,1],[5,2],[9,0],[3,1]])
    y = np.array([0,1,0,1,0])
    modelo = LogisticRegression()
    modelo.fit(X,y)
    return modelo

modelo_ml = entrenar_modelo()

# ---------------- BIOMECÁNICA ----------------

def clasificar_angulo(angulo):
    if angulo < 60:
        return "Limitación severa"
    elif angulo < 120:
        return "Limitación moderada"
    else:
        return "Rango funcional"

# ---------------- PDF ----------------

def generar_pdf(datos):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>Reporte Clínico - FisioSport AI</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    for key, value in datos.items():
        elements.append(Paragraph(f"<b>{key}:</b> {value}", styles["Normal"]))
        elements.append(Spacer(1, 0.2 * inch))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ---------------- SESIÓN ----------------

if "usuario" not in st.session_state:
    st.session_state.usuario = None

# ---------------- INTERFAZ ----------------

st.title("🏥 FisioSport AI")

menu = ["Login", "Registro"]
opcion = st.sidebar.selectbox("Menú", menu)

if opcion == "Registro":
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Registrar"):
        if registrar_usuario(email, password):
            st.success("Usuario registrado")
        else:
            st.error("Email ya registrado")

if opcion == "Login":
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Entrar"):
        if login_usuario(email, password):
            st.session_state.usuario = email
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

# ---------------- PANEL ----------------

if st.session_state.usuario:

    st.sidebar.success(f"Conectado: {st.session_state.usuario}")

    if st.sidebar.button("Cerrar sesión"):
        st.session_state.usuario = None
        st.rerun()

    st.header("Registro Clínico")

    nombre = st.text_input("Nombre paciente")
    edad = st.number_input("Edad", 0, 120)
    lesion = st.text_input("Lesión")
    dolor = st.slider("Dolor EVA", 0, 10)
    fase = st.selectbox("Fase", ["Aguda", "Subaguda", "Crónica"])
    obs = st.text_area("Observaciones")
    fecha = st.date_input("Fecha")

    if st.button("Guardar paciente"):

        registrar_paciente(
            st.session_state.usuario,
            nombre,
            edad,
            lesion,
            dolor,
            fase,
            obs,
            str(fecha)
        )

        st.success("Paciente guardado")

        # IA reglas
        recomendacion = recomendar_ejercicios(lesion, dolor, fase)
        st.subheader("Recomendación IA")
        st.info(recomendacion)

        # ML
        entrada = np.array([[dolor, ["Aguda","Subaguda","Crónica"].index(fase)]])
        pred = modelo_ml.predict(entrada)

        if pred[0] == 1:
            st.warning("Modelo ML: Apto para carga progresiva")
        else:
            st.info("Modelo ML: Mantener fase conservadora")

        # PDF
        datos_pdf = {
            "Nombre": nombre,
            "Edad": edad,
            "Lesión": lesion,
            "Dolor": dolor,
            "Fase": fase,
            "Recomendación": recomendacion
        }

        pdf = generar_pdf(datos_pdf)

        st.download_button(
            label="Descargar reporte PDF",
            data=pdf,
            file_name="reporte_clinico.pdf",
            mime="application/pdf"
        )

    # ---------------- HISTORIAL ----------------

    st.header("Historial de Pacientes")

    pacientes = obtener_pacientes(st.session_state.usuario)

    if pacientes:
        df = pd.DataFrame(pacientes, columns=["Nombre","Edad","Lesión","Dolor","Fase","Fecha"])
        st.dataframe(df)

        st.subheader("Dashboard Clínico")
        st.metric("Total Pacientes", len(df))
        st.metric("Dolor Promedio", round(df["Dolor"].mean(),2))
        st.bar_chart(df["Dolor"])

    # ---------------- BIOMECÁNICA ----------------

    st.header("Evaluación Biomecánica")

    angulo = st.number_input("Ángulo articular (°)", 0, 180)

    if st.button("Evaluar ángulo"):
        st.success(clasificar_angulo(angulo))
