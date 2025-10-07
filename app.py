from flask import Flask, request, session, redirect, url_for, render_template_string, Response
import os

app = Flask(__name__)
app.secret_key = os.environ.get("TEMU_SECRET_KEY", "temu2025")

DISTRICTS = ["Хан-Уул", "Баянзүрх", "Сонгинохайрхан", "Баянгол", "Чингэлтэй"]
USERS = {
    "admin@ubcab.mn": {"password":"temu2025","role":"admin","name":"Админ"},
    "99112233": {"password":"1234","role":"driver","name":"Энхбат","district":"Хан-Уул"}
}

@app.route("/health")
def health(): 
    return {"ok": True}

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    role = session["role"]
    if role=="admin":
        return f"<h2>Админ хэсэг</h2><p>Дүүрэгүүд: {DISTRICTS}</p>"
    return f"<h2>Жолооч хэсэг</h2><p>Таны дүүрэг: {session.get('district')}</p>"

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u = request.form.get("u","").strip()
        p = request.form.get("p","").strip()
        if u in USERS and USERS[u]["password"]==p:
            session["user"]=u
            session["role"]=USERS[u]["role"]
            session["district"]=USERS[u].get("district","")
            return redirect("/")
        return "<h3>Нууц үг буруу</h3>"
    return """<form method=post>
    <input name=u placeholder='И-мэйл / утас'><br>
    <input name=p type=password placeholder='Нууц үг'><br>
    <button>Нэвтрэх</button>
    </form>"""

if __name__=="__main__":
    app.run(host="0.0.0.0", port=8000)
