import imaplib
import email
from email.header import decode_header
import requests
import re
import json
import os
from bs4 import BeautifulSoup

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

# Load IMAP_PATH from environment variables
imap_path_str = os.getenv('IMAP_PATH')

# If IMAP_PATH is defined, parse it; otherwise, use an empty string
if imap_path_str:    
    IMAP_PATH = imap_path_str
else:    
    IMAP_PATH = "inbox"

ATTACHMENT_DIR = 'attachments'

# Ensure attachment directory exists
os.makedirs(ATTACHMENT_DIR, exist_ok=True)

def connect_to_email():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select(IMAP_PATH)
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
    html_body = ""
    attachments = []

    # Decode subject
    if msg["subject"]:
        decoded_subject, encoding = decode_header(msg["subject"])[0]
        if isinstance(decoded_subject, bytes):
            subject = decoded_subject.decode(encoding or "utf-8")
        else:
            subject = decoded_subject

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = part.get("Content-Disposition")

            if content_type == "text/plain" and disposition is None:
                body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace")
            elif content_type == "text/html" and disposition is None:
                html_body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace")
            elif disposition and "attachment" in disposition:
                filename = part.get_filename()
                if filename:
                    filepath = os.path.join(ATTACHMENT_DIR, filename)
                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    attachments.append(filepath)
    else:
        content_type = msg.get_content_type()
        if content_type == "text/plain":
            body = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="replace")
        elif content_type == "text/html":
            html_body = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="replace")

   # Prefer HTML as-is, since Vikunja supports it
    if html_body:
        body = html_body
    else:
       # fallback to plain text with line breaks converted to <br> for HTML rendering
       body = body.replace("\r\n", "\n").replace("\r", "\n")
       body = body.replace("\n", "<br>")
    return subject.strip(), body.strip(), attachments


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
    print(payload)
    response = requests.put(url, json=payload, headers=headers)
    if response.status_code == 201:
        print(f"Task '{title}' created successfully in project ID {project_id}.")
        print(f"TaskID: {response.json().get('id')}")
        return response.json().get("id")
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
