import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main():

    # Auth stuff
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    find_upcoming_events(creds=creds, number_of_events=10)

    make_event(
        creds=creds,
        summary="From Python bla",
        location="Singapore",
        description="This is a test event",
        color_id="6",
        start_date_time="2024-06-11T05:00:00",
        start_timezone="Singapore",
        end_date_time="2024-06-11T10:00:00",
        end_timezone="Singapore",
        recurrence="RRULE:FREQ=DAILY;COUNT=2",
    )


def find_upcoming_events(creds, number_of_events):
    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        max_time = (
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).isoformat() + "Z"  # 1 year from now

        print(f"Getting the upcoming {number_of_events} events")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                timeMax=max_time,
                maxResults=number_of_events,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
            return

        # Prints the start and name of the next events
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"])

    except HttpError as error:
        print(f"An error occurred: {error}")


def make_event(
    creds,
    summary,
    location,
    description,
    color_id,
    start_date_time,
    start_timezone,
    end_date_time,
    end_timezone,
    recurrence,
):
    try:
        service = build("calendar", "v3", credentials=creds)

        event = {
            "summary": summary,
            "location": location,
            "description": description,
            "colorId": color_id,
            "start": {
                "dateTime": start_date_time,
                "timeZone": start_timezone,
            },
            "end": {
                "dateTime": end_date_time,
                "timeZone": end_timezone,
            },
            "recurrence": [recurrence],
            "attendees": [{"email": "goenka.ekansh@gmail.com"}],
        }

        event = service.events().insert(calendarId="primary", body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")

    except HttpError as error:
        print(f"An error occurred: {error}")


main()
