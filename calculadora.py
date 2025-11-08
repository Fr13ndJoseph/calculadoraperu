# Calculadora Nutricional Perú – con pantalla de bienvenida y nombre personalizado
# Proyecto educativo – no reemplaza orientación médica profesional.

import tkinter as tk
from tkinter import ttk, messagebox
import random, os, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

# Paleta de colores
PALETTE = {
    "bg": "#F8FAFC",
    "primary": "#0ea5e9",
    "accent": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "ink": "#0f172a"
}

# Funciones de cálculo
def clasificar_imc(v):
    if v < 18.5: return "Bajo peso"
    if v < 25: return "Peso normal"
    if v < 30: return "Sobrepeso"
    return "Obesidad"

def bmr_mifflin(sexo, kg, m, edad):
    cm = m * 100
    return 10 * kg + 6.25 * cm - 5 * edad + (5 if sexo == "M" else -161)

def tdee(bmr, factor): return bmr * factor
def agua_ml(kg): return int(round(kg * 35))

ACTIVIDADES = {"Sedentario":1.2,"Ligero":1.375,"Moderado":1.55,"Intenso":1.725,"Muy intenso":1.9}
OBJETIVOS = {"Bajar (-15%)":-0.15,"Mantener (0%)":0.0,"Subir (+15%)":0.15}
HORARIOS = [("07:30","Desayuno"),("10:30","Snack AM"),("13:30","Almuerzo"),("16:30","Snack PM"),("20:00","Cena")]
DIAS = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
DISTRIB = {"Desayuno":0.25,"Snack AM":0.1,"Almuerzo":0.35,"Snack PM":0.1,"Cena":0.2}

# Platos peruanos
PLATOS_PE = {
    "Bajo peso":{"Desayuno":["Pan con palta y huevo","Quinua con leche y plátano"],
                 "Snack AM":["Yogur + granola"],"Almuerzo":["Lomo saltado + arroz + ensalada"],
                 "Snack PM":["Mazamorra morada"],"Cena":["Causa de pollo + ensalada"],
                 "notas":"Añade calorías saludables."},
    "Peso normal":{"Desayuno":["Avena con leche + fruta"],"Snack AM":["Yogur natural"],
                 "Almuerzo":["Pollo a la plancha + arroz integral"],"Snack PM":["Queso fresco + tomate"],
                 "Cena":["Sopa de verduras + omelette"],"notas":"Mantén equilibrio diario."},
    "Sobrepeso":{"Desayuno":["Avena en agua + fruta"],"Snack AM":["Fruta entera"],
                 "Almuerzo":["Pescado + verduras + arroz integral"],"Snack PM":["Fruta + puñado de maní"],
                 "Cena":["Sopa de quinua + pollo"],"notas":"Evita bebidas azucaradas."},
    "Obesidad":{"Desayuno":["Omelette verduras + pan integral"],"Snack AM":["Gelatina sin azúcar"],
                 "Almuerzo":["Pescado al horno + ensalada"],"Snack PM":["Queso fresco + tomate"],
                 "Cena":["Crema de zapallo + pollo"],"notas":"Evita ultraprocesados."}
}

# ----------------------- APP PRINCIPAL -----------------------
class CalculadoraApp:
    def __init__(self, root):
        self.root = root
        root.title("Calculadora Nutricional Perú")
        root.geometry("960x620")
        self.crear_ui()

    def crear_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Accent.TButton", background=PALETTE["accent"], foreground="white")
        style.configure("Primary.TButton", background=PALETTE["primary"], foreground="white")
        style.configure("Warning.TButton", background=PALETTE["warning"], foreground="white")

        # Marco principal
        f = tk.Frame(self.root, bg="white")
        f.pack(fill="x", pady=6)

        # Campo de nombres
        tk.Label(f, text="Nombres y Apellidos:", bg="white", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=6, pady=6)
        self.nombres = tk.Entry(f, width=40)
        self.nombres.grid(row=0, column=1, columnspan=4, padx=6, pady=6)

        # Datos personales
        self.sexo = tk.StringVar(value="M")
        ttk.Radiobutton(f, text="Masculino", variable=self.sexo, value="M").grid(row=1, column=0, padx=4)
        ttk.Radiobutton(f, text="Femenino", variable=self.sexo, value="F").grid(row=1, column=1, padx=4)
        tk.Label(f, text="Edad:", bg="white").grid(row=1, column=2)
        self.ed = tk.Entry(f, width=6); self.ed.grid(row=1, column=3)
        tk.Label(f, text="Peso (kg):", bg="white").grid(row=1, column=4)
        self.pe = tk.Entry(f, width=6); self.pe.grid(row=1, column=5)
        tk.Label(f, text="Altura (m):", bg="white").grid(row=1, column=6)
        self.al = tk.Entry(f, width=6); self.al.grid(row=1, column=7)

        # Actividad y objetivo
        self.cb_act = ttk.Combobox(f, values=list(ACTIVIDADES.keys()), width=15, state="readonly"); self.cb_act.current(1)
        self.cb_act.grid(row=2, column=0, columnspan=2, padx=4, pady=4)
        self.cb_obj = ttk.Combobox(f, values=list(OBJETIVOS.keys()), width=15, state="readonly"); self.cb_obj.current(1)
        self.cb_obj.grid(row=2, column=2, columnspan=2, padx=4, pady=4)

        ttk.Button(f, text="Calcular", style="Primary.TButton", command=self.calcular).grid(row=2, column=6)
        ttk.Button(f, text="Exportar PDF", style="Warning.TButton", command=self.exportar_pdf).grid(row=2, column=7)

        self.res = tk.Label(self.root, text="—", bg="white", font=("Segoe UI", 10))
        self.res.pack(fill="x", pady=6)

        # Tabla
        self.tree = ttk.Treeview(self.root, columns=("Día","Hora","Comida","Menú","Calorías"), show="headings", height=15)
        for c in ("Día","Hora","Comida","Menú","Calorías"): self.tree.heading(c, text=c)
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)

    def calcular(self):
        try:
            nombre = self.nombres.get().strip()
            s = self.sexo.get(); e = int(self.ed.get()); p = float(self.pe.get()); a = float(self.al.get())
            act = ACTIVIDADES[self.cb_act.get()]; obj = OBJETIVOS[self.cb_obj.get()]
            imc = p/(a**2); cat = clasificar_imc(imc); bmr = bmr_mifflin(s,p,a,e); tdee_v = tdee(bmr,act)
            kcal = int(round(tdee_v*(1+obj))); agua = agua_ml(p)
            self.res.config(text=f"{nombre} – IMC {imc:.2f} ({cat}) | BMR {int(bmr)} | TDEE {int(tdee_v)} | Objetivo {kcal} kcal | Agua {agua} ml")
            self.tree.delete(*self.tree.get_children())
            filas = []
            for d in DIAS:
                for h,t in HORARIOS:
                    op = PLATOS_PE[cat][t][0]; cal = int(round(kcal*DISTRIB[t]))
                    filas.append((d,h,t,op,f"{cal} kcal"))
            for f in filas: self.tree.insert("", "end", values=f)
            self._datos = dict(nombre=nombre, cat=cat, imc=imc, bmr=int(bmr), tdee=int(tdee_v), kcal=kcal, agua=agua)
            messagebox.showinfo("Listo", "Plan generado correctamente.")
        except:
            messagebox.showerror("Error", "Verifica los valores ingresados.")

    def exportar_pdf(self):
        if not hasattr(self,"_datos"):
            messagebox.showwarning("Atención","Calcula primero tu plan."); return
        desk = os.path.join(os.path.expanduser("~"),"Desktop"); os.makedirs(desk, exist_ok=True)
        cat = self._datos["cat"].replace(" ","_"); stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        nombre_archivo = f"Plan_peru_{cat}_{stamp}.pdf"
        filename = os.path.join(desk, nombre_archivo)
        try:
            doc = SimpleDocTemplate(filename, pagesize=A4); styles = getSampleStyleSheet(); c = []
            c.append(Paragraph("<b>PLAN NUTRICIONAL – PERÚ</b>", styles["Title"])); c.append(Spacer(1,10))
            d = self._datos
            c.append(Paragraph(f"<b>Nombre:</b> {d['nombre']}<br/><b>IMC:</b> {d['imc']:.2f} ({d['cat']})<br/>"
                               f"<b>BMR:</b> {d['bmr']} kcal | <b>TDEE:</b> {d['tdee']} kcal | "
                               f"<b>Objetivo:</b> {d['kcal']} kcal/día | <b>Agua:</b> {d['agua']} ml", styles["Normal"]))
            c.append(Spacer(1,10))
            data = [["Día","Hora","Comida","Menú","Calorías"]] + [self.tree.item(i,"values") for i in self.tree.get_children()]
            t = Table(data, colWidths=[60,45,70,280,60])
            t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("GRID",(0,0),(-1,-1),0.25,colors.black)]))
            c.append(t); c.append(Spacer(1,8))
            c.append(Paragraph("<font size=8 color=gray>Proyecto educativo. Ajusta porciones y consulta a un profesional.</font>", styles["Normal"]))
            doc.build(c)
            messagebox.showinfo("PDF creado", f"Guardado en tu Escritorio como:\n{nombre_archivo}")
            try: os.startfile(filename)
            except: pass
        except Exception as e:
            messagebox.showerror("Error", str(e))

# ----------------------- BIENVENIDA -----------------------
def mostrar_bienvenida():
    splash = tk.Tk()
    splash.title("Bienvenido")
    splash.geometry("700x400")
    splash.config(bg="#0ea5e9")

    tk.Label(splash, text="Bienvenido a la Calculadora Nutricional Perú 🇵🇪",
             bg="#0ea5e9", fg="white", font=("Segoe UI", 18, "bold")).pack(pady=30)
    texto = ("Esta aplicación te ayudará a conocer tu IMC, gasto calórico y plan nutricional personalizado.\n"
             "Incluye comidas típicas del Perú y permite exportar tu plan semanal en PDF.\n\n"
             "Ingresa tus datos y obtén un plan hecho a tu medida.")
    tk.Label(splash, text=texto, bg="#0ea5e9", fg="white", font=("Segoe UI", 12), wraplength=600, justify="center").pack(pady=10)

    def iniciar():
        splash.destroy()
        root = tk.Tk()
        CalculadoraApp(root)
        root.mainloop()

    ttk.Button(splash, text="Comenzar →", style="Accent.TButton", command=iniciar).pack(pady=40)
    splash.mainloop()

if __name__ == "__main__":
    mostrar_bienvenida()