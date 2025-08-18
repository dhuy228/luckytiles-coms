from typing import Union, List, Dict
from datetime import datetime, timedelta
from collections import defaultdict
import json
import os
import requests
import pytz

from fastapi import FastAPI, HTTPException, Depends, Header

app = FastAPI()

def verify_api_key(x_api_key: str = Header()):
    """Verify the API key in the request header"""
    expected_api_key = os.getenv("API_KEY")
    if not expected_api_key:
        raise HTTPException(status_code=500, detail="API key not configured on server")
    
    if x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return x_api_key


@app.get("/")
def read_root():
    return {"Hello": "World"}


def _format_date_au(iso_date):
    """Convert ISO date to Australian time in 'February 28, 2025' format"""
    dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
    au_dt = dt.astimezone(pytz.timezone('Australia/Sydney'))
    return au_dt.strftime('%B %d, %Y')


def _get_current_week_event_id(event_id: str):
    # Get API key from environment variables
    api_key = os.getenv("HUMANITIX_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500,
                            detail="Humanitix API key not configured")

    headers = {"x-api-key": f"{api_key}", "Accept": "application/json"}

    try:
        # Fetch specific event details
        event_url = f"https://api.humanitix.com/v1/events/{event_id}"
        event_response = requests.get(event_url, headers=headers)
        event_response.raise_for_status()
        event_data = event_response.json()

        name = event_data.get("name", "")
        dates = event_data.get("dates", [])

        now = datetime.now(pytz.timezone('Australia/Sydney'))
        sydney_tz = pytz.timezone('Australia/Sydney')
        sub_event_id = None
        sub_event_date = None
        # Calculate Monday-Sunday week
        current_week_start = now.replace(hour=0,
                                         minute=0,
                                         second=0,
                                         microsecond=0)

        # Calculate Monday-Sunday week
        day_of_week = now.weekday()  # 0 = Monday, 1 = Tuesday, etc.
        days_to_monday = -day_of_week  # Days to go back to Monday
        current_week_start += timedelta(days=days_to_monday)
        current_week_end = current_week_start + timedelta(days=6)  # Sunday

        for date in dates:
            if date.get('deleted') or date.get('disabled'):
                continue

            # Convert UTC event time to Australian timezone
            start_date_utc = datetime.fromisoformat(date['startDate'].replace(
                'Z', '+00:00'))
            end_date_utc = datetime.fromisoformat(date['endDate'].replace(
                'Z', '+00:00'))

            start_date = start_date_utc.astimezone(sydney_tz)
            end_date = end_date_utc.astimezone(sydney_tz)

            if start_date <= current_week_end and end_date >= current_week_start:
                sub_event_id = date.get('_id')
                sub_event_date = _format_date_au(date.get('startDate'))

        return (name, sub_event_date, sub_event_id)

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching sub_event_id data from Humanitix API: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Unexpected error: {str(e)}")


def _get_current_week_event_info(event_id: str, sub_event_id: str):
    # Get API key from environment variables
    api_key = os.getenv("HUMANITIX_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500,
                            detail="Humanitix API key not configured")

    headers = {"x-api-key": f"{api_key}", "Accept": "application/json"}

    params = {"page": 1, "eventDateId": sub_event_id}

    try:
        # Fetch specific event details
        event_url = f"https://api.humanitix.com/v1/events/{event_id}/tickets"
        event_response = requests.get(event_url,
                                      headers=headers,
                                      params=params)
        event_response.raise_for_status()
        event_data = event_response.json()

        total_tickets = event_data.get("total", 0)
        tickets = event_data.get("tickets", [])

        ticket_type_data = defaultdict(lambda: {
            'total_attendees': 0,
            'attendee_names': []
        })

        for ticket in tickets:
            ticket_type = ticket.get('ticketTypeName', '')
            number = ticket.get('number', 0)

            # Get attendee name
            first_name = ticket.get('firstName', '')
            last_name = ticket.get('lastName', '')
            full_name = f"{first_name} {last_name}".strip()

            # Add to totals
            ticket_type_data[ticket_type]['total_attendees'] += number

            # Add attendee name (handle multiple tickets per person)
            ticket_type_data[ticket_type]['attendee_names'].append(full_name)

        return (total_tickets, ticket_type_data)

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching sub_event_info data from Humanitix API: {str(e)}. Id: {sub_event_id}")
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Unexpected error: {str(e)}")


def _format_event_message(data):
    message = f"🎯 {data['event_name']}\n"
    message += f"📅 {data['event_date']}\n"
    message += f"🎫 Total Tickets: {data['tickets']}\n\n"

    for ticket_type, info in data['details'].items():
        message += f"🎪 {ticket_type} ({info['total_attendees']} attendees):\n"
        for name in info['attendee_names']:
            message += f"   • {name}\n"
        message += "\n"

    return message.strip()


@app.get("/humanitix/events/{event_id}")
def get_events(event_id: str, _api_key: str = Depends(verify_api_key)):
    """
    Get attendee information for a specific Humanitix event
    Returns eventName, Date, and number of attendees for each ticket type
    """

    # Get API key from environment variables
    api_key = os.getenv("HUMANITIX_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500,
                            detail="Humanitix API key not configured")

    headers = {"x-api-key": f"{api_key}", "Accept": "application/json"}

    event_name, event_date, sub_event_id = _get_current_week_event_id(event_id)

    if sub_event_id is None:
        return _format_event_message({
            "event_name": event_name,
            "event_date": None,
            "tickets": 0,
            "details": {}
        })

    total_tickets, ticket_type_data = _get_current_week_event_info(
        event_id, "sub_event_id")

    try:
        return _format_event_message({
            "event_name": event_name,
            "event_date": event_date,
            "tickets": total_tickets,
            "details": ticket_type_data
        })

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching get_events data from Humanitix API: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Unexpected error: {str(e)}")
