# Use an official Python runtime as a parent image
FROM alpine:3.20 

# Set the working directory in the container
WORKDIR /app

# Install cron and necessary dependencies
RUN apk update && \
    apk add libffi-dev && \
    apk add gcc && \
    apk add python3 && \
    apk add py3-requests && \
    apk add py3-pip 

# Copy the current directory contents into the container at /app
COPY mail-parser.py /app/

RUN echo "*/5 * * * * cd /app && /usr/bin/python3 /app/mail_parser.py >> /var/log/mail_parser.log 2>&1" >> /etc/crontabs/root
RUN echo " " >> /etc/crontabs/root

# Run the script and keep the container running (via cron)
CMD ["crond", "-f"]
