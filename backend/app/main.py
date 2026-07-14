from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import crop, disease, fertilizer, weather, yield_

app = FastAPI(
    title="AI Crop Recommendation & Climate-Adaptive Farming Assistant",
    description=(
        "Demo API: crop recommendation (ML), leaf disease screening (CV heuristic), "
        "yield prediction (ML), weather intelligence (live Open-Meteo forecasts + "
        "rule-based agro-alerts), and a fertilizer N-P-K balancing engine."
    ),
    version="0.4.0",
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


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
