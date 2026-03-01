from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import joblib
import uvicorn

BASE_DIR = Path(__file__).resolve().parent


def _load_artifacts():
    """Load model assets with a safe fallback so API startup does not crash."""
    artifacts = {}
    errors = []
    files = {
        "model": BASE_DIR / "model.pkl",
        "scaler": BASE_DIR / "scaler.pkl",
        "features": BASE_DIR / "features.pkl",
    }

    for name, path in files.items():
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"{path.name} is missing or empty")
            artifacts[name] = None
            continue
        try:
            artifacts[name] = joblib.load(path)
        except Exception as exc:
            errors.append(f"{path.name} failed to load: {exc}")
            artifacts[name] = None

    return artifacts["model"], artifacts["scaler"], artifacts["features"], errors


model, scaler, features, artifact_errors = _load_artifacts()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request structure
class Customer(BaseModel):
    tenure: int
    MonthlyCharges: float
    TotalCharges: float
    gender: str
    SeniorCitizen: int
    Partner: str
    Dependents: str
    PhoneService: str
    MultipleLines: str
    InternetService: str
    OnlineSecurity: str
    OnlineBackup: str
    DeviceProtection: str
    TechSupport: str
    StreamingTV: str
    StreamingMovies: str
    Contract: str
    PaperlessBilling: str
    PaymentMethod: str

@app.get("/")
def home():
    status = "ready" if not artifact_errors else "degraded"
    return {
        "message": "Customer Churn Prediction API Running",
        "status": status,
        "artifact_errors": artifact_errors,
    }

@app.post("/predict")
def predict(data: Customer):
    if model is None or scaler is None or features is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Model artifacts are missing/corrupt. Regenerate valid "
                "model.pkl, scaler.pkl, and features.pkl in backend/."
            ),
        )

    try:
        # Convert input to DataFrame
        input_df = pd.DataFrame([data.model_dump()])

        # One-hot encoding
        input_df = pd.get_dummies(input_df)

        # Add missing columns
        for col in features:
            if col not in input_df.columns:
                input_df[col] = 0

        # Ensure same column order
        input_df = input_df[features]

        # Scale and predict
        input_scaled = scaler.transform(input_df)
        prediction = model.predict(input_scaled)[0]
        probability = model.predict_proba(input_scaled)[0][1]
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Prediction failed due to invalid input or model mismatch: {exc}",
        ) from exc

    return {
        "churn_prediction": int(prediction),
        "churn_probability": round(float(probability) * 100, 2)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
