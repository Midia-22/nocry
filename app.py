from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for
)
import jwt
import json
import time
import datetime
import requests
from api import * 

app = Flask(__name__)

# ============================
# CONFIGURAÇÕES
# ============================
SECRET = "Midia22"

# Carregar módulos na inicialização
with open(r"dbs\modules.json", 'r', encoding='utf-8') as f:
    modules = json.load(f)


# ============================
# FUNÇÕES AUXILIARES
# ============================

def log(username: str, password: str) -> bool:
    """Valida usuário e senha comparando com users.json."""
    with open(r"dbs\users.json", 'r', encoding="utf-8") as f:
        users = json.load(f)

    agora = int(time.time())  # Timestamp atual

    for entry in users:
        if (
            entry['username'].lower() == username.lower() and
            entry['password'] == password
        ):
            return entry['validade'] > agora

    return False


def gerar_jwt(username: str) -> str:
    """Gera um token JWT válido por 30 minutos."""
    exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    payload = {
        "user": username,
        "exp": exp
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')


def validar_jwt(token: str):
    """Valida token JWT e retorna payload, caso contrário None."""
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except Exception:
        return None


# ============================
# ROTAS: API
# ============================

@app.route("/modules", methods=["GET"])
def api_modules():
    return jsonify(modules)


@app.route("/entrar", methods=["POST"])
def api_entrar():
    username = request.form.get("username")
    password = request.form.get("password")

    if log(username, password):
        token = gerar_jwt(username)
        return jsonify({"ok": True, "token": token})

    return jsonify({"ok": False, "token": None})


@app.route("/verificar_token", methods=["POST"])
def api_verificar_token():
    token = request.json.get("token")
    payload = validar_jwt(token)

    if payload:
        return jsonify({"ok": True, "user": payload["user"]})

    return jsonify({"ok": False})


# ============================
# ROTAS: PÁGINAS HTML
# ============================

@app.route("/")
@app.route("/consultas")
def consultas():
    return render_template("consultas.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/modulo")
def modulo_base():
    return render_template("modulo.html")


@app.route("/modulo/<id>")
def modulo_com_ancora(id):
    """Carrega modulo.html e adiciona âncora #id corretamente."""
    return redirect(url_for("modulo_base") + f"#{id}")



@app.route("/api/<id>/", methods=["POST"])
def consulta(id):
    form = request.get_json(silent=True) or {}
    if not form.get("token"):
        return jsonify({"ok": False, "error": "sessão invalida"})
    else:
        token = form.get("token")
        payload = validar_jwt(token)
        if not payload:
            return jsonify({"ok": False, "error": "sessão invalida"})
    form.pop("token", None)


    # Definir "valor" dependendo do suporte
    if id in dict_support:
        valor = form
    else:
        values = sum(1 for k in form if form[k])

        if values > 1:
            valor = form

        elif values == 1:
            # pega o único valor não vazio
            for key in form:
                if form[key]:
                    valor = form[key]
                    break

        else:
            return jsonify({"ok": False, "msg": "parametros invalido"}), 404

    # Verificar base
    entry = entrys.get(id)
    if not entry:
        return jsonify({"ok": False, "msg": f"base {id} não encontrada"}), 404

    db_key, cls = entry

    # Executa consulta
    result = consult_generic(cls, db_key, valor)

    # Respostas
    if result is False:
        return jsonify({"ok": False, "msg": "erro interno"}), 400

    elif result is None:
        return jsonify({"ok": True, "msg": "sem registros"}), 200

    return jsonify({"ok": True, "data": result}), 200

# ============================
# EXECUÇÃO
# ============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)


# ============================
# EXECUÇÃO
# ============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
