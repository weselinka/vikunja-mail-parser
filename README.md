# 📧 Email Parser for Vikunja

This script connects to your email inbox and automatically creates tasks in [Vikunja](https://vikunja.io) based on incoming emails.

- 💌 Reads unread emails via IMAP
- 📬 Parses the subject line to determine the target Vikunja project
- ✍️ Creates a new task with the email body as the task description
- 📎 Supports file attachments (uploaded to the created task)
- 🐳 Runs as a Docker container with cron (using Supercronic)

---

## 🚀 How It Works

The script scans your inbox for **unread emails**, checks if the subject matches any keyword in `PROJECT_MAPPING`, and creates a task in the matching Vikunja project.

For example, with this config:

```env
PROJECT_MAPPING='{"support": "3", "dev": "7"}'
```

- An email with subject: `Bug report - support` → creates a task in project ID **3**
- An email with subject: `dev: add feature X` → creates a task in project ID **7**

The matching keyword (`support`, `dev`) is **removed** from the task title.

---

## 🛠 Required Environment Variables

| Variable           | Example value                                  | Description |
|--------------------|------------------------------------------------|-------------|
| `IMAP_SERVER`      | `imap.gmail.com`                               | Your IMAP server hostname |
| `EMAIL_ACCOUNT`    | `you@example.com`                              | The email address to check |
| `EMAIL_PASSWORD`   | `app-password-123`                             | The password or app password |
| `VIKUNJA_API_URL`  | `https://vikunja.example.com/api/v1`           | Base URL for the Vikunja API |
| `VIKUNJA_TOKEN`    | `your-bearer-token`                            | Personal access token from Vikunja |
| `PROJECT_MAPPING`  | `'{"support": "3", "dev": "7"}'`               | JSON object mapping subject keywords to project IDs |

## 🛠 Optional Environment Variables

| Variable           | Example value                                  | Description |
|--------------------|------------------------------------------------|-------------|
| `IMAP_FOLDER`      | `inbox/todo`                                   | optional: IMAP Path to folder, default is `inbox` |
| `DEFAULT_PROJECT`  | `1`                                            | optional: Project ID to put any email into (useful only with an IMAP Folder set) |

> 🔹 **What is a Vikunja Project ID?**  
> You can find it by opening a project in Vikunja and checking the URL:  
> `https://vikunja.example.com/projects/3/tasks` → the ID is **3**

---

## 🐳 Running in Docker

```bash
docker run -d \
  --name vikunja-mail-parser \
  -e IMAP_SERVER=imap.example.com \
  -e EMAIL_ACCOUNT=you@example.com \
  -e EMAIL_PASSWORD=yourpassword \
  -e VIKUNJA_API_URL=https://vikunja.example.com/api/v1 \
  -e VIKUNJA_TOKEN=your-vikunja-token \
  -e PROJECT_MAPPING='{"support": "3", "dev": "7"}' \
  -e IMAP_FOLDER='inbox' \
  --restart unless-stopped \
  weselinka/vikunja-mail-parser
```

---

### 🐋 Docker Compose

```yaml
version: '3.8'

services:
  vikunja-mail-parser:
    image: weselinka/vikunja-mail-parser
    container_name: vikunja-mail-parser
    environment:
      IMAP_SERVER: imap.example.com
      EMAIL_ACCOUNT: you@example.com
      EMAIL_PASSWORD: yourpassword
      VIKUNJA_API_URL: https://vikunja.example.com/api/v1
      VIKUNJA_TOKEN: your-vikunja-token
      PROJECT_MAPPING: '{"support": "3", "dev": "7"}'
      IMAP_FOLDER: 'inbox'
    restart: unless-stopped
```
---

## 🛠 Build the Docker Image Locally

Download the project and inside the project directory run:
```bash
docker build -t weselinka/vikunja-mail-parser:latest .
```

---

## 💡 Notes

- Emails must be **unread** to be processed.
- Attachments will be uploaded to the created task.
- Tasks are created with the full email body (formatted with line breaks or HTML).
- If no keyword in the subject matches `PROJECT_MAPPING`, the email is **MARKED READ** and ignored.

---

## 🙌 Contributions

Feature requests, issues, or PRs are welcome. Feel free to fork or suggest improvements!
