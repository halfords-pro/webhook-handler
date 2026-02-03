import json
import logging
import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Freshdesk Webhook Endpoint",
    description="Minimal webhook receiver for Freshdesk events",
    version="1.0.0"
)

# Webhook storage directory
WEBHOOK_REQUESTS_DIR = Path("webhook-requests")

@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/webhooks/freshdesk")
async def receive_freshdesk_webhook(request: Request):
    """
    Receive and store Freshdesk webhook payloads.

    Saves each webhook to disk as a JSON file with a unique ID.
    """

    FD_WEBHOOK_REQUESTS_DIR = WEBHOOK_REQUESTS_DIR / "freshdesk"

    try:
        # Parse request body
        payload = await request.json()

        # Generate unique ID for this webhook
        request_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat()

        # Prepare webhook data with metadata
        webhook_data = {
            "request_id": request_id,
            "timestamp": timestamp,
            "source": "freshdesk",
            "payload": payload
        }

        # Save to disk
        FD_WEBHOOK_REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = FD_WEBHOOK_REQUESTS_DIR / f"{request_id}.json"
        with open(file_path, "w") as f:
            json.dump(webhook_data, f, indent=2)

        logger.info(f"Received webhook {request_id} - saved to {file_path}")

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "request_id": request_id,
                "timestamp": timestamp
            }
        )

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/")
async def root():
    """Root endpoint with basic service information."""
    return {
        "service": "Freshdesk Webhook Endpoint",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "webhook": "/webhooks/freshdesk"
        }
    }
