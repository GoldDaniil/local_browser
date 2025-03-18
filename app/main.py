from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psycopg2
import bcrypt
import subprocess
import re
from pyvis.network import Network
import os
from starlette.middleware.sessions import SessionMiddleware#добавлена поддержка сессий

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="a3f1c8d4e5f6a7b8c9d0e")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db_connection():#подключение к бд
    return psycopg2.connect(
        dbname="auth_db",
        user="user",
        password="password",
        host="db",
        port="5432"
    )

def get_network_devices():#получение устройств из сети
    result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
    devices = []
    arp_output = result.stdout

    pattern = re.compile(r'\? \((\d+\.\d+\.\d+\.\d+)\) at ((?:[\da-f]{1,2}:){5}[\da-f]{1,2}|incomplete)', re.IGNORECASE)
    for line in arp_output.splitlines():
        match = pattern.search(line)
        if match:
            ip, mac = match.groups()
            devices.append({"ip": ip, "mac": mac if mac != 'incomplete' else 'N/A'})
    return devices

def create_network_map():#cоздание и сохранение карты сети
    devices = get_network_devices()
    net = Network(height='600px', width='100%', bgcolor='#222222', font_color='white')
    net.add_node('Router', label='Router', color='red')

    for device in devices:
        label = f"IP: {device['ip']}\nMAC: {device['mac']}"
        net.add_node(device['ip'], label=label, color='blue')
        net.add_edge('Router', device['ip'])

    net.save_graph('templates/network_map.html')

@app.on_event("startup")
def startup_event():
    create_network_map()

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse("register.html", {"request": request, "error": error})

@app.post("/register")
def register_user(username: str = Form(...), password: str = Form(...), email: str = Form(...)):
    if username.lower() == "admin":
        return RedirectResponse("/register?error=Cannot+register+admin+user", status_code=303)

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()

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



# тестируем main.html
@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@app.post("/login")
def login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, email, password FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
        request.session["username"] = username
        return RedirectResponse(url="/main", status_code=303)
    else:
        return RedirectResponse(url="/login?error=Invalid+credentials", status_code=303)

@app.get("/main", response_class=HTMLResponse)
def main_page(request: Request):
    username = request.session.get("username")
    password = request.session.get("password")#получаем пароль из сессии

    if not username or not password:
        return RedirectResponse(url="/login", status_code=303)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, email FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        return templates.TemplateResponse("main.html", {
            "request": request,
            "username": user[0],
            "email": user[1],
            "password": password #передаем пароль в main.html
        })
    else:
        return RedirectResponse(url="/login", status_code=303)
# тестируем main.html

# тестируем вход для админа

@app.get("/adminlogin", response_class=HTMLResponse)
def admin_login(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse("adminlogin.html", {"request": request, "error": error})

@app.post("/adminlogin")
def admin_login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username = %s", ("admin",))  #находим админа в базе
    admin = cur.fetchone()
    cur.close()
    conn.close()

    if admin and bcrypt.checkpw(password.encode('utf-8'), admin[0].encode('utf-8')):  # сраввниваем хэшированный пароль
        request.session["admin"] = "admin"  # метка - что админ вошел
        return RedirectResponse(url="/admin", status_code=303)
    else:
        return RedirectResponse(url="/adminlogin?error=Invalid+credentials", status_code=303)

@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request):
    admin = request.session.get("admin")
    if not admin:
        return RedirectResponse(url="/adminlogin", status_code=303)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()

    return templates.TemplateResponse("admin.html", {"request": request, "users": users})


# тестируем вход для админа


@app.get("/network_map", response_class=HTMLResponse)
def network_map(request: Request):
    return templates.TemplateResponse("network_map.html", {"request": request})

@app.post("/delete_user/{user_id}")
def delete_user(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse("/admin", status_code=303)

@app.get("/edit_user/{user_id}", response_class=HTMLResponse)
def edit_user(request: Request, user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return templates.TemplateResponse("edit_user.html", {"request": request, "user": user})

@app.post("/edit_user/{user_id}")
def update_user(user_id: int, username: str = Form(...), email: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET username = %s, email = %s WHERE id = %s", (username, email, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse("/admin", status_code=303)

@app.get("/add_user", response_class=HTMLResponse)
def add_user_form(request: Request):
    return templates.TemplateResponse("add_user.html", {"request": request})

@app.post("/add_user")
def add_user(username: str = Form(...), password: str = Form(...), email: str = Form(...)):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (username, hashed_password, email))
    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse("/admin", status_code=303)