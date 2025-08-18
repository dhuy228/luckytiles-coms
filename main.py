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
    
    # Get API key from environment variables
    api_key = os.getenv("HUMANITIX_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Humanitix API key not configured")
    
    # Calculate current week date range
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    headers = {
        "x-api-key": f"{api_key}",
        "Accept": "application/json"
    }
    
    try:
        # Note: This endpoint would need to be modified once we know how to get all events
        # For now, this is a placeholder that shows the structure
        return {
            "message": "To implement this endpoint, we need to know how to get a list of all events from Humanitix API",
            "weekRange": {
                "startDate": start_of_week.strftime("%Y-%m-%d"),
                "endDate": end_of_week.strftime("%Y-%m-%d")
            },
            "note": "Once we have an endpoint to list all events, we can filter by dates and get attendees for each"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

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
            "eventId": event_data.get("_id"),
            "description": event_data.get("description"),
            "location": event_data.get("eventLocation", {}).get("venueName"),
            "address": event_data.get("eventLocation", {}).get("address"),
            "startDate": event_data.get("startDate"),
            "endDate": event_data.get("endDate"),
            "timezone": event_data.get("timezone"),
            "dates": event_data.get("dates", []),
            "attendeesByTicketType": ticket_counts,
            "totalAttendees": sum(ticket_counts.values()),
            "ticketTypes": event_data.get("ticketTypes", []),
            "totalCapacity": event_data.get("totalCapacity"),
            "eventUrl": event_data.get("url")
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from Humanitix API: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")