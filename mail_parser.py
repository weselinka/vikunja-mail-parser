import imaplib
import email
from email.header import decode_header
import requests
import re
import json
import os

# Load configuration from environment variables
IMAP_SERVER = os.getenv('IMAP_SERVER')
EMAIL_ACCOUNT = os.getenv('EMAIL_ACCOUNT')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
VIKUNJA_API_URL = os.getenv('VIKUNJA_API_URL')
VIKUNJA_TOKEN = os.getenv('VIKUNJA_TOKEN')

# Load PROJECT_MAPPING from environment variables
project_mapping_str = os.getenv('PROJECT_MAPPING')

# If PROJECT_MAPPING is defined, parse it; otherwise, use an empty dictionary
if project_mapping_str:
    PROJECT_MAPPING = json.loads(project_mapping_str)
else:
    print("No Projects mapped, check config of env")
    print({PROJECT_MAPPING})
    PROJECT_MAPPING = {}

def connect_to_email():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select("inbox")
    return mail

def fetch_unread_emails(mail):
    status, messages = mail.search(None, "UNSEEN")
    if status != "OK" or len(messages[0].split()) == 0:
        print("No new messages to parse.")
        return []
    return messages[0].split()

def parse_email(msg):
    subject = ""
    body = ""
    
    # Decode email subject
    if msg["subject"]:
        subject, encoding = decode_header(msg["subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")
    
    # Extract email body
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode()
                break
    else:
        body = msg.get_payload(decode=True).decode()
    
    return subject, body

def determine_project(subject):
    for keyword, project_id in PROJECT_MAPPING.items():
        if re.search(keyword, subject, re.IGNORECASE):
            return project_id
    return None

def create_vikunja_task(project_id, title, description):
    url = f"{VIKUNJA_API_URL}/projects/{project_id}/tasks"
    headers = {"Authorization": f"Bearer {VIKUNJA_TOKEN}"}
    payload = {
        "title": title,
        "description": description,
    }
    response = requests.put(url, json=payload, headers=headers)
    if response.status_code == 201:
        print(f"Task '{title}' created successfully in project ID {project_id}.")
    else:
        print(f"Failed to create task. Status: {response.status_code}, Response: {response.json()}")

def main():
    mail = connect_to_email()
    unread_emails = fetch_unread_emails(mail)
    
    for num in unread_emails:
        status, data = mail.fetch(num, "(RFC822)")
        if status != "OK":
            print(f"Failed to fetch email ID {num}.")
            continue

        msg = email.message_from_bytes(data[0][1])
        subject, body = parse_email(msg)
        print(f"Processing email with subject: {subject}")
        
        project_id = determine_project(subject)
        if project_id:
            create_vikunja_task(project_id, subject, body)
        else:
            print("No matching project found for email subject.")
    
    mail.logout()

if __name__ == "__main__":
    main()
