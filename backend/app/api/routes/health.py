"""
Health check endpoints for monitoring system status
"""
import os
import psutil
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.config import get_settings
from app.utils.exceptions import AppException

router = APIRouter()
settings = get_settings()

@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """Basic health check endpoint"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "mna-entry-tool",
            "version": settings.VERSION
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health_check():
    """Detailed health check with system metrics"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Service checks
        services_status = await check_services()
        
        # Model availability
        models_status = await check_models()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "mna-entry-tool",
            "version": settings.VERSION,
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2)
            },
            "services": services_status,
            "models": models_status
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Detailed health check failed")

async def check_services() -> Dict[str, str]:
    """Check external services availability"""
    services = {}
    
    # Check Redis
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        services["redis"] = "healthy"
    except Exception as e:
        services["redis"] = f"error: {str(e)}"
    
    # Check Google Cloud Vision (if configured)
    if settings.GOOGLE_CLOUD_CREDENTIALS:
        try:
            from google.cloud import vision
            client = vision.ImageAnnotatorClient()
            services["google_cloud_vision"] = "healthy"
        except Exception as e:
            services["google_cloud_vision"] = f"error: {str(e)}"
    else:
        services["google_cloud_vision"] = "not_configured"
    
    # Check OpenAI (if configured)
    if settings.OPENAI_API_KEY:
        try:
            import openai
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            services["openai"] = "healthy"
        except Exception as e:
            services["openai"] = f"error: {str(e)}"
    else:
        services["openai"] = "not_configured"
    
    return services

async def check_models() -> Dict[str, str]:
    """Check AI models