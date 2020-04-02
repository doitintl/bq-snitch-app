import json
import os

import requests
from flask import Flask, request
from google.cloud import bigquery

import alert_channels
import utils

app = Flask(__name__)


@app.route('/', methods=['POST'])
def bq_snitch():
    utils.print_and_flush("BQ-snitch triggered")
    job_id = request.get_json()["protoPayload"]["serviceData"]["jobCompletedEvent"]["job"]["jobName"]["jobId"]
    alert_threshold = int(os.environ.get("ALERT_THRESHOLD"))
    tera_bytes_cost = int(os.environ.get("TB_COST"))
    client = bigquery.Client()
    job = client.get_job(job_id)
    if not hasattr(job, 'total_bytes_billed'):
        return
    project = job.project
    location = job.location
    bytes_per_tera_bytes = 2 ** 40
    total_tera_bytes_billed = job.total_bytes_billed / bytes_per_tera_bytes
    total_cost = total_tera_bytes_billed * tera_bytes_cost
    utils.print_and_flush("Total cost: " + str(total_cost))
    if total_cost >= alert_threshold:
        utils.print_and_flush("Job violated cost threshold limit: " + str(alert_threshold) + "$")
        giga_bytes_billed = total_tera_bytes_billed * 1024

        slack_alert = str_to_bool(os.environ.get("SLACK_ALERT"))
        if slack_alert:
            utils.print_and_flush("Sending slack alert")
            webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
            web_api_token = os.environ.get("SLACK_WEB_API_TOKEN")
            dest_channel = os.environ.get("SLACK_WEB_API_DESTINATION_CHANNEL")

            alert_channels.send_slack_alert(webhook_url, web_api_token, dest_channel, job.query, job_id, project,
                                            location, job.user_email, total_cost, giga_bytes_billed)

        email_alert = str_to_bool(os.environ.get("EMAIL_ALERT"))
        if email_alert:
            utils.print_and_flush("Sending email alert")
            sender = os.environ.get("EMAIL_SENDER")
            cc_list = os.environ.get("EMAIL_CC", "").split(",")
            sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")
            alert_channels.send_email_alert(sendgrid_api_key, sender, job.query, job_id, project, location,
                                            job.user_email, cc_list, total_cost, giga_bytes_billed)
        external_handler = str_to_bool(os.environ.get("EXTERNAL_HANDLER"))
        if external_handler:
            external_handler_url = os.environ.get("EXTERNAL_HANDLER_URL")
            utils.print_and_flush("Sending request to external handler" + external_handler_url)

            body = construct_post_body(job.query, job_id, project, location, job.user_email, total_cost,
                                       giga_bytes_billed)
            json_data = json.dumps(body)
            response_status = send_http(external_handler_url, json_data)

            utils.print_and_flush("External handler response status code: " + str(response_status))

    else:
        utils.print_and_flush("Job didn't violate cost threshold limit")

    return "BQ-Snitch Finished"


def str_to_bool(s):
    if s.lower() == 'true':
        return True
    elif s.lower() == 'false':
        return False
    else:
        raise ValueError


def construct_post_body(query, job_id, project, location, user_email, total_cost, giga_bytes_billed):
    body = {'query': query,
            'job_id': job_id,
            'project': project,
            'location': location,
            'user_email': user_email,
            'total_cost': total_cost,
            'giga_bytes_billed': giga_bytes_billed}
    return body


def send_http(receiving_service_url, request_body):
    # Set up metadata server request
    # See https://cloud.google.com/compute/docs/instances/verifying-instance-identity#request_signature
    metadata_server_token_url = 'http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience='

    token_request_url = metadata_server_token_url + receiving_service_url
    token_request_headers = {'Metadata-Flavor': 'Google'}

    # Fetch the token
    token_response = requests.get(token_request_url, headers=token_request_headers)
    jwt = token_response.content.decode("utf-8")

    # Provide the token in the request to the receiving service
    receiving_service_headers = {'Authorization': f'bearer {jwt}', 'Content-type': 'application/json'}
    service_response = requests.post(receiving_service_url, request_body, headers=receiving_service_headers)

    return service_response.status_code


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
