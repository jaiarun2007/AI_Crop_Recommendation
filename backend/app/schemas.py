from pydantic import BaseModel, ConfigDict, Field


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
