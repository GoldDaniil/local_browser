from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psycopg2
import os

app = FastAPI()
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

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse("register.html", {"request": request, "error": error})

@app.post("/register")
def register_user(username: str = Form(...), password: str = Form(...), email: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
            (username, password, email)
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
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login_user(username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE username = %s AND password = %s",
        (username, password)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        return RedirectResponse("/", status_code=303)
    else:
        raise HTTPException(status_code=400, detail="Invalid credentials")
