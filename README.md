# Email Parser for Vikunja.io

This script creates tasks by sending an email using the Vikunja API.

The parser is a simple Python 3 script that connects to an IMAP mail server using the provided credentials. It checks for unread emails with subjects containing the word `MAPPING`, which is defined in the environment variables. It then pairs these emails to a project ID and creates a task within that project. 

A Docker container is provided for ease of use, but you can also run the script with a cron job (which is also set up in the Docker container).

I have also implemented handling of file attachements from the emails (pdf,png,jpg).
The script also removes the MAPPING tag from the task name.

## Example Usage for Cron Job

To run the script every 5 minutes, add the following to your crontab:

```shell
*/5 * * * * /usr/bin/python3 /app/mail_parser.py >> /var/log/mail_parser.log 2>&1
```

## Required Environment Variables

You must include the following environment variables:

```shell
IMAP_SERVER
EMAIL_ACCOUNT
EMAIL_PASSWORD
VIKUNJA_API_URL
VIKUNJA_TOKEN
PROJECT_MAPPING
```

Alternatively, you can edit the Python script to change these values directly.

## Running in a Docker Container

To run the parser in a Docker container, use the following command:

```shell
docker run -d   --name vikunja-mail-parser   -e IMAP_SERVER=imap_server   -e EMAIL_ACCOUNT=imap_email_account   -e EMAIL_PASSWORD=imap_email_password   -e VIKUNJA_API_URL=https://my.vikunjaurl.com/api/v1   -e VIKUNJA_TOKEN=vikunja_token   -e PROJECT_MAPPING='{"STRING_FOR_EMAIL_SUBJECT": "PROJECT_ID", "STRING_FOR_EMAIL_SUBJECT": "PROJECT_ID"}'   --restart unless-stopped   weselinka/vikunja-mail-parser
```

### Docker Compose

If you prefer using Docker Compose, you can use the following configuration:

```yaml
version: '3.8'

services:
  vikunja-mail-parser:
    image: weselinka/vikunja-mail-parser
    container_name: vikunja-mail-parser
    environment:
      IMAP_SERVER: imap_server
      EMAIL_ACCOUNT: imap_email_account
      EMAIL_PASSWORD: imap_email_password
      VIKUNJA_API_URL: https://my.vikunjaurl.com/api/v1
      VIKUNJA_TOKEN: vikunja_token
      PROJECT_MAPPING: '{"STRING_FOR_EMAIL_SUBJECT": "PROJECT_ID", "STRING_FOR_EMAIL_SUBJECT": "PROJECT_ID"}'
    restart: unless-stopped
```

### Building the Docker Container Locally

If you'd like to build the container yourself, you can do so from the `docker-compose-build.yml` file. After cloning the repository, run:

```shell
docker-compose --file docker-compose-build.yml up --build -d
```

## Notes

- Make sure the `PROJECT_MAPPING` environment variable contains a dictionary that maps email subject strings to project IDs.
- The script checks for unread emails and matches the subject to the mapping, creating tasks in the corresponding projects.

## Contributions

Any comments or feature requests are welcome! However, please note that I cannot guarantee any feature implementation at this time.
