from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import logging
import httpx
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Roex Python Microservice", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Roex API configuration
roex_api_key = os.getenv("ROEX_API_KEY")
if not roex_api_key:
    logger.error("ROEX_API_KEY environment variable not set")
    raise ValueError("ROEX_API_KEY environment variable not set")

ROEX_API_BASE = "https://api.roexaudio.com/v1"

# Pydantic models for requests
class ProcessAudioRequest(BaseModel):
    service_type: str
    file_url: str
    musical_style: Optional[str] = "POP"
    webhook_url: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = {}

class JobStatusRequest(BaseModel):
    job_id: str
    service_type: str

class FileUploadRequest(BaseModel):
    file_name: str
    content_type: str

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# File upload endpoint - gets signed URL from Roex
@app.post("/upload/signed-url")
async def get_upload_url(request: FileUploadRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ROEX_API_BASE}/upload/signed-url",
                headers={"Authorization": f"Bearer {roex_api_key}"},
                json={
                    "file_name": request.file_name,
                    "content_type": request.content_type
                }
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Upload URL generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Main audio processing endpoint
@app.post("/process")
async def process_audio(request: ProcessAudioRequest, background_tasks: BackgroundTasks):
    try:
        logger.info(f"Processing audio with service type: {request.service_type}")
        
        # Map service types to Roex operations
        if request.service_type == "mastering_full":
            return await process_mastering(request)
        elif request.service_type == "mixing_full":
            return await process_mixing(request)
        elif request.service_type == "mix_enhance":
            return await process_mix_enhancement(request)
        elif request.service_type == "mix_analysis":
            return await process_analysis(request)
        elif request.service_type == "cleanup":
            return await process_cleanup(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported service type: {request.service_type}")
            
    except Exception as e:
        logger.error(f"Audio processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_mastering(request: ProcessAudioRequest):
    """Process mastering using Roex HTTP API"""
    try:
        payload = {
            "track_url": request.file_url,
            "musical_style": request.musical_style.upper() if request.musical_style else "POP",
            "desired_loudness": "MEDIUM",
            "sample_rate": "44100"
        }
        
        if request.webhook_url:
            payload["webhook_url"] = request.webhook_url
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ROEX_API_BASE}/mastering/preview",
                headers={"Authorization": f"Bearer {roex_api_key}"},
                json=payload
            )
            response.raise_for_status()
            result = response.json()
        
        logger.info(f"Mastering task created: {result.get('mastering_task_id')}")
        
        return {
            "success": True,
            "job_id": result.get("mastering_task_id"),
            "service_type": "mastering_full",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Mastering failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_mixing(request: ProcessAudioRequest):
    """Process mixing using Roex HTTP API"""
    try:
        payload = {
            "track_data": [{
                "track_url": request.file_url,
                "instrument_group": "VOCAL_GROUP",
                "presence_setting": "LEAD",
                "pan_preference": "CENTRE",
                "reverb_preference": "LOW"
            }],
            "musical_style": request.musical_style.upper() if request.musical_style else "POP",
            "return_stems": False
        }
        
        if request.webhook_url:
            payload["webhook_url"] = request.webhook_url
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ROEX_API_BASE}/mix/preview",
                headers={"Authorization": f"Bearer {roex_api_key}"},
                json=payload
            )
            response.raise_for_status()
            result = response.json()
        
        logger.info(f"Mix task created: {result.get('multitrack_task_id')}")
        
        return {
            "success": True,
            "job_id": result.get("multitrack_task_id"),
            "service_type": "mixing_full",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Mixing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_mix_enhancement(request: ProcessAudioRequest):
    """Process mix enhancement using Roex HTTP API"""
    try:
        payload = {
            "track_url": request.file_url
        }
        
        if request.webhook_url:
            payload["webhook_url"] = request.webhook_url
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ROEX_API_BASE}/enhance",
                headers={"Authorization": f"Bearer {roex_api_key}"},
                json=payload
            )
            response.raise_for_status()
            result = response.json()
        
        logger.info(f"Enhancement task created: {result.get('enhance_task_id')}")
        
        return {
            "success": True,
            "job_id": result.get("enhance_task_id"),
            "service_type": "mix_enhance",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Mix enhancement failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_analysis(request: ProcessAudioRequest):
    """Process audio analysis using Roex HTTP API"""
    try:
        payload = {
            "track_url": request.file_url
        }
        
        if request.webhook_url:
            payload["webhook_url"] = request.webhook_url
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ROEX_API_BASE}/analysis",
                headers={"Authorization": f"Bearer {roex_api_key}"},
                json=payload
            )
            response.raise_for_status()
            result = response.json()
        
        logger.info(f"Analysis task created: {result.get('analysis_task_id')}")
        
        return {
            "success": True,
            "job_id": result.get("analysis_task_id"),
            "service_type": "mix_analysis",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_cleanup(request: ProcessAudioRequest):
    """Process audio cleanup using Roex HTTP API"""
    try:
        payload = {
            "audio_file_location": request.file_url,
            "sound_source": "VOCAL_GROUP"  # Default to vocal cleanup
        }
        
        if request.webhook_url:
            payload["webhook_url"] = request.webhook_url
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ROEX_API_BASE}/cleanup",
                headers={"Authorization": f"Bearer {roex_api_key}"},
                json=payload
            )
            response.raise_for_status()
            result = response.json()
        
        logger.info(f"Cleanup task created: {result.get('cleanup_task_id')}")
        
        return {
            "success": True,
            "job_id": result.get("cleanup_task_id"),
            "service_type": "cleanup",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Job status endpoint
@app.post("/status")
async def get_job_status(request: JobStatusRequest):
    try:
        logger.info(f"Checking status for job: {request.job_id}, service: {request.service_type}")
        
        endpoint_map = {
            "mastering_full": f"/mastering/preview/{request.job_id}",
            "mixing_full": f"/mix/preview/{request.job_id}",
            "mix_enhance": f"/enhance/{request.job_id}",
            "mix_analysis": f"/analysis/{request.job_id}",
            "cleanup": f"/cleanup/{request.job_id}"
        }
        
        endpoint = endpoint_map.get(request.service_type)
        if not endpoint:
            raise HTTPException(status_code=400, detail=f"Unsupported service type: {request.service_type}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ROEX_API_BASE}{endpoint}",
                headers={"Authorization": f"Bearer {roex_api_key}"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "status": "completed",
                    "result": result,
                    "job_id": request.job_id
                }
            elif response.status_code == 202:
                return {
                    "success": True,
                    "status": "processing",
                    "job_id": request.job_id
                }
            else:
                return {
                    "success": False,
                    "status": "failed",
                    "error": f"HTTP {response.status_code}",
                    "job_id": request.job_id
                }
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        return {
            "success": False,
            "status": "failed",
            "error": str(e),
            "job_id": request.job_id
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)