from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os
import qrcode

app = Flask(__name__)
app.secret_key = "clave_secreta"

ARCHIVO = "inventario.xlsx"
CARPETA_QR = "static/qr"

os.makedirs(CARPETA_QR, exist_ok=True)

USUARIO = "admin"
PASSWORD = "1234"

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["usuario"] == USUARIO and request.form["password"] == PASSWORD:
            session["login"] = True
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- DATOS ----------------
def cargar_datos():
    if not os.path.exists(ARCHIVO):
        df = pd.DataFrame(columns=["ID", "Producto", "Cantidad", "Precio", "QR"])
        df.to_excel(ARCHIVO, index=False)
    return pd.read_excel(ARCHIVO)

def guardar_datos(df):
    df.to_excel(ARCHIVO, index=False)

# ---------------- QR ----------------
def generar_qr(id_producto):
    url = f"http://127.0.0.1:5000/producto/{id_producto}"
    ruta = f"{CARPETA_QR}/{id_producto}.png"
    img = qrcode.make(url)
    img.save(ruta)
    return ruta

# ---------------- HOME ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    if "login" not in session:
        return redirect("/login")

    df = cargar_datos()
    query = request.form.get("query")

    if query:
        df = df[df["Producto"].str.contains(query, case=False)]

    return render_template("index.html", data=df.to_dict(orient="records"))

# ---------------- AGREGAR ----------------
@app.route("/agregar", methods=["GET", "POST"])
def agregar():
    if "login" not in session:
        return redirect("/login")

    if request.method == "POST":
        df = cargar_datos()

        nuevo_id = int(df["ID"].max() + 1) if not df.empty else 1

        nuevo = {
            "ID": nuevo_id,
            "Producto": request.form["producto"],
            "Cantidad": request.form["cantidad"],
            "Precio": request.form["precio"],
            "QR": generar_qr(nuevo_id)
        }

        df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
        guardar_datos(df)

        return redirect("/")

    return render_template("agregar.html")

# ---------------- EDITAR ----------------
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if "login" not in session:
        return redirect("/login")

    df = cargar_datos()

    if request.method == "POST":
        df.loc[df["ID"] == id, "Producto"] = request.form["producto"]
        df.loc[df["ID"] == id, "Cantidad"] = request.form["cantidad"]
        df.loc[df["ID"] == id, "Precio"] = request.form["precio"]

        guardar_datos(df)
        return redirect("/")

    producto = df[df["ID"] == id].to_dict(orient="records")[0]
    return render_template("editar.html", producto=producto)

# ---------------- ELIMINAR ----------------
@app.route("/eliminar/<int:id>")
def eliminar(id):
    if "login" not in session:
        return redirect("/login")

    df = cargar_datos()
    df = df[df["ID"] != id]
    guardar_datos(df)

    return redirect("/")

# ---------------- VER PRODUCTO (QR) ----------------
@app.route("/producto/<int:id>")
def ver_producto(id):
    df = cargar_datos()
    producto = df[df["ID"] == id]

    if producto.empty:
        return "Producto no encontrado"

    return render_template("producto.html", producto=producto.to_dict(orient="records")[0])

# ---------------- SUBIR EXCEL ----------------
@app.route("/subir", methods=["GET", "POST"])
def subir():
    if "login" not in session:
        return redirect("/login")

    if request.method == "POST":
        archivo = request.files["archivo"]
        if archivo:
            archivo.save(ARCHIVO)
        return redirect("/")

    return render_template("subir.html")

@app.route("/scanner")
def scanner():
    return render_template("scanner.html")

if __name__ == "__main__":
    app.run(debug=True)