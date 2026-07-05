import os
from flask import Flask, redirect, render_template, request,session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_login import LoginManager, login_user, logout_user, login_required,current_user


import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name="dcbyqpk3b",
    api_key="281568496983838",
    api_secret="-pTKqawctrK42fnXN3Kdq0BxkTc"
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "una-clave-larga-y-dificil-de-adivinar"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://user:Aq96hgqvXCQRe1hypDpLMzYk77Byb2Ak@dpg-d8ng70ugvqtc7398ng40-a.oregon-postgres.render.com/mundial_ivdg"

db = SQLAlchemy(app)

class Bingo(db.Model):
    __tablename__ = "bingo"
    __table_args__ = {"schema": "bingo"}
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    retos = db.Column(db.Text)

class Reto(db.Model):
    __tablename__ = "reto"
    __table_args__ = {"schema": "bingo"}
    id = db.Column(db.Integer, primary_key=True)
    bingo_id = db.Column(db.Integer,db.ForeignKey("bingo.bingo.id"), nullable=False)
    texto = db.Column(db.String(200))

    
class RetoPartida(db.Model):
    __tablename__ = "reto_partida"
    __table_args__ = {"schema": "bingo"}
    id = db.Column(db.Integer, primary_key=True)
    partida_id = db.Column(db.Integer, db.ForeignKey("bingo.partida.id"), nullable=False)
    reto_id = db.Column(db.Integer, db.ForeignKey("bingo.reto.id"), nullable=False)
    
    reto = db.relationship("Reto", backref=db.backref("retos_partida", lazy=True))
    partida = db.relationship("Partida", backref=db.backref("retos_partida", lazy=True))
    completado = db.Column(db.Boolean, default=False)
    imagen = db.Column(db.String(200))

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuario"
    __table_args__ = {"schema": "bingo"}

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    
class Partida(db.Model):
    __tablename__ = "partida"
    __table_args__ = {"schema": "bingo"}

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("bingo.usuario.id"), nullable=False)
    bingo_id = db.Column(db.Integer, db.ForeignKey("bingo.bingo.id"), nullable=False)
    
    bingo = db.relationship("Bingo", backref=db.backref("partidas", lazy=True))
    usuario = db.relationship("Usuario", backref=db.backref("partidas", lazy=True))
    
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route("/")
def index():
    return render_template("inicio.html")

@app.route("/crear", methods=["GET", "POST"])
def crear():
    if request.method == "POST":
        nombre = request.form["nombre"]
        retos = request.form.getlist("reto")
        nuevo_bingo = Bingo(nombre=nombre, retos="\n".join(retos))
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
@login_required
def mis_bingos():
    partidas = Partida.query.filter_by(usuario_id=current_user.id).all()
    return render_template("mis-bingos.html", partidas=partidas)

@app.route("/bingo/<int:id>")
def ver_bingo(id):
    bingo = Bingo.query.get_or_404(id)
    retos = Reto.query.filter_by(bingo_id=id).all()
    return render_template("bingo.html", bingo=bingo, retos=retos)

@app.route("/jugar/<int:bingo_id>")
@login_required
def jugar(bingo_id):
    bingo = Bingo.query.get_or_404(bingo_id)
    partida = Partida(usuario_id=current_user.id, bingo_id=bingo_id)
    db.session.add(partida)
    db.session.commit()
    retos = Reto.query.filter_by(bingo_id=bingo_id).all()
    for reto in retos:
        db.session.add(RetoPartida(
            partida_id=partida.id,
            reto_id=reto.id
        ))
    db.session.commit()
    return redirect(f"/partida/{partida.id}")

@app.route("/partida/<int:partida_id>")
@login_required
def ver_partida(partida_id):
    partida = Partida.query.get_or_404(partida_id)
    if partida.usuario_id != current_user.id:
        return "No tienes permiso para ver esta partida", 403
    retos_partida = RetoPartida.query.filter_by(partida_id=partida_id).order_by(RetoPartida.id).all()
    return render_template("bingo.html", bingo=partida.bingo, retos=retos_partida)

@app.route("/subir/<int:reto_id>", methods=["POST"])
def subir_imagen(reto_id):

    file = request.files["imagen"]

    upload_result = cloudinary.uploader.upload(file)

    url = upload_result["secure_url"]

    reto = RetoPartida.query.get(reto_id)
    reto.imagen = url
    reto.completado = True

    db.session.commit()

    return redirect(f"/partida/{reto.partida_id}")

@app.route("/toggle/<int:reto_partida_id>", methods=["POST"])
@login_required
def toggle_reto(reto_partida_id):

    reto = RetoPartida.query.get_or_404(reto_partida_id)

    if reto.partida.usuario_id != current_user.id:
        return "", 403

    reto.completado = not reto.completado
    db.session.commit()

    return "", 204

@app.route("/registro", methods=["GET", "POST"])
def crear_usuario():
    if request.method == "POST":
        nombre = request.form["nombre"]
        if Usuario.query.filter_by(nombre=nombre).first():
            return "El nombre de usuario ya existe", 400
        nuevo_usuario = Usuario(nombre=nombre)
        db.session.add(nuevo_usuario)
        db.session.commit()
        login_user(nuevo_usuario)
        return redirect("/")
    return render_template("crear-usuario.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nombre = request.form["nombre"]
        usuario = Usuario.query.filter_by(nombre=nombre).first()
        if usuario:
            login_user(usuario)
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route("/multijugador")
@login_required
def multijugador():
    bingos= Bingo.query.all()
    return render_template("multijugador.html",bingos=bingos)

if __name__ == "__main__":
    app.run(debug=True)