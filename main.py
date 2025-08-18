from typing import Union, List, Dict
from datetime import datetime, timedelta
import os
import requests

from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


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
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Fetch all events (without date parameters)
        events_url = "https://api.humanitix.com/v1/events"
        
        events_response = requests.get(events_url, headers=headers)
        events_response.raise_for_status()
        events_data = events_response.json()
        
        result = []
        
        for event in events_data.get("events", []):
            event_id = event["id"]
            event_name = event["name"]
            event_date_str = event["start_date"]
            
            # Parse event date and check if it's in current week
            try:
                event_date = datetime.fromisoformat(event_date_str.replace('Z', '+00:00'))
                event_date_local = event_date.replace(tzinfo=None)  # Remove timezone for comparison
                
                # Check if event is in current week
                if not (start_of_week <= event_date_local <= end_of_week):
                    continue
                    
            except (ValueError, AttributeError):
                # Skip events with invalid dates
                continue
            
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
            
            event_info = {
                "eventName": event_name,
                "date": event_date_str,
                "attendeesByTicketType": ticket_counts,
                "totalAttendees": sum(ticket_counts.values())
            }
            
            result.append(event_info)
        
        return {
            "weekRange": {
                "startDate": start_of_week.strftime("%Y-%m-%d"),
                "endDate": end_of_week.strftime("%Y-%m-%d")
            },
            "events": result
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from Humanitix API: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")