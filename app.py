import streamlit as st
import sqlite3
import hashlib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.linear_model import LinearRegression
from PIL import Image

st.set_page_config(page_title="FisioSport AI ULTRA", layout="wide")

# ==========================
# BASE DE DATOS MULTIUSUARIO
# ==========================
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
    usuario_id INTEGER,
    nombre TEXT,
    lesion TEXT,
    fase TEXT,
    fecha TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sesiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER,
    rom REAL,
    fecha TEXT
)
""")

conn.commit()

# ==========================
# SEGURIDAD
# ==========================
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

# ==========================
# MACHINE LEARNING
# ==========================
def predecir_rom_futuro(sesiones):
    if len(sesiones) < 2:
        return None

    X = np.arange(len(sesiones)).reshape(-1, 1)
    y = sesiones["rom"].values

    model = LinearRegression()
    model.fit(X, y)

    next_index = np.array([[len(sesiones)]])
    prediction = model.predict(next_index)[0]

    return round(prediction, 2)

# ==========================
# ROM MANUAL
# ==========================
def calcular_angulo(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba, bc = a-b, c-b
    norma = np.linalg.norm(ba) * np.linalg.norm(bc)
    if norma == 0:
        return 0
    cos_angle = np.dot(ba, bc) / norma
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return round(np.degrees(np.arccos(cos_angle)), 2)

# ==========================
# SESIÓN
# ==========================
if "usuario" not in st.session_state:
    st.session_state.usuario = None
    st.session_state.usuario_id = None

# ==========================
# LOGIN
# ==========================
if st.session_state.usuario is None:

    st.title("FisioSport AI ULTRA")

    opcion = st.radio("Opción", ["Login", "Registrar"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if opcion == "Registrar" and st.button("Registrar"):
        if registrar_usuario(email, password):
            st.success("Registrado")
        else:
            st.error("Correo ya existe")

    if opcion == "Login" and st.button("Ingresar"):
        user = login_usuario(email, password)
        if user:
            st.session_state.usuario = email
            st.session_state.usuario_id = user[0]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

# ==========================
# APP PRINCIPAL
# ==========================
else:

    menu = st.sidebar.radio("Menú", [
        "Dashboard",
        "Nuevo Paciente",
        "Sesión ROM",
        "Historial + ML",
        "Cámara / Imagen"
    ])

    # DASHBOARD
    if menu == "Dashboard":
        df = pd.read_sql_query(
            f"SELECT * FROM pacientes WHERE usuario_id={st.session_state.usuario_id}",
            conn
        )
        st.metric("Pacientes Totales", len(df))

    # NUEVO PACIENTE
    if menu == "Nuevo Paciente":
        nombre = st.text_input("Nombre")
        lesion = st.selectbox("Lesión", ["Rodilla", "Hombro"])
        fase = st.selectbox("Fase", ["Aguda", "Subaguda", "Crónica"])

        if st.button("Guardar"):
            fecha = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "INSERT INTO pacientes (usuario_id, nombre, lesion, fase, fecha) VALUES (?, ?, ?, ?, ?)",
                (st.session_state.usuario_id, nombre, lesion, fase, fecha)
            )
            conn.commit()
            st.success("Paciente creado")

    # SESIÓN ROM
    if menu == "Sesión ROM":
        pacientes = pd.read_sql_query(
            f"SELECT * FROM pacientes WHERE usuario_id={st.session_state.usuario_id}",
            conn
        )

        if not pacientes.empty:
            nombre = st.selectbox("Paciente", pacientes["nombre"])
            rom = st.number_input("ROM medido (°)", 0.0, 180.0)

            if st.button("Registrar ROM"):
                paciente_id = pacientes[pacientes["nombre"]==nombre]["id"].values[0]
                fecha = datetime.now().strftime("%Y-%m-%d")
                cursor.execute(
                    "INSERT INTO sesiones (paciente_id, rom, fecha) VALUES (?, ?, ?)",
                    (paciente_id, rom, fecha)
                )
                conn.commit()
                st.success("Sesión guardada")

    # HISTORIAL + ML
    if menu == "Historial + ML":
        pacientes = pd.read_sql_query(
            f"SELECT * FROM pacientes WHERE usuario_id={st.session_state.usuario_id}",
            conn
        )

        if not pacientes.empty:
            nombre = st.selectbox("Paciente", pacientes["nombre"])
            paciente_id = pacientes[pacientes["nombre"]==nombre]["id"].values[0]

            sesiones = pd.read_sql_query(
                f"SELECT * FROM sesiones WHERE paciente_id={paciente_id}",
                conn
            )

            if not sesiones.empty:
                st.line_chart(sesiones["rom"])

                prediccion = predecir_rom_futuro(sesiones)
                if prediccion:
                    st.success(f"Predicción próxima sesión: {prediccion}°")
            else:
                st.info("Sin sesiones registradas")

    # CÁMARA / IMAGEN
    if menu == "Cámara / Imagen":
        st.header("Medición manual desde imagen")

        uploaded = st.file_uploader("Subir imagen", type=["jpg","png"])

        if uploaded:
            img = Image.open(uploaded)
            st.image(img, use_column_width=True)

            st.info("Ingrese manualmente 3 puntos para cálculo de ángulo")

            ax = st.number_input("Ax")
            ay = st.number_input("Ay")
            bx = st.number_input("Bx")
            by = st.number_input("By")
            cx = st.number_input("Cx")
            cy = st.number_input("Cy")

            if st.button("Calcular Ángulo"):
                angulo = calcular_angulo((ax,ay),(bx,by),(cx,cy))
                st.success(f"Ángulo: {angulo}°")

    if st.sidebar.button("Cerrar sesión"):
        st.session_state.usuario = None
        st.session_state.usuario_id = None
        st.rerun()
