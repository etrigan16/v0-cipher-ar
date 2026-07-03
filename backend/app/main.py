from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, asm, phishing
from app.database import init_db

app = FastAPI(title="Aukalabs API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://aukalabs.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(asm.router)
app.include_router(phishing.router)


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}
