import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.logger import logger
from api.routers import auth, documents, chat 

app = FastAPI(title="FinAI Enterprise Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)