# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.8

# Copy local code to the container image.
ENV APP_HOME /app
ENV ALERT_THRESHOLD 0
ENV TB_COST 5
ENV SLACK_ALERT false
ENV SLACK_WEBHOOK_URL https://hooks.slack.com/services/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
# ENV SLACK_WEB_API_TOKEN
# ENV SLACK_WEB_API_DESTINATION_CHANNEL
ENV EMAIL_ALERT true
ENV SENDGRID_API_KEY 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
ENV EMAIL_SENDER ohaionm@gmail.com
ENV EMAIL_CC moshe@doit-intl.com,moshe.ohaion@mentory.io


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