from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psycopg2
import bcrypt

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db_connection():
    return psycopg2.connect(
        dbname="auth_db",
        user="user",
        password="password",
        host="db",
        port="5432"
    )

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse("register.html", {"request": request, "error": error})

@app.post("/register")
def register_user(username: str = Form(...), password: str = Form(...), email: str = Form(...)):
    if username.lower() == "admin":#запрет регистрации пользователя с именем admin
        return RedirectResponse("/register?error=Cannot+register+admin+user", status_code=303)

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()#хеширование пароля

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
            (username, hashed_password, email)
        )
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()
        return RedirectResponse("/register?error=User+already+exists", status_code=303)
    finally:
        cur.close()
        conn.close()
    return RedirectResponse("/", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@app.post("/login")
def login_user(username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT username, password FROM users WHERE username = %s",
        (username,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
        if username == "admin":
            return RedirectResponse("/admin", status_code=303)
        else:
            return RedirectResponse("/", status_code=303)
    else:
        return RedirectResponse("/login?error=Invalid+credentials", status_code=303)

@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return templates.TemplateResponse("admin.html", {"request": request, "users": users})
