from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import logging
import asyncio
from datetime import datetime

# Import roex-python library
from roex_python.client import RoExClient
from roex_python.models import (
    TrackData, MultitrackMixRequest, InstrumentGroup,
    PresenceSetting, PanPreference, ReverbPreference, MusicalStyle,
    MasteringRequest, DesiredLoudness,
    EnhanceMixRequest, AnalysisRequest, AudioCleanupRequest, SoundSource
)

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

# Initialize Roex client
roex_api_key = os.getenv("ROEX_API_KEY")
if not roex_api_key:
    logger.error("ROEX_API_KEY environment variable not set")
    raise ValueError("ROEX_API_KEY environment variable not set")

client = RoExClient(api_key=roex_api_key)

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
        # Use roex-python's file upload utility
        from roex_python.utils import upload_file
        
        # For now, return a placeholder - actual implementation would use Roex's upload system
        # This would be replaced with proper Roex upload URL generation
        return {
            "upload_url": "https://placeholder-upload-url.com",
            "file_url": f"https://storage.roexaudio.com/uploads/{request.file_name}",
            "success": True
        }
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
    """Process mastering using roex-python"""
    try:
        mastering_request = MasteringRequest(
            track_url=request.file_url,
            musical_style=MusicalStyle(request.musical_style.upper()) if request.musical_style else MusicalStyle.POP,
            desired_loudness=DesiredLoudness.MEDIUM,
            sample_rate="44100"
        )
        
        # Create mastering preview task
        task = client.mastering.create_mastering_preview(mastering_request)
        logger.info(f"Mastering task created: {task.mastering_task_id}")
        
        return {
            "success": True,
            "job_id": task.mastering_task_id,
            "service_type": "mastering_full",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Mastering failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_mixing(request: ProcessAudioRequest):
    """Process mixing using roex-python"""
    try:
        # For mixing, we need track data - simplified for single track
        tracks = [
            TrackData(
                track_url=request.file_url,
                instrument_group=InstrumentGroup.VOCAL_GROUP,
                presence_setting=PresenceSetting.LEAD,
                pan_preference=PanPreference.CENTRE,
                reverb_preference=ReverbPreference.LOW
            )
        ]
        
        mix_request = MultitrackMixRequest(
            track_data=tracks,
            musical_style=MusicalStyle(request.musical_style.upper()) if request.musical_style else MusicalStyle.POP,
            return_stems=False
        )
        
        # Create mix preview task
        task = client.mix.create_mix_preview(mix_request)
        logger.info(f"Mix task created: {task.multitrack_task_id}")
        
        return {
            "success": True,
            "job_id": task.multitrack_task_id,
            "service_type": "mixing_full",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Mixing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_mix_enhancement(request: ProcessAudioRequest):
    """Process mix enhancement using roex-python"""
    try:
        enhance_request = EnhanceMixRequest(
            track_url=request.file_url
        )
        
        # Create enhancement task
        task = client.enhance.create_enhancement(enhance_request)
        logger.info(f"Enhancement task created: {task.enhance_task_id}")
        
        return {
            "success": True,
            "job_id": task.enhance_task_id,
            "service_type": "mix_enhance",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Mix enhancement failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_analysis(request: ProcessAudioRequest):
    """Process audio analysis using roex-python"""
    try:
        analysis_request = AnalysisRequest(
            track_url=request.file_url
        )
        
        # Create analysis task
        task = client.analysis.create_analysis(analysis_request)
        logger.info(f"Analysis task created: {task.analysis_task_id}")
        
        return {
            "success": True,
            "job_id": task.analysis_task_id,
            "service_type": "mix_analysis",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_cleanup(request: ProcessAudioRequest):
    """Process audio cleanup using roex-python"""
    try:
        cleanup_request = AudioCleanupRequest(
            audio_file_location=request.file_url,
            sound_source=SoundSource.VOCAL_GROUP  # Default to vocal cleanup
        )
        
        # Create cleanup task
        task = client.cleanup.create_audio_cleanup(cleanup_request)
        logger.info(f"Cleanup task created: {task.cleanup_task_id}")
        
        return {
            "success": True,
            "job_id": task.cleanup_task_id,
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
        
        # Check job status based on service type
        if request.service_type == "mastering_full":
            try:
                result = client.mastering.retrieve_preview_master(request.job_id)
                if result:
                    return {
                        "success": True,
                        "status": "completed",
                        "download_url": result.get('download_url_mastered_preview'),
                        "job_id": request.job_id
                    }
            except Exception:
                # Job might still be processing
                pass
                
        elif request.service_type == "mixing_full":
            try:
                result = client.mix.retrieve_preview_mix(request.job_id)
                if result:
                    return {
                        "success": True,
                        "status": "completed",
                        "download_url": result.get('preview_mix_url'),
                        "job_id": request.job_id
                    }
            except Exception:
                pass
                
        elif request.service_type == "mix_enhance":
            try:
                result = client.enhance.retrieve_enhancement(request.job_id)
                if result:
                    return {
                        "success": True,
                        "status": "completed",
                        "download_url": result.get('download_url_enhanced_mix'),
                        "job_id": request.job_id
                    }
            except Exception:
                pass
                
        elif request.service_type == "mix_analysis":
            try:
                result = client.analysis.retrieve_analysis(request.job_id)
                if result:
                    return {
                        "success": True,
                        "status": "completed",
                        "analysis_data": result,
                        "job_id": request.job_id
                    }
            except Exception:
                pass
                
        elif request.service_type == "cleanup":
            try:
                result = client.cleanup.retrieve_audio_cleanup(request.job_id)
                if result:
                    return {
                        "success": True,
                        "status": "completed",
                        "cleanup_data": result,
                        "job_id": request.job_id
                    }
            except Exception:
                pass
        
        # If we reach here, job is still processing
        return {
            "success": True,
            "status": "processing",
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