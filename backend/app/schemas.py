from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SoilClimateInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "N": 90,
                "P": 42,
                "K": 43,
                "temperature": 20.9,
                "humidity": 82.0,
                "ph": 6.5,
                "rainfall": 203.0,
            }
        }
    )

    N: float = Field(..., ge=0, le=200, description="Nitrogen content in soil (kg/ha)")
    P: float = Field(..., ge=0, le=200, description="Phosphorus content in soil (kg/ha)")
    K: float = Field(..., ge=0, le=250, description="Potassium content in soil (kg/ha)")
    temperature: float = Field(..., ge=-10, le=60, description="Temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity in %")
    ph: float = Field(..., ge=0, le=14, description="Soil pH")
    rainfall: float = Field(..., ge=0, le=1000, description="Rainfall in mm")


class CropPrediction(BaseModel):
    crop: str
    confidence: float


class CropRecommendationResponse(BaseModel):
    top_recommendation: str
    confidence: float
    alternatives: list[CropPrediction]
    model_used: str


class DiseaseDetectionResponse(BaseModel):
    status: str
    severity_percent: float
    confidence: float
    message: str
    method: str


class YieldPredictionInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "Area": "India",
                "Item": "Rice, paddy",
                "Year": 2013,
                "average_rain_fall_mm_per_year": 1083.0,
                "pesticides_tonnes": 46765.0,
                "avg_temp": 24.5,
            }
        }
    )

    Area: str = Field(..., description="Country/region name (e.g. 'India')")
    Item: str = Field(..., description="Crop name as used in FAO data (e.g. 'Rice, paddy')")
    Year: int = Field(..., ge=1900, le=2100)
    average_rain_fall_mm_per_year: float = Field(..., ge=0, le=10000)
    pesticides_tonnes: float = Field(..., ge=0)
    avg_temp: float = Field(..., ge=-30, le=60)


class YieldPredictionResponse(BaseModel):
    predicted_yield_kg_per_ha: float
    predicted_yield_tonnes_per_ha: float
    model_used: str
    model_r2: float
    warnings: list[str]


# --- Weather Intelligence ---


class LocationInfo(BaseModel):
    name: str
    country: str | None = None
    latitude: float
    longitude: float


class DailyForecast(BaseModel):
    date: str
    temp_max_c: float
    temp_min_c: float
    precipitation_mm: float
    precipitation_probability_percent: float | None = None
    humidity_percent: float | None = None
    wind_speed_max_kmh: float
    reference_et0_mm: float | None = Field(
        None, description="FAO reference evapotranspiration (ET0), used by the irrigation engine"
    )


class WeatherAlert(BaseModel):
    date: str
    type: str
    severity: str
    message: str


class WeatherForecastResponse(BaseModel):
    location: LocationInfo
    timezone: str | None = None
    daily: list[DailyForecast]


class WeatherAlertsResponse(BaseModel):
    location: LocationInfo
    alerts: list[WeatherAlert]


# --- Fertilizer Recommendation Engine ---


class FertilizerRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"crop": "rice", "N": 40, "P": 20, "K": 15, "ph": 6.0}
        }
    )

    crop: str = Field(..., description="Crop name, e.g. 'rice' (see /api/fertilizer/known-crops)")
    N: float = Field(..., ge=0, le=300, description="Current soil Nitrogen (kg/ha)")
    P: float = Field(..., ge=0, le=300, description="Current soil Phosphorus (kg/ha)")
    K: float = Field(..., ge=0, le=300, description="Current soil Potassium (kg/ha)")
    ph: float = Field(..., ge=0, le=14, description="Current soil pH")


class NutrientAdvice(BaseModel):
    nutrient: str
    status: str
    delta_kg_ha: float
    recommended_product: str | None = None
    recommended_dose_kg_ha: float | None = None
    note: str | None = None


class PHAdvice(BaseModel):
    status: str
    message: str


class FertilizerResponse(BaseModel):
    crop: str
    ideal_reference: dict
    nutrients: list[NutrientAdvice]
    ph_advice: PHAdvice
    disclaimer: str


# --- Irrigation Recommendation Engine ---


class IrrigationRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "crop": "rice",
                "growth_stage": "mid_season",
                "location": "Coimbatore",
                "days": 7,
                "field_size_ha": 1.0,
            }
        }
    )

    crop: str = Field(..., description="Crop name (see /api/irrigation/known-crops)")
    growth_stage: str = Field(
        ..., description="One of: initial, development, mid_season, late_season"
    )
    location: str | None = Field(None, description="Place name, e.g. 'Coimbatore'")
    lat: float | None = None
    lon: float | None = None
    days: int = Field(7, ge=1, le=16)
    field_size_ha: float = Field(1.0, gt=0, le=10000)


class IrrigationDayPlan(BaseModel):
    date: str
    reference_et0_mm: float
    crop_coefficient: float
    crop_water_demand_mm: float
    rainfall_mm: float
    irrigation_needed_mm: float
    irrigation_needed_liters: float
    action: str


class IrrigationResponse(BaseModel):
    crop: str
    growth_stage: str
    crop_coefficient: float
    field_size_ha: float
    daily_plan: list[IrrigationDayPlan]
    total_irrigation_mm: float
    total_irrigation_liters: float
    method: str
    disclaimer: str
    location: LocationInfo


# --- AI RAG Assistant ---


class AssistantQueryRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"question": "What model is used for disease detection?", "top_k": 3}
        }
    )

    question: str = Field(..., min_length=3, max_length=500)
    top_k: int = Field(3, ge=1, le=10)


class AssistantSource(BaseModel):
    document: str
    heading: str
    text: str
    score: float


class AssistantQueryResponse(BaseModel):
    answer: str
    mode: str
    sources: list[AssistantSource]


# --- Authentication ---


class UserRegisterRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "farmer@example.com",
                "password": "a-strong-password",
                "full_name": "Example Farmer",
            }
        }
    )

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    full_name: str | None = Field(None, max_length=200)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=72)


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
