from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.logger import logger

# Import your newly created routers
from api.routers import auth, documents, chat 

app = FastAPI(title="FinAudit AI Enterprise Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Registering Routers (Now they are ACTIVE)
app.include_router(auth.router, tags=["Authentication"])
app.include_router(documents.router, tags=["Document Management"])
app.include_router(chat.router, tags=["AI Engine"])

@app.get("/")
def health_check():
    logger.info("Health check endpoint hit.")
    return {"status": "Enterprise API is running smoothly", "version": "1.0.0"}