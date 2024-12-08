import imaplib
import email
from email.header import decode_header
import requests
import re
import json
import os
import shutil

from dotenv import load_dotenv

load_dotenv('.env')

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
    PROJECT_MAPPING = {}

ATTACHMENT_DIR = 'attachments'

# Ensure attachment directory exists
os.makedirs(ATTACHMENT_DIR, exist_ok=True)

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
    attachments = []
    
    # Decode email subject
    if msg["subject"]:
        subject, encoding = decode_header(msg["subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")
    
    # Extract email body and attachments
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get("Content-Disposition"):
                body = part.get_payload(decode=True).decode()
            elif part.get_content_disposition() and "attachment" in part.get_content_disposition():
                filename = part.get_filename()
                if filename:
                    filepath = os.path.join(ATTACHMENT_DIR, filename)
                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    attachments.append(filepath)
    else:
        body = msg.get_payload(decode=True).decode()
    
    return subject, body, attachments

def determine_project(subject):
    for keyword, project_id in PROJECT_MAPPING.items():
        if re.search(keyword, subject, re.IGNORECASE):
            return project_id, keyword
    return None, None

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
        print(f"TaskID:")
        print(response.json().get("id"))
        return response.json().get("id")  # Return the task ID for attachment upload
    else:
        print(f"Failed to create task. Status: {response.status_code}, Response: {response.json()}")
        return None

def upload_task_attachments(task_id, attachments):
    url = f"{VIKUNJA_API_URL}/tasks/{task_id}/attachments"
    headers = {"Authorization": f"Bearer {VIKUNJA_TOKEN}"}
    files = [("files", (os.path.basename(filepath), open(filepath, "rb"))) for filepath in attachments]
    
    try:
        response = requests.put(url, headers=headers, files=files)
        if response.status_code == 200:
            print(f"Attachments uploaded successfully to task ID {task_id}.")
        else:
            print(f"Failed to upload attachments. Status: {response.status_code}, Response: {response.json()}")
    finally:
        # Close file handlers
        for _, (_, file) in files:
            file.close()

def cleanup_attachments(attachments):
    for filepath in attachments:
        try:
            os.remove(filepath)
            print(f"Deleted attachment: {filepath}")
        except OSError as e:
            print(f"Error deleting file {filepath}: {e}")

def main():
    mail = connect_to_email()
    unread_emails = fetch_unread_emails(mail)
    
    for num in unread_emails:
        status, data = mail.fetch(num, "(RFC822)")
        if status != "OK":
            print(f"Failed to fetch email ID {num}.")
            continue

        msg = email.message_from_bytes(data[0][1])
        subject, body, attachments = parse_email(msg)
        print(f"Processing email with subject: {subject}")
        
        project_id, keyword = determine_project(subject)
        if project_id:
            # Remove project keyword from task title
            if keyword:
                subject = re.sub(keyword, "", subject, flags=re.IGNORECASE).strip()
            
            task_id = create_vikunja_task(project_id, subject, body)
            if task_id and attachments:
                upload_task_attachments(task_id, attachments)
                cleanup_attachments(attachments)
        else:
            print("No matching project found for email subject.")
    
    mail.logout()

if __name__ == "__main__":
    main()
