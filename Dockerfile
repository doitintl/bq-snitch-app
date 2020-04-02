# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.8

# Copy local code to the container image.
ENV APP_HOME /app
ENV ALERT_THRESHOLD 0
ENV TB_COST 5
ENV SLACK_ALERT false
# ENV SLACK_WEBHOOK_URL
# ENV SLACK_WEB_API_TOKEN
# ENV SLACK_WEB_API_DESTINATION_CHANNEL
ENV EMAIL_ALERT false
# ENV SENDGRID_API_KEY
# ENV EMAIL_SENDER
# ENV EMAIL_CC
ENV EXTERNAL_HANDLER false
ENV EXTERNAL_HANDLER_URL ''
ENV EXTERNAL_HANDLER_PORT 8080

WORKDIR $APP_HOME
COPY . ./

# Install production dependencies.
RUN pip install Flask gunicorn
RUN pip install -r requirements.txt

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app