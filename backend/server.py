from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from pathlib import Path
import os, bcrypt, jwt, uuid

ROOT_DIR = Path(__file__).parent
client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
app = FastAPI(title="NSEC Academia Network")
api = APIRouter(prefix="/api")
JWT_ALGORITHM = "HS256"

def clean_user(user):
    if not user: return None
    return {"id": str(user.get("_id", user.get("id"))), "name": user["name"], "email": user["email"], "role": user["role"], "relationship": user.get("relationship", "Single"), "avatar": user.get("avatar", "")}

def token_for(user):
    return jwt.encode({"sub": str(user["id"]), "exp": datetime.now(timezone.utc) + timedelta(hours=12)}, os.environ["JWT_SECRET"], algorithm=JWT_ALGORITHM)

async def current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token and request.headers.get("Authorization", "").startswith("Bearer "):
        token = request.headers["Authorization"][7:]
    if not token: raise HTTPException(401, "Please sign in to continue")
    try: payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError: raise HTTPException(401, "Your session has expired")
    user = await db.users.find_one({"_id": payload["sub"]})
    if not user: user = await db.users.find_one({"id": payload["sub"]})
    if not user: raise HTTPException(401, "Account not found")
    return user

class RegisterInput(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = "student"

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class PostInput(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    image: Optional[str] = ""

class RoomInput(BaseModel):
    title: str
    description: str

class TeacherInput(BaseModel):
    topic: str
    details: str

@api.get("/")
async def root(): return {"message": "NSEC Academia Network"}

@api.post("/auth/register")
async def register(data: RegisterInput, response: Response):
    email = data.email.lower()
    if await db.users.find_one({"email": email}): raise HTTPException(409, "An account with this email already exists")
    role = data.role.lower() if data.role.lower() in {"student", "teacher", "founder"} else "student"
    user = {"id": str(uuid.uuid4()), "name": data.name, "email": email, "role": role, "relationship": "Single", "avatar": "", "password_hash": bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.users.insert_one(user)
    response.set_cookie("access_token", token_for(user), httponly=True, samesite="lax", max_age=43200)
    return clean_user(user)

@api.post("/auth/login")
async def login(data: LoginInput, response: Response):
    user = await db.users.find_one({"email": data.email.lower()})
    if not user or not bcrypt.checkpw(data.password.encode(), user["password_hash"].encode()): raise HTTPException(401, "Email or password is incorrect")
    response.set_cookie("access_token", token_for(user), httponly=True, samesite="lax", max_age=43200)
    return clean_user(user)

@api.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token"); return {"ok": True}

@api.get("/auth/me")
async def me(user=Depends(current_user)): return clean_user(user)

@api.get("/feed")
async def feed():
    docs = await db.posts.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return docs

@api.post("/feed")
async def create_post(data: PostInput, user=Depends(current_user)):
    post = {"id": str(uuid.uuid4()), "author": user["name"], "role": user["role"], "avatar": user.get("avatar", ""), "body": data.body, "image": data.image or "", "likes": 0, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.posts.insert_one(post); post.pop("_id", None); return post

@api.get("/rooms")
async def rooms():
    docs = await db.rooms.find({}, {"_id": 0}).to_list(50)
    if not docs: return [{"id":"academics","title":"Academics & Research","description":"Ideas, papers, labs, and learning resources","members":128},{"id":"placements","title":"Placements & Careers","description":"Internships, interviews, and opportunities","members":96},{"id":"campus","title":"Campus Life","description":"Clubs, hostel life, events, and everyday NSEC","members":74}]
    return docs

@api.post("/rooms")
async def create_room(data: RoomInput, user=Depends(current_user)):
    room = {"id": str(uuid.uuid4()), "title": data.title, "description": data.description, "members": 1, "created_by": user["name"]}
    await db.rooms.insert_one(room); room.pop("_id", None); return room

@api.get("/teacher-updates")
async def teacher_updates(): return await db.teacher_updates.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)

@api.post("/teacher-updates")
async def create_teacher_update(data: TeacherInput, user=Depends(current_user)):
    if user["role"] not in {"teacher", "founder"}: raise HTTPException(403, "Only teachers can publish teaching updates")
    update = {"id": str(uuid.uuid4()), "teacher": user["name"], "topic": data.topic, "details": data.details, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.teacher_updates.insert_one(update); update.pop("_id", None); return update

app.include_router(api)
app.add_middleware(CORSMiddleware, allow_origins=["https://nsec-community.preview.emergentagent.com", "http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def setup():
    await db.users.create_index("email", unique=True)
    if not await db.users.find_one({"email": "admin@nsec.edu"}):
        password = os.environ.get("ADMIN_PASSWORD", "nsec-admin-2026")
        await db.users.insert_one({"id": str(uuid.uuid4()), "name":"NSEC Admin", "email":"admin@nsec.edu", "role":"founder", "relationship":"NSEC community", "avatar":"", "password_hash":bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()})

@app.on_event("shutdown")
async def shutdown(): client.close()