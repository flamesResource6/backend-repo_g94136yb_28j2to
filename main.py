import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from database import db, create_document, get_documents
from schemas import User, BlogPost, ContactMessage

app = FastAPI(title="SaaS Starter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "SaaS Starter Backend running"}

# Auth: minimal email signup (demo; in real apps, use proper auth)
class SignupPayload(BaseModel):
    name: str
    email: EmailStr
    password: str

@app.post("/api/auth/signup")
def signup(payload: SignupPayload):
    # Basic check if user exists
    try:
        existing = list(db["user"].find({"email": payload.email}).limit(1)) if db else []
        if existing:
            raise HTTPException(status_code=409, detail="User already exists")

        # Very simplified hashing placeholder (for demo only)
        # In production, use passlib/bcrypt and never store plain passwords
        password_hash = f"hashed::{payload.password}"
        user = User(name=payload.name, email=payload.email, password_hash=password_hash)
        user_id = create_document("user", user)
        return {"ok": True, "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Blog: list posts (seed a few if collection empty)
@app.get("/api/blog")
def list_blog():
    try:
        posts = get_documents("blogpost") if db else []
        if not posts:
            # Seed minimal posts
            seed = [
                {
                    "title": "Launching our pastel fintech SaaS",
                    "slug": "launching-pastel-fintech-saas",
                    "excerpt": "A clean, minimalist platform for modern teams.",
                    "content": "Welcome to our new SaaS built with a pastel vibe.",
                    "tags": ["launch", "product"],
                    "author": "Team",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
                {
                    "title": "Designing with softness and clarity",
                    "slug": "designing-with-softness",
                    "excerpt": "Why soft pastels improve readability and focus.",
                    "content": "Soft palettes can reduce cognitive load for users.",
                    "tags": ["design", "ui"],
                    "author": "Design",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            ]
            if db:
                db["blogpost"].insert_many(seed)
                posts = get_documents("blogpost")
        # Normalize ObjectId
        for p in posts:
            if "_id" in p:
                p["id"] = str(p.pop("_id"))
        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Contact: submit message
class ContactPayload(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

@app.post("/api/contact")
def contact(payload: ContactPayload):
    try:
        doc = ContactMessage(**payload.model_dump())
        msg_id = create_document("contactmessage", doc)
        return {"ok": True, "message_id": msg_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = getattr(db, 'name', "✅ Connected")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
