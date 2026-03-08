from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import mysql.connector
import uvicorn

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Paarthkumar@986892",
    database="result_dashboard"
)

cursor = db.cursor()

# Login Page
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# 
from fastapi import Form
from fastapi.responses import RedirectResponse, HTMLResponse

@app.post("/login")
def login(student_id: str = Form(...), password: str = Form(...)):

    query = "SELECT * FROM students WHERE student_id = %s AND password = %s"
    cursor.execute(query, (student_id, password))

    student = cursor.fetchone()

    if student:
        return RedirectResponse(f"/dashboard/{student_id}", status_code=302)
    else:
        return HTMLResponse("Invalid ID or Password")


# Dashboard Page
@app.get("/dashboard/{student_id}", response_class=HTMLResponse)
def dashboard(request: Request, student_id: str):

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
if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)