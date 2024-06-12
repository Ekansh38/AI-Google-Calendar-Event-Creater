import datetime
import os.path
import re
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI

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

    # find_upcoming_events(creds=creds, number_of_events=10)

    user_input = input("> ")
    prompt = (
        "You need to look at a users input and create google calendar event based on it. You need to fill out the follow fields: summary: Any String treat it like a title, location: Any String, description: Any String, start_date_time: String in this format: 2024-06-11T05:00:00, start_timezone: In formate of country/city if just a country and or city like Singpore just use the country name and nothing else. end_date_time: String in this format: 2024-06-11T10:00:00, end_timezone: same as start_timezone, recurrence: a string in this format RRULE:FREQ=DAILY;COUNT=2 but most of the time for default leave it like RRULE:FREQ=DAILY;COUNT=1, color_id: a number from 1 - 11 one is the color lavendar two is sage three is grape four is flamingo five is banana six is tangerine seven is peacock eight is graphite nine is blueberry ten is basil and eleven is tomato also simpley enter a number and nothing else in this field. The user input is: "
        + user_input
        + ". Also some context, we are in Singapore. The current date and time is"
        + " "
        + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        + ". Also please dont write anything other than the fields in the user input. Also dont write None instead leave it blank if you want to leave somthing blank"
    )

    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        stream=False,
    )

    response = response.choices[0].message.content
    # print(response)
    response = parse_response(response)

    recurrence = response["recurrence"]

    if response["recurrence"] == "":
        recurrence = "RRULE:FREQ=DAILY;COUNT=1"

    # print(response)

    make_event(
        creds=creds,
        summary=response["summary"],
        location=response["location"],
        description=response["description"],
        color_id=response["color_id"],
        start_date_time=response["start_date_time"],
        start_timezone=response["start_timezone"],
        end_date_time=response["end_date_time"],
        end_timezone=response["end_timezone"],
        recurrence=recurrence,
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


def parse_response(response):
    fields = [
        "summary",
        "location",
        "description",
        "start_date_time",
        "start_timezone",
        "end_date_time",
        "end_timezone",
        "recurrence",
        "color_id",
    ]
    parsed_data = {}

    for field in fields:
        pattern = re.compile(rf"{field}: (.*)")
        match = pattern.search(response)
        if match:
            parsed_data[field] = match.group(1).strip()
        else:
            parsed_data[field] = None

    return parsed_data


main()
