# Calculadora Nutricional Perú (versión web con Streamlit)
# Proyecto educativo. No reemplaza consejo médico profesional.

import streamlit as st
import pandas as pd
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

# ------- Utilidades --------
def clasificar_imc(v):
    if v < 18.5: return "Bajo peso"
    if v < 25:   return "Peso normal"
    if v < 30:   return "Sobrepeso"
    return "Obesidad"

def bmr_mifflin(sexo, kg, m, edad):
    cm = m*100
    return 10*kg + 6.25*cm - 5*edad + (5 if sexo == "Masculino" else -161)

def tdee(bmr, factor): return bmr*factor
def agua_ml(kg): return int(round(kg*35))

ACTIVIDADES = {
    "Sedentario (poco o nada)": 1.2,
    "Ligero (1-3 d/sem)":       1.375,
    "Moderado (3-5 d/sem)":     1.55,
    "Intenso (6-7 d/sem)":      1.725,
    "Muy intenso (atleta)":     1.9,
}
OBJETIVOS = {"Bajar (−15%)":-0.15,"Mantener (0%)":0.0,"Subir (+15%)":0.15}

HORARIOS = [("07:30","Desayuno"),("10:30","Snack AM"),("13:30","Almuerzo"),("16:30","Snack PM"),("20:00","Cena")]
DIAS = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
DISTRIB = {"Desayuno":0.25,"Snack AM":0.10,"Almuerzo":0.35,"Snack PM":0.10,"Cena":0.20}

PLATOS_PE = {
    "Bajo peso": {
        "Desayuno":["Pan francés con palta + huevo","Quinua con leche + plátano"],
        "Snack AM":["Yogur + granola","Frutos secos"],
        "Almuerzo":["Lomo saltado + arroz + ensalada","Ají de gallina + arroz"],
        "Snack PM":["Mazamorra morada","Pan con queso"],
        "Cena":["Sopa criolla + pan","Causa de pollo + ensalada"],
        "notas":"Suma calorías saludables."
    },
    "Peso normal": {
        "Desayuno":["Avena con leche + fruta","Pan integral con palta"],
        "Snack AM":["Yogur natural","Fruta"],
        "Almuerzo":["Pollo plancha + arroz integral + ensalada","Pescado al horno + papa + ensalada"],
        "Snack PM":["Queso fresco + tomate","Yogur + avena"],
        "Cena":["Sopa de verduras + omelette","Sudado de pescado + yuca"],
        "notas":"Mantén equilibrio y agua 6–8 vasos/día."
    },
    "Sobrepeso": {
        "Desayuno":["Avena en agua + fruta","Pan integral + pavo + tomate"],
        "Snack AM":["Pepino/zanahoria","Yogur light"],
        "Almuerzo":["Pescado plancha + ensalada + arroz integral (pequeño)","Pollo parrilla + ensalada + papa (pequeña)"],
        "Snack PM":["Fruta + puñado pequeño de maní","Queso fresco + tomate"],
        "Cena":["Sopa de quinua + pollo","Ensalada andina + palta pequeña"],
        "notas":"Evita bebidas azucaradas y controla porciones."
    },
    "Obesidad": {
        "Desayuno":["Omelette verduras + pan integral (1)","Avena en agua + chía + fruta"],
        "Snack AM":["Gelatina sin azúcar","Pepino/zanahoria"],
        "Almuerzo":["Pescado al horno + ensalada + camote (pequeño)","Chaufa integral de verduras + pollo (bajo aceite)"],
        "Snack PM":["Ensalada de frutas (sin azúcar)","Requesón + tomate"],
        "Cena":["Crema de zapallo + pollo plancha","Ensalada completa + atún/huevo"],
        "notas":"Planifica compras y evita ultraprocesados."
    }
}

def generar_plan(cat, kcal_obj):
    filas = []
    for dia in DIAS:
        for hora, tiempo in HORARIOS:
            opciones = PLATOS_PE[cat][tiempo]
            menu = opciones[0]  # simple (puedes randomizar si quieres)
            kcal = int(round(kcal_obj * DISTRIB[tiempo]))
            filas.append((dia, hora, tiempo, menu, f"{kcal} kcal"))
    df = pd.DataFrame(filas, columns=["Día","Hora","Comida","Menú (Perú)","Calorías"])
    return df

