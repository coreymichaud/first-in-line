import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the webhook URL from the environment variable
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL is not set in the .env file.")

message = "Job @ Company \n<https://coreymichaud.dev>"  # If you wrap the link in <>, Discord will display it as a link WITHOUT the url image preview.

data = {
    "content": message
}

response = requests.post(WEBHOOK_URL, json=data)

if response.status_code == 204:
    print("Message sent successfully!")
else:
    print(f"Failed to send message: {response.status_code} - {response.text}")
