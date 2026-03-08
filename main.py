from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import mysql.connector
import uvicorn

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="986892")
templates = Jinja2Templates(directory="templates")

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Paarthkumar@986892",
    database="result_dashboard"
)
cursor = db.cursor()

# ---------------- STUDENT LOGIN ----------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/login")
def login(request: Request, student_id: str = Form(...), password: str = Form(...)):
    query = "SELECT * FROM students WHERE student_id = %s AND password = %s"
    cursor.execute(query, (student_id, password))
    student = cursor.fetchone()

    if student:
        request.session["student_id"] = student_id
        request.session["role"] = "student"
        return RedirectResponse(f"/dashboard/{student_id}", status_code=302)
    else:
        return HTMLResponse("Invalid ID or Password")


@app.get("/admin", response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})


@app.post("/login")
def login(student_id: str = Form(...), password: str = Form(...)):
    query = "SELECT * FROM students WHERE student_id = %s AND password = %s"
    cursor.execute(query, (student_id, password))
    student = cursor.fetchone()

    if student:
        return RedirectResponse(f"/dashboard/{student_id}", status_code=302)
    else:
        return HTMLResponse("Invalid ID or Password")


@app.get("/dashboard/{student_id}", response_class=HTMLResponse)
def dashboard(request: Request, student_id: str):
    session_student_id = request.session.get("student_id")
    role = request.session.get("role")

    if not session_student_id or role != "student":
        return RedirectResponse("/student", status_code=302)

    if session_student_id != student_id:
        return HTMLResponse("Access denied")

    query = "SELECT * FROM students WHERE student_id = %s"
    cursor.execute(query, (student_id,))
    student = cursor.fetchone()

    if not student:
        return HTMLResponse("Student not found")

    def get_status(mark):
        if mark >= 80:
            return "Strong"
        elif mark >= 60:
            return "Average"
        else:
            return "Weak"

    data = {
        "name": student[1],
        "student_id": student[0],
        "cpp": student[3],
        "java": student[4],
        "aptitude": student[5],
        "dsa": student[6],
        "cpp_status": get_status(student[3]),
        "java_status": get_status(student[4]),
        "aptitude_status": get_status(student[5]),
        "dsa_status": get_status(student[6])
    }

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "data": data}
    )

# ---------------- ADMIN LOGIN ----------------

@app.get("/admin", response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})


@app.post("/admin/login")
def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    query = "SELECT * FROM admins WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    admin = cursor.fetchone()

    if admin:
        request.session["admin_username"] = username
        request.session["role"] = "admin"
        return RedirectResponse("/admin/dashboard", status_code=302)
    else:
        return HTMLResponse("Invalid admin credentials")


@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    admin_username = request.session.get("admin_username")
    role = request.session.get("role")

    if not admin_username or role != "admin":
        return RedirectResponse("/admin", status_code=302)

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request, "message": "", "msg_type": ""}
    )

# ---------------- FILE UPLOAD PLACEHOLDER ----------------
@app.post("/admin/upload", response_class=HTMLResponse)
def upload_file(request: Request, file: UploadFile = File(...)):
    admin_username = request.session.get("admin_username")
    role = request.session.get("role")

    if not admin_username or role != "admin":
        return RedirectResponse("/admin", status_code=302)

    import pandas as pd
    import os

@app.post("/admin/upload", response_class=HTMLResponse)
def upload_file(request: Request, file: UploadFile = File(...)):
    import pandas as pd
    import os

    filename = file.filename.lower()

    try:
        temp_path = f"temp_{file.filename}"

        with open(temp_path, "wb") as buffer:
            buffer.write(file.file.read())

        if filename.endswith(".csv"):
            df = pd.read_csv(temp_path)
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(temp_path)
        else:
            os.remove(temp_path)
            return templates.TemplateResponse(
                "admin_dashboard.html",
                {
                    "request": request,
                    "message": "Only CSV and XLSX files are allowed.",
                    "msg_type": "error"
                }
            )

        required_columns = ["student_id", "name", "password", "cpp", "java", "aptitude", "dsa"]

        for col in required_columns:
            if col not in df.columns:
                os.remove(temp_path)
                return templates.TemplateResponse(
                    "admin_dashboard.html",
                    {
                        "request": request,
                        "message": f"Missing required column: {col}",
                        "msg_type": "error"
                    }
                )

        inserted_count = 0
        updated_count = 0

        for _, row in df.iterrows():
            check_query = "SELECT * FROM students WHERE student_id = %s"
            cursor.execute(check_query, (str(row["student_id"]),))
            existing_student = cursor.fetchone()

            if existing_student:
                update_query = """
                    UPDATE students
                    SET name = %s, password = %s, cpp = %s, java = %s, aptitude = %s, dsa = %s
                    WHERE student_id = %s
                """
                cursor.execute(update_query, (
                    str(row["name"]),
                    str(row["password"]),
                    int(row["cpp"]),
                    int(row["java"]),
                    int(row["aptitude"]),
                    int(row["dsa"]),
                    str(row["student_id"])
                ))
                updated_count += 1
            else:
                insert_query = """
                    INSERT INTO students (student_id, name, password, cpp, java, aptitude, dsa)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    str(row["student_id"]),
                    str(row["name"]),
                    str(row["password"]),
                    int(row["cpp"]),
                    int(row["java"]),
                    int(row["aptitude"]),
                    int(row["dsa"])
                ))
                inserted_count += 1

        db.commit()
        os.remove(temp_path)

        return templates.TemplateResponse(
            "admin_dashboard.html",
            {
                "request": request,
                "message": f"Upload successful. Inserted: {inserted_count}, Updated: {updated_count}.",
                "msg_type": "success"
            }
        )

    except Exception as e:
        return templates.TemplateResponse(
            "admin_dashboard.html",
            {
                "request": request,
                "message": f"Error while uploading file: {str(e)}",
                "msg_type": "error"
            }
        )   
    

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

if __name__ == "__main__": 
    uvicorn.run("main:app", reload=True)