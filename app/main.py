from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import db
from app.api.routes import health, users, auth, admissions, resources, courses, contacts, payment

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await db.connect()
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        # We don't raise here strictly to allow the app to boot even if DB is down initially,
        # but in a real production env you might want it to fail fast.
    yield
    # Shutdown
    try:
        await db.disconnect()
    except Exception as e:
        pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "https://smc-trade-institute.vercel.app",
        "https://smclassesranjhi.in"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(admissions.router, prefix="/api/v1")
app.include_router(resources.router, prefix="/api/v1")
app.include_router(courses.router, prefix="/api/v1")
app.include_router(contacts.router, prefix="/api/v1")
app.include_router(payment.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Inspired Wings Publication Server"}
