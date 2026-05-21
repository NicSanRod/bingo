import os
from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name="dcbyqpk3b",
    api_key="281568496983838",
    api_secret="-pTKqawctrK42fnXN3Kdq0BxkTc"
)

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bingos.db"

db = SQLAlchemy(app)

class Bingo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    retos = db.Column(db.Text)

class Reto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bingo_id = db.Column(db.Integer)
    texto = db.Column(db.String(200))
    completado = db.Column(db.Boolean, default=False)
    imagen = db.Column(db.String(200))  # ruta del archivo

with app.app_context():
    db.drop_all()
    db.create_all()

@app.route("/")
def index():
    return render_template("inicio.html")

@app.route("/crear", methods=["GET", "POST"])
def crear():
    if request.method == "POST":
        nombre = request.form["nombre"]
        retos = request.form.getlist("reto")
        nuevo_bingo = Bingo(nombre=nombre, retos="||".join(retos))
        db.session.add(nuevo_bingo)
        db.session.commit()
        for r in retos:
            if r.strip():
                db.session.add(Reto(
                    bingo_id=nuevo_bingo.id,
                    texto=r
                ))
        db.session.commit()
        return redirect("/")
    tamaño=5
    return render_template("crear.html", tamaño=tamaño)
@app.route("/mis-bingos")
def mis_bingos():
    bingos = Bingo.query.all()
    return render_template("mis-bingos.html", bingos=bingos)

@app.route("/bingo/<int:id>")
def ver_bingo(id):
    bingo = Bingo.query.get_or_404(id)
    retos = Reto.query.filter_by(bingo_id=id).all()
    return render_template("bingo.html", bingo=bingo, retos=retos)

@app.route("/subir/<int:reto_id>", methods=["POST"])
def subir_imagen(reto_id):

    file = request.files["imagen"]

    upload_result = cloudinary.uploader.upload(file)

    url = upload_result["secure_url"]

    reto = Reto.query.get(reto_id)
    reto.imagen = url
    reto.completado = True

    db.session.commit()

    return redirect(f"/bingo/{reto.bingo_id}")

if __name__ == "__main__":
    app.run(debug=True)