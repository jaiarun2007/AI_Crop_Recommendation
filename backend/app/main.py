from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401 - registers models on Base before create_all
from app.database import Base, engine
from app.routers import assistant, auth, crop, disease, fertilizer, irrigation, weather, yield_

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Crop Recommendation & Climate-Adaptive Farming Assistant",
    description=(
        "Demo API: crop recommendation (ML), leaf disease screening (CV heuristic), "
        "yield prediction (ML), weather intelligence (live Open-Meteo forecasts + "
        "rule-based agro-alerts), a fertilizer N-P-K balancing engine, an irrigation "
        "scheduler (FAO-56 crop-coefficient method), a RAG assistant over the project's "
        "own documents, and JWT authentication."
    ),
    version="0.7.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crop.router)
app.include_router(disease.router)
app.include_router(yield_.router)
app.include_router(weather.router)
app.include_router(fertilizer.router)
app.include_router(irrigation.router)
app.include_router(assistant.router)
app.include_router(auth.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
