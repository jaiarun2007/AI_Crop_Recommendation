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