def pdf_bytes(datos, df, notas):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    content = []
    content.append(Paragraph("<b>PLAN NUTRICIONAL – PERÚ</b>", styles["Title"]))
    content.append(Spacer(1, 8))
    res = (f"<b>Nombre:</b> {datos['nombre']}<br/>"
           f"<b>IMC:</b> {datos['imc']:.2f} ({datos['cat']}) &nbsp;&nbsp; "
           f"<b>BMR:</b> {datos['bmr']} kcal &nbsp;&nbsp; "
           f"<b>TDEE:</b> {datos['tdee']} kcal &nbsp;&nbsp; "
           f"<b>Objetivo:</b> {datos['kcal']} kcal/día &nbsp;&nbsp; "
           f"<b>Agua:</b> {datos['agua']} ml")
    content.append(Paragraph(res, styles["Normal"]))
    content.append(Spacer(1, 6))
    # tabla
    data = [df.columns.tolist()] + df.values.tolist()
    t = Table(data, colWidths=[60,45,70,285,60])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), colors.lightgrey),
        ("GRID",(0,0),(-1,-1),0.25, colors.black),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))
    content.append(t)
    content.append(Spacer(1, 6))
    content.append(Paragraph(f"<b>Notas:</b> {notas}", styles["Normal"]))
    content.append(Spacer(1, 6))
    content.append(Paragraph("<font size=8 color=gray>BMR: calorías en reposo. TDEE: gasto energético total diario.</font>", styles["Normal"]))
    doc.build(content)
    buf.seek(0)
    return buf

# ------- Interfaz Streamlit --------
st.set_page_config(page_title="Calculadora Nutricional Perú", page_icon="🇵🇪", layout="centered")

st.title("Calculadora Nutricional Perú 🇵🇪")
st.caption("Proyecto educativo – no reemplaza orientación médica profesional.")

col1, col2 = st.columns([1,1])
with col1:
    nombre = st.text_input("Nombres y Apellidos", "Edith Malqui")
    sexo = st.selectbox("Sexo", ["Femenino","Masculino"])
    edad = st.number_input("Edad (años)", 10, 100, 28)
with col2:
    peso = st.number_input("Peso (kg)", 30.0, 300.0, 85.0, step=0.1)
    altura = st.number_input("Altura (m)", 1.2, 2.3, 1.55, step=0.01)

act = st.selectbox("Nivel de actividad", list(ACTIVIDADES.keys()), index=1)
obj = st.selectbox("Objetivo", list(OBJETIVOS.keys()), index=0)

if st.button("Generar plan"):
    imc = peso/(altura**2)
    cat = clasificar_imc(imc)
    bmr = bmr_mifflin(sexo, peso, altura, edad)
    gasto = tdee(bmr, ACTIVIDADES[act])
    kcal_obj = int(round(gasto*(1+OBJETIVOS[obj])))
    agua = agua_ml(peso)

    df = generar_plan(cat, kcal_obj)
    st.subheader("Resumen")
    st.write(f"**IMC:** {imc:.2f} ({cat})  |  **BMR:** {int(bmr)} kcal  |  **TDEE:** {int(gasto)} kcal  |  **Objetivo:** {kcal_obj} kcal/día  |  **Agua:** {agua} ml/día")

    st.subheader("Plan semanal")
    st.dataframe(df, use_container_width=True)

    datos = dict(nombre=nombre, imc=imc, cat=cat, bmr=int(bmr), tdee=int(gasto), kcal=kcal_obj, agua=agua)
    notas = PLATOS_PE[cat]["notas"]
    pdf_buffer = pdf_bytes(datos, df, notas)

    st.download_button(
        label="⬇️ Descargar PDF",
        data=pdf_buffer,
        file_name=f"Plan_peru_{cat.replace(' ','_')}.pdf",
        mime="application/pdf"
    )
