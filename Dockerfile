FROM python:3.12-alpine

WORKDIR /app

# Install curl, use it to install Supercronic, then remove curl
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.33/supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=71b0d58cc53f6bd72cf2f293e09e294b79c666d8 \
    SUPERCRONIC=supercronic-linux-amd64

RUN apk add --no-cache curl && \
    curl -fsSLO "$SUPERCRONIC_URL" && \
    echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - && \
    chmod +x "$SUPERCRONIC" && \
    mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" && \
    ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic && \
    apk del curl  # remove curl to save space

# Install Python dependencies
RUN pip install --no-cache-dir requests beautifulsoup4

# Copy script and cronjob
COPY mail_parser.py /app/
RUN printf '*/5 * * * * /usr/local/bin/python /app/mail_parser.py\n' > /app/cronjob

# Run Supercronic with your cron job
CMD ["/usr/local/bin/supercronic", "/app/cronjob"]

