from typing import Union, List, Dict
from datetime import datetime, timedelta
import os
import requests

from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/humanitix/current-week-events")
def get_current_week_attendees():
    """
    Get attendee information for current week Humanitix events
    Returns eventName, Date, and number of attendees for each ticket type
    """
    # TODO: Implement this endpoint once we have the correct API structure
    return {"message": "This endpoint needs to be implemented"}

@app.get("/humanitix/events/{event_id}/attendees")
def get_event_attendees(event_id: str):
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

        # Fetch attendees for this event
        attendees_url = f"https://api.humanitix.com/v1/events/{event_id}/attendees"
        attendees_response = requests.get(attendees_url, headers=headers)
        attendees_response.raise_for_status()
        attendees_data = attendees_response.json()

        # Count attendees by ticket type
        ticket_counts = {}
        for attendee in attendees_data.get("attendees", []):
            ticket_type = attendee.get("ticket_type", "Unknown")
            ticket_counts[ticket_type] = ticket_counts.get(ticket_type, 0) + 1

        return {
            "eventName": event_data.get("name"),
            "date": event_data.get("start_date"),
            "attendeesByTicketType": ticket_counts,
            "totalAttendees": sum(ticket_counts.values())
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from Humanitix API: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")