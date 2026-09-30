"""
main.py — FastAPI entrypoint
Run: uvicorn backend.main:app --reload   (from project root)
 OR: cd backend && uvicorn main:app --reload
"""
import os, sys

# Make sure project root is on the path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.predict_api import predict_crop
from cnn.predict_soil import InvalidSoilImage, SoilProcessingError
from backend.history import (
    save_prediction, get_history, get_prediction_by_id, 
    delete_prediction, get_soil_types, get_stats
)

app = FastAPI(title="CropSense AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "message": "CropSense AI API is running. POST to /predict"}

# History endpoints
@app.get("/history")
def get_prediction_history(
    limit: int = 50,
    soil_type: str = None,
    search: str = None
):
    """Get prediction history with optional filtering."""
    try:
        history = get_history(limit=limit, soil_type_filter=soil_type, search=search)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")

@app.get("/history/{prediction_id}")
def get_prediction(prediction_id: str):
    """Get a specific prediction by ID."""
    prediction = get_prediction_by_id(prediction_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction

@app.delete("/history/{prediction_id}")
def delete_prediction_endpoint(prediction_id: str):
    """Delete a prediction by ID."""
    if delete_prediction(prediction_id):
        return {"message": "Prediction deleted successfully"}
    raise HTTPException(status_code=404, detail="Prediction not found")

@app.get("/history/stats")
def get_history_stats():
    """Get prediction statistics."""
    try:
        stats = get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

@app.get("/history/soil-types")
def get_soil_types_endpoint():
    """Get unique soil types from history."""
    try:
        soil_types = get_soil_types()
        return {"soil_types": soil_types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving soil types: {str(e)}")

@app.post("/predict")
async def predict(
    image: UploadFile = File(..., description="Soil image (JPG/PNG)"),
    latitude:  float  = Form(..., description="GPS latitude"),
    longitude: float  = Form(..., description="GPS longitude"),
):
    if image.content_type not in ("image/jpeg", "image/png", "image/jpg"):
        return JSONResponse(status_code=400, content={"success": False, "message": "Only JPG/PNG images are accepted."})
    try:
        image_bytes = await image.read()
        result = await predict_crop(image_bytes, latitude, longitude)
        
        # Auto-save to history
        try:
            save_prediction(
                location=result.get("location", "Unknown"),
                latitude=latitude,
                longitude=longitude,
                soil_type=result["soil_type"],
                soil_confidence=result["soil_confidence"],
                temperature=result["temperature"],
                humidity=result["humidity"],
                rainfall=result["rainfall"],
                ph=result["ph"],
                organic_carbon=result["organic_carbon"],
                crops=result["crops"],
                image_name=image.filename or "soil_image"
            )
        except Exception as save_error:
            print(f"Warning: Failed to save prediction to history: {save_error}")
            # Don't fail the prediction if history save fails
        
        return result
    except InvalidSoilImage as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e), "detail": str(e)})
    except SoilProcessingError as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e), "detail": str(e)})
    except FileNotFoundError as e:
        return JSONResponse(status_code=503, content={"success": False, "message": str(e), "detail": str(e)})
    except Exception as e:
        msg = f"Prediction error: {str(e)}"
        return JSONResponse(status_code=500, content={"success": False, "message": msg, "detail": msg})

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
