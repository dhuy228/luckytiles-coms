from typing import Union, List, Dict
from datetime import datetime, timedelta
import os
import requests

from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/humanitix/events/{event_id}")
def get_events(event_id: str):
    """
    Get attendee information for a specific Humanitix event
    Returns eventName, Date, and number of attendees for each ticket type
    """

    # Get API key from environment variables
    api_key = os.getenv("HUMANITIX_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Humanitix API key not configured")

    headers = {
        "x-api-key": f"{api_key}",
        "Accept": "application/json"
    }

    try:
        # Fetch specific event details
        event_url = f"https://api.humanitix.com/v1/events/{event_id}"
        event_response = requests.get(event_url, headers=headers)
        event_response.raise_for_status()
        event_data = event_response.json()

        return event_data

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from Humanitix API: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")