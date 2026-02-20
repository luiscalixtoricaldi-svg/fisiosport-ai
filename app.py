import streamlit as st
import sqlite3
import bcrypt
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import io

st.set_page_config(page_title="FisioSport AI Pro", page_icon="🏥")

# ================= DATABASE LOCAL (backup) =================

def crear_conexion():
    return sqlite3.connect("fisiosport.db", check_same_thread=False)

def crear_tablas():
    conn = crear_conexion()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        rol TEXT
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

# ================= SEGURIDAD =================

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def verificar_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

# ================= USUARIOS =================

def registrar_usuario(email, password, rol):
    try:
        conn = crear_conexion()
        cursor = conn.cursor()
        hashed = hash_password(password)

        cursor.execute(
            "INSERT INTO usuarios (email, password, rol) VALUES (?, ?, ?)",
            (email, hashed, rol)
        )

        conn.commit()
        conn.close()
        return True
    except:
        return False

def login_usuario(email, password):
    conn = crear_conexion()
    cursor = conn.cursor()

    cursor.execute("SELECT email, password, rol FROM usuarios WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user:
        if verificar_password(password, user[1]):
            return {"email": user[0], "rol": user[2]}
    return None

# ================= PACIENTES =================

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

def obtener_pacientes(usuario_email, rol):
    conn = crear_conexion()
    cursor = conn.cursor()

    if rol == "admin":
        cursor.execute("SELECT nombre, edad, lesion, dolor, fase, fecha FROM pacientes")
    else:
        cursor.execute("""
        SELECT nombre, edad, lesion, dolor, fase, fecha
        FROM pacientes WHERE usuario_email = ?
        """, (usuario_email,))

    data = cursor.fetchall()
    conn.close()
    return data

# ================= IA REGLAS =================

def recomendar_ejercicios(lesion, dolor, fase):
    lesion = lesion.lower()
    if "lca" in lesion:
        return "Protocolo progresivo LCA según fase"
    if dolor >= 7:
        return "Fase protectora con isométricos"
    return "Fortalecimiento progresivo"

# ================= MODELO ML =================

def entrenar_modelo():
    X = np.array([[2,0],[8,1],[5,2],[9,0],[3,1]])
    y = np.array([0,1,0,1,0])
    model = LogisticRegression()
    model.fit(X,y)
    return model

modelo_ml = entrenar_modelo()

# ================= PDF =================

def generar_pdf(datos):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>Reporte Clínico - FisioSport AI Pro</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    for k,v in datos.items():
        elements.append(Paragraph(f"<b>{k}:</b> {v}", styles["Normal"]))
        elements.append(Spacer(1, 0.2 * inch))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ================= SESIÓN =================

if "usuario" not in st.session_state:
    st.session_state.usuario = None

# ================= UI =================

st.title("🏥 FisioSport AI Pro")

menu = ["Login", "Registro"]
opcion = st.sidebar.selectbox("Menú", menu)

# -------- REGISTRO --------

if opcion == "Registro":
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    rol = st.selectbox("Rol", ["fisioterapeuta","admin"])

    if st.button("Registrar"):
        if registrar_usuario(email, password, rol):
            st.success("Usuario creado")
        else:
            st.error("Error o email existente")

# -------- LOGIN --------

if opcion == "Login":
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Entrar"):
        user = login_usuario(email, password)
        if user:
            st.session_state.usuario = user
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

# -------- PANEL --------

if st.session_state.usuario:

    user = st.session_state.usuario

    st.sidebar.success(f"{user['email']} ({user['rol']})")

    if st.sidebar.button("Cerrar sesión"):
        st.session_state.usuario = None
        st.rerun()

    st.header("Registro Clínico")

    nombre = st.text_input("Paciente")
    edad = st.number_input("Edad", 0, 120)
    lesion = st.text_input("Lesión")
    dolor = st.slider("Dolor EVA", 0, 10)
    fase = st.selectbox("Fase", ["Aguda","Subaguda","Crónica"])
    obs = st.text_area("Observaciones")
    fecha = st.date_input("Fecha")

    if st.button("Guardar"):
        registrar_paciente(user["email"], nombre, edad, lesion, dolor, fase, obs, str(fecha))
        st.success("Paciente guardado")

        recomendacion = recomendar_ejercicios(lesion, dolor, fase)
        st.info(recomendacion)

        entrada = np.array([[dolor, ["Aguda","Subaguda","Crónica"].index(fase)]])
        pred = modelo_ml.predict(entrada)

        if pred[0] == 1:
            st.warning("ML: Carga progresiva indicada")
        else:
            st.info("ML: Mantener conservador")

        pdf = generar_pdf({
            "Paciente": nombre,
            "Lesión": lesion,
            "Dolor": dolor,
            "Fase": fase,
            "Recomendación": recomendacion
        })

        st.download_button("Descargar PDF", pdf, "reporte.pdf")

    st.header("Dashboard")

    pacientes = obtener_pacientes(user["email"], user["rol"])

    if pacientes:
        df = pd.DataFrame(pacientes, columns=["Nombre","Edad","Lesión","Dolor","Fase","Fecha"])
        st.dataframe(df)
        st.metric("Total", len(df))
        st.metric("Dolor promedio", round(df["Dolor"].mean(),2))
        st.bar_chart(df["Dolor"])
