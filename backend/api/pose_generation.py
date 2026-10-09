import logging
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import config

router = APIRouter()
logger = logging.getLogger(__name__)

class PoseRequest(BaseModel):
    text: str
    spoken_language: str = "en"
    signed_language: str = "ase"

@router.post("/generate_pose")
async def generate_pose(request: PoseRequest):
    """
    Generate pose data from text using the translate project's API or local fallback.
    """
    pose_data = None
    if config.POSE_API_URL and config.POSE_API_URL.startswith("http"):
        try:
            params = {
                'text': request.text,
                'spoken': request.spoken_language,
                'signed': request.signed_language
            }
            response = requests.get(config.POSE_API_URL, params=params, timeout=5)
            response.raise_for_status()
            pose_data = response.content
        except Exception as e:
            logger.warning(f"Remote pose generation failed, falling back to local pose: {e}")
    
    if not pose_data:
        import os
        default_pose_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "default.pose")
        if os.path.exists(default_pose_path):
            with open(default_pose_path, "rb") as f:
                pose_data = f.read()
        else:
            raise HTTPException(status_code=503, detail="Pose generation unavailable and default pose file not found.")
        
    import base64
    pose_data_b64 = base64.b64encode(pose_data).decode('utf-8')
    
    return {
        "pose_data": pose_data_b64,
        "data_format": "binary_base64"
    } 