from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/api")
def api_status():
    return {"message": "Smart College Complaint System LIVE", "docs": "/docs"}
USERS_FILE = "users.json"
COMPLAINTS_FILE = "complaints.json"

class LoginModel(BaseModel):
    email: str
    password: str

def load_json(f):
    if not os.path.exists(f):
        return []
    with open(f, "r") as file:
        try:
            return json.load(file)
        except:
            return []

def save_json(f, data):
    with open(f, "w") as file:
        json.dump(data, file, indent=2)

@app.post("/login")
def login(data: LoginModel):
    return {"msg": "Login success", "name": data.email}

@app.post("/complaints")
def add_complaint(c: dict):
    complaints = load_json(COMPLAINTS_FILE)
    c["status"] = c.get("status") or "Pending"
    c["handled_by"] = c.get("handled_by") or "-"
    c["admin_remarks"] = c.get("admin_remarks") or "No remarks"
    c["room_no"] = c.get("room_no") or c.get("room") or "-"
    c["pin_no"] = c.get("pin_no") or c.get("pin") or c.get("roll_no") or "-"
    complaints.append(c)
    save_json(COMPLAINTS_FILE, complaints)
    return {"msg": "Complaint added"}

@app.get("/complaints")
def get_all_complaints():
    data = load_json(COMPLAINTS_FILE)
    # id leni complaints ki id add chesthunnam
    for i, c in enumerate(data):
        if "id" not in c or c["id"] is None:
            c["id"] = i
    return data

@app.get("/my_complaints/{email}")
def get_my_complaints(email: str):
    all_c = load_json(COMPLAINTS_FILE)
    return [x for x in all_c if x.get('email') == email]

@app.put("/complaints/{idx}")
def update_status(idx: int, data: dict):
    complaints = load_json(COMPLAINTS_FILE)
    # remarks ni anni rakalu ga save chey
    r = data.get("remarks") or data.get("admin_remarks") or data.get("adminRemarks") or ""
    if r:
        data["remarks"] = r
        data["admin_remarks"] = r
        data["adminRemarks"] = r
        data["admin_remark"] = r
    
    updated = False
    for c in complaints:
        if str(c.get("id")) == str(idx):
            c.update(data)
            updated = True
            break
    if not updated:
        try:
            if 0 <= int(idx) < len(complaints):
                complaints[int(idx)].update(data)
                updated = True
        except:
            pass
            
    if updated:
        save_json(COMPLAINTS_FILE, complaints)
        print(f"SAVED: {data}")
        return {"message": "updated"}
    return {"error": "Not found"}
    # Frontend LIVE cheyadaniki
app.mount("/", StaticFiles(directory=".", html=True), name="frontend")
