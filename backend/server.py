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
    return {"id": str(user.get("id", user.get("_id"))), "name": user["name"], "email": user["email"], "role": user["role"], "relationship": user.get("relationship", "Single"), "avatar": user.get("avatar", ""), "department": user.get("department", ""), "bio": user.get("bio", ""), "headline": user.get("headline", ""), "interests": user.get("interests", [])}

def token_for(user, token_type="access"):
    lifetime = timedelta(minutes=15) if token_type == "access" else timedelta(days=7)
    return jwt.encode({"sub": str(user["id"]), "email": user["email"], "type": token_type, "exp": datetime.now(timezone.utc) + lifetime}, os.environ["JWT_SECRET"], algorithm=JWT_ALGORITHM)

def set_auth_cookies(response, user):
    response.set_cookie("access_token", token_for(user, "access"), httponly=True, samesite="lax", max_age=900, path="/")
    response.set_cookie("refresh_token", token_for(user, "refresh"), httponly=True, samesite="lax", max_age=604800, path="/")

async def current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token and request.headers.get("Authorization", "").startswith("Bearer "):
        token = request.headers["Authorization"][7:]
    if not token: raise HTTPException(401, "Please sign in to continue")
    try:
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access": raise HTTPException(401, "Invalid session type")
    except HTTPException: raise
    except jwt.InvalidTokenError: raise HTTPException(401, "Your session has expired")
    user = await db.users.find_one({"id": payload["sub"]})
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

class ProfileInput(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    relationship: str = Field(default="Single", max_length=40)
    department: str = Field(default="", max_length=100)
    bio: str = Field(default="", max_length=500)
    headline: str = Field(default="", max_length=120)
    interests: List[str] = Field(default_factory=list, max_length=8)
    avatar: str = ""

class RoomPostInput(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    parent_id: Optional[str] = None

class CommentInput(BaseModel):
    body: str = Field(min_length=1, max_length=800)

class StoryInput(BaseModel):
    image: str
    caption: Optional[str] = ""

class StoryReactInput(BaseModel):
    emoji: str

class ForgotPasswordInput(BaseModel):
    email: EmailStr

class ResetPasswordInput(BaseModel):
    token: str
    password: str = Field(min_length=6)

@api.get("/")
async def root(): return {"message": "NSEC Academia Network"}

@api.post("/auth/register")
async def register(data: RegisterInput, response: Response):
    email = data.email.lower()
    if await db.users.find_one({"email": email}): raise HTTPException(409, "An account with this email already exists")
    role = data.role.lower() if data.role.lower() in {"student", "teacher", "founder"} else "student"
    user = {"id": str(uuid.uuid4()), "name": data.name, "email": email, "role": role, "relationship": "Single", "avatar": "", "password_hash": bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.users.insert_one(user)
    set_auth_cookies(response, user)
    return clean_user(user)

@api.post("/auth/login")
async def login(data: LoginInput, response: Response):
    user = await db.users.find_one({"email": data.email.lower()})
    if not user or not bcrypt.checkpw(data.password.encode(), user["password_hash"].encode()): raise HTTPException(401, "Email or password is incorrect")
    set_auth_cookies(response, user)
    return clean_user(user)

@api.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/"); response.delete_cookie("refresh_token", path="/"); return {"ok": True}

@api.get("/auth/me")
async def me(user=Depends(current_user)): return clean_user(user)

@api.post("/auth/refresh")
async def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token: raise HTTPException(401, "Refresh session not found")
    try: payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError: raise HTTPException(401, "Refresh session has expired")
    if payload.get("type") != "refresh": raise HTTPException(401, "Invalid refresh session")
    user = await db.users.find_one({"id": payload.get("sub")})
    if not user: raise HTTPException(401, "Account not found")
    response.set_cookie("access_token", token_for(user, "access"), httponly=True, samesite="lax", max_age=900, path="/")
    return {"ok": True}

@api.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordInput):
    user = await db.users.find_one({"email": data.email.lower()})
    if user:
        reset_token = uuid.uuid4().hex
        await db.password_reset_tokens.insert_one({"token": reset_token, "user_id": user["id"], "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(), "used": False})
    return {"message": "If an account exists, recovery instructions have been created."}

@api.post("/auth/reset-password")
async def reset_password(data: ResetPasswordInput):
    record = await db.password_reset_tokens.find_one({"token": data.token, "used": False})
    if not record or datetime.fromisoformat(record["expires_at"]) < datetime.now(timezone.utc): raise HTTPException(400, "This recovery link is invalid or expired")
    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    await db.users.update_one({"id": record["user_id"]}, {"$set": {"password_hash": hashed}})
    await db.password_reset_tokens.update_one({"token": data.token}, {"$set": {"used": True}})
    return {"message": "Password updated. You can now sign in."}

@api.put("/profile")
async def update_profile(data: ProfileInput, user=Depends(current_user)):
    changes = data.model_dump()
    await db.users.update_one({"id": user["id"]}, {"$set": changes})
    user.update(changes)
    return clean_user(user)

def _post_shape(post):
    post.pop("_id", None)
    post["like_count"] = len(post.get("liked_by", []))
    post["comment_count"] = post.get("comment_count", 0)
    return post

@api.get("/feed")
async def feed():
    docs = await db.posts.find({}).sort("created_at", -1).to_list(50)
    return [_post_shape(d) for d in docs]

@api.post("/feed")
async def create_post(data: PostInput, user=Depends(current_user)):
    post = {"id": str(uuid.uuid4()), "author_id": user["id"], "author": user["name"], "role": user["role"], "avatar": user.get("avatar", ""), "body": data.body, "image": data.image or "", "liked_by": [], "comment_count": 0, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.posts.insert_one(post); return _post_shape(post)

@api.post("/feed/{post_id}/like")
async def like_post(post_id: str, user=Depends(current_user)):
    post = await db.posts.find_one({"id": post_id})
    if not post: raise HTTPException(404, "Post not found")
    liked = user["id"] in post.get("liked_by", [])
    op = {"$pull": {"liked_by": user["id"]}} if liked else {"$addToSet": {"liked_by": user["id"]}}
    await db.posts.update_one({"id": post_id}, op)
    updated = await db.posts.find_one({"id": post_id})
    return _post_shape(updated)

@api.get("/feed/{post_id}/comments")
async def list_comments(post_id: str):
    comments = await db.comments.find({"post_id": post_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    return comments

@api.post("/feed/{post_id}/comments")
async def create_comment(post_id: str, data: CommentInput, user=Depends(current_user)):
    post = await db.posts.find_one({"id": post_id})
    if not post: raise HTTPException(404, "Post not found")
    comment = {"id": str(uuid.uuid4()), "post_id": post_id, "author_id": user["id"], "author": user["name"], "role": user["role"], "avatar": user.get("avatar", ""), "body": data.body, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.comments.insert_one(comment); comment.pop("_id", None)
    await db.posts.update_one({"id": post_id}, {"$inc": {"comment_count": 1}})
    return comment

@api.get("/stories")
async def list_stories(request: Request):
    try: user = await current_user(request)
    except HTTPException: user = None
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    stories = await db.stories.find({"created_at": {"$gte": cutoff}}, {"_id": 0}).sort("created_at", -1).to_list(200)
    grouped = {}
    for s in stories:
        s["view_count"] = len(s.get("viewers", []))
        if not user or s["author_id"] != user["id"]:
            s.pop("viewers", None)
        aid = s["author_id"]
        if aid not in grouped:
            grouped[aid] = {"author_id": aid, "author": s["author"], "avatar": s.get("avatar", ""), "role": s.get("role", "student"), "stories": []}
        grouped[aid]["stories"].append(s)
    return list(grouped.values())

@api.post("/stories")
async def create_story(data: StoryInput, user=Depends(current_user)):
    story = {"id": str(uuid.uuid4()), "author_id": user["id"], "author": user["name"], "role": user["role"], "avatar": user.get("avatar", ""), "image": data.image, "caption": data.caption or "", "reactions": {}, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.stories.insert_one(story); story.pop("_id", None)
    return story

STORY_EMOJIS = {"❤️", "🔥", "👏", "😂", "😮"}

@api.post("/stories/{story_id}/view")
async def view_story(story_id: str, user=Depends(current_user)):
    story = await db.stories.find_one({"id": story_id}, {"_id": 0})
    if not story: raise HTTPException(404, "Story not found")
    if story["author_id"] != user["id"] and not any(v["id"] == user["id"] for v in story.get("viewers", [])):
        viewer = {"id": user["id"], "name": user["name"], "avatar": user.get("avatar", ""), "role": user["role"], "viewed_at": datetime.now(timezone.utc).isoformat()}
        await db.stories.update_one({"id": story_id}, {"$push": {"viewers": viewer}})
    updated = await db.stories.find_one({"id": story_id}, {"_id": 0})
    return {"id": story_id, "view_count": len(updated.get("viewers", []))}

@api.post("/stories/{story_id}/react")
async def react_story(story_id: str, data: StoryReactInput, user=Depends(current_user)):
    if data.emoji not in STORY_EMOJIS: raise HTTPException(400, "Unsupported reaction")
    story = await db.stories.find_one({"id": story_id}, {"_id": 0})
    if not story: raise HTTPException(404, "Story not found")
    reactions = story.get("reactions", {})
    prev = next((e for e, ids in reactions.items() if user["id"] in ids), None)
    if prev:
        reactions[prev] = [i for i in reactions[prev] if i != user["id"]]
        if not reactions[prev]: reactions.pop(prev)
    if prev != data.emoji:
        reactions.setdefault(data.emoji, []).append(user["id"])
    await db.stories.update_one({"id": story_id}, {"$set": {"reactions": reactions}})
    return {"id": story_id, "reactions": reactions}

@api.get("/directory/trending")
async def trending_directory():
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    counts = {}
    for coll in (db.posts, db.comments, db.stories):
        docs = await coll.find({"created_at": {"$gte": cutoff}}, {"_id": 0, "author_id": 1}).to_list(1000)
        for d in docs:
            aid = d.get("author_id")
            if aid: counts[aid] = counts.get(aid, 0) + 1
    top = sorted(counts.items(), key=lambda x: -x[1])[:8]
    result = []
    for aid, score in top:
        u = await db.users.find_one({"id": aid}, {"password_hash": 0})
        if u: result.append({**clean_user(u), "activity": score})
    return result

@api.get("/rooms")
async def rooms():
    docs = await db.rooms.find({}, {"_id": 0}).to_list(50)
    if not docs: return [{"id":"academics","title":"Academics & Research","description":"Ideas, papers, labs, and learning resources","members":128},{"id":"placements","title":"Placements & Careers","description":"Internships, interviews, and opportunities","members":96},{"id":"campus","title":"Campus Life","description":"Clubs, hostel life, events, and everyday NSEC","members":74}]
    return docs

@api.post("/rooms")
async def create_room(data: RoomInput, user=Depends(current_user)):
    room = {"id": str(uuid.uuid4()), "title": data.title, "description": data.description, "members": 1, "created_by": user["name"]}
    await db.rooms.insert_one(room); room.pop("_id", None); return room

@api.get("/rooms/{room_id}/posts")
async def room_posts(room_id: str):
    posts = await db.room_posts.find({"room_id": room_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    return posts

@api.post("/rooms/{room_id}/posts")
async def create_room_post(room_id: str, data: RoomPostInput, user=Depends(current_user)):
    post = {"id": str(uuid.uuid4()), "room_id": room_id, "author": user["name"], "role": user["role"], "body": data.body, "parent_id": data.parent_id, "reactions": {"thoughtful": 0, "useful": 0}, "reacted_by": [], "created_at": datetime.now(timezone.utc).isoformat()}
    await db.room_posts.insert_one(post); post.pop("_id", None); return post

@api.post("/rooms/{room_id}/posts/{post_id}/react")
async def react_to_room_post(room_id: str, post_id: str, user=Depends(current_user)):
    post = await db.room_posts.find_one({"id": post_id, "room_id": room_id}, {"_id": 0})
    if not post: raise HTTPException(404, "Discussion post not found")
    reacted = user["id"] in post.get("reacted_by", [])
    if reacted:
        await db.room_posts.update_one({"id": post_id}, {"$pull": {"reacted_by": user["id"]}, "$inc": {"reactions.thoughtful": -1}})
    else:
        await db.room_posts.update_one({"id": post_id}, {"$addToSet": {"reacted_by": user["id"]}, "$inc": {"reactions.thoughtful": 1}})
    updated = await db.room_posts.find_one({"id": post_id}, {"_id": 0})
    return updated

@api.get("/discover")
async def discover(q: str = ""):
    term = q.strip()
    people_query = {"$or": [{"name": {"$regex": term, "$options": "i"}}, {"department": {"$regex": term, "$options": "i"}}, {"headline": {"$regex": term, "$options": "i"}}]} if term else {}
    people = [clean_user(x) for x in await db.users.find(people_query, {"password_hash": 0}).to_list(50)]
    rooms_list = await rooms()
    if term: rooms_list = [r for r in rooms_list if term.lower() in (r.get("title", "") + r.get("description", "")).lower()]
    updates = await db.teacher_updates.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    if term: updates = [u for u in updates if term.lower() in (u.get("topic", "") + u.get("details", "")).lower()]
    return {"people": people, "rooms": rooms_list, "updates": updates}

@api.get("/teacher-updates")
async def teacher_updates(): return await db.teacher_updates.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)

@api.post("/teacher-updates")
async def create_teacher_update(data: TeacherInput, user=Depends(current_user)):
    if user["role"] not in {"teacher", "founder"}: raise HTTPException(403, "Only teachers can publish teaching updates")
    update = {"id": str(uuid.uuid4()), "teacher": user["name"], "topic": data.topic, "details": data.details, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.teacher_updates.insert_one(update); update.pop("_id", None); return update

app.include_router(api)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def setup():
    await db.users.create_index("email", unique=True)
    await db.password_reset_tokens.create_index("expires_at")
    await db.stories.create_index("created_at")
    if not await db.users.find_one({"email": "admin@nsec.edu"}):
        password = os.environ.get("ADMIN_PASSWORD", "nsec-admin-2026")
        await db.users.insert_one({"id": str(uuid.uuid4()), "name":"NSEC Admin", "email":"admin@nsec.edu", "role":"founder", "relationship":"NSEC community", "avatar":"", "password_hash":bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()})

@app.on_event("shutdown")
async def shutdown(): client.close()
