import os
from datetime import datetime
from iterativeworkflow import get_graph, run_agent
from pydantic import BaseModel
from auth_models import UserSignup, UserLogin
from auth_utils import hash_password, verify_password, create_access_token, decode_access_token
from database import users_collection, history_collection

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow frontend URL from env (set on Render), plus local dev URLs
frontend_url = os.getenv("FRONTEND_URL", "")
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://postjun.netlify.app", # Explicitly allow your Netlify URL
]
if frontend_url:
    for url in frontend_url.split(","):
        cleaned = url.strip().rstrip("/")
        if cleaned:
            allowed_origins.append(cleaned)
            allowed_origins.append(f"{cleaned}/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = get_graph()

class InputModel(BaseModel):
    raw_input: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload["sub"]

@app.post("/signup")
def register(user: UserSignup):
    existing = users_collection.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_pw = hash_password(user.password)

    users_collection.insert_one({
        "username": user.username,
        "email": user.email,
        "password": hashed_pw
    })

    return {"message": "User created successfully"}

@app.post("/login")
def login(user: UserLogin):
    db_user = users_collection.find_one({"username": user.username})
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": db_user["username"]})

    return {"access_token": token, "token_type": "bearer"}

@app.post("/chat")
def chat(input_model: InputModel, current_user: str = Depends(get_current_user)):
    generated_post = run_agent(graph, input_model.raw_input)
    history_collection.insert_one({
        "username": current_user,
        "topic": input_model.raw_input,
        "generated_post": generated_post,
        "created_at": datetime.utcnow()
    })
    return {"post": generated_post}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/history")
def get_history(current_user: str = Depends(get_current_user)):
    user_history = list(history_collection.find(
        {"username": current_user},
        {"_id": 0}
    ).sort("created_at", -1))
    return {"history": user_history}