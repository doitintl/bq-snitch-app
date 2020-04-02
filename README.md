# BigQuery Snitch
Implemented as Google Cloud Run and triggered by BigQuery `query` job to inform the user/channel on Email/Slack along with query details (date/time, syntax, amount of scanned data and cost).

# Authorization
To use Events for Cloud Run, ensure that you have the roles/run.admin role which grants you run.triggers.* permissions. 
Users with project owner/editor roles have these permissions by default. To grant these permissions to another user, ensure they are granted one of these roles. 
You may run one of the following commands to do so:

gcloud projects add-iam-policy-binding [PROJECT-NAME] --member user:[USER-EMAIL-ADDRESS] --role roles/editor
OR
gcloud projects add-iam-policy-binding [PROJECT-NAME] --member user:[USER-EMAIL-ADDRESS] --role roles/owner
OR
gcloud projects add-iam-policy-binding [PROJECT-NAME] --member user:[USER-EMAIL-ADDRESS] --role roles/run.admin

# Configuration

Before deploying the function, adjust the properties in Dockerfile:

 - **ALERT_THRESHOLD** - Any query reaching this value will trigger an alert, i.e. `1` means $1.0 USD

 - **TB_COST** - The amount Google charges for 1 Terabyte of data processed by a query ($5 per TB according to https://cloud.google.com/bigquery/pricing#on_demand_pricing)

 - **SLACK_ALERT** - Should Slack alerts be enabled (value can be either `true` or `false`)

 - **SLACK_WEBHOOK_URL** - If slack alerts enabled, alerts will be sent to this URL. Using the following link will help you generate the URL:
https://api.slack.com/incoming-webhooks.

 - **SLACK_WEB_API_TOKEN** - If slack alerts enabled, alerts will be sent via Web API using this token. Using the following link will help you generate the token:
https://api.slack.com/web

 - **SLACK_WEB_API_DESTINATION_CHANNEL** - If slack alert enabled and SLACK_WEB_API_TOKEN is defined, alert will be sent via Web API to this channel

 - **EMAIL_ALERT** - Should email alerts be enabled (value can be either `true` or `false`)

 - **SENDGRID_API_KEY** - API key of your Sendgrid account. Go to https://app.sendgrid.com -> Settings -> API Keys to retrieve your key. If you don't have Sendgrid account, you can sign up for a free edition [here](https://console.cloud.google.com/marketplace/details/sendgrid-app/sendgrid-email).

 - **EMAIL_SENDER** - The email address you want the alert email to be sent from (i.e. `bq-notifier@domain.com`)

 - **EMAIL_RECIPIENTS** - Comma separated list of additional emails to receive the alerts. Alerts will always be sent to the user who has executed the query.
  
 - **EXTERNAL_HANDLER** - Should external handler be invoked (value can be either `true` or `false`)
 
 - **EXTERNAL_HANDLER_URL** - URL of a Post method that will receive the alert details. This feature refers to users that wants to implement their own logic for handling alerts. Following properties will be sent as json in the request body:
 query, job_id, project, location, user_email, total_cost, giga_bytes_billed
 
  
# Deploy Function

To deploy the app to Cloud Run, execute the following commands. Replace the `project_number` with the project number where you deploy the app.

```
export PROJECT_ID=YOUR-PROJECT-ID

gcloud config set project $PROJECT_ID

gcloud builds submit --tag gcr.io/$(gcloud config get-value project)/IMAGE-NAME

gcloud run deploy YOUR-SERVICE-NAME --image gcr.io/$(gcloud config get-value project)/IMAGE-NAME


```

# Creaete trigger
gcloud alpha events triggers create TRIGGER-NAME --target-service YOUR-SERVICE-NAME --type com.google.cloud.auditlog.event --parameters methodName=jobservice.jobcompleted,serviceName=bigquery.googleapis.com

# Change environment variables values
gcloud run services update YOUR-APP-NAME --update-env-vars KEY1=VALUE1,KEY2=VALUE2 

For example:
gcloud run services update bq-snitch --update-env-vars EMAIL_ALERT=true,SLACK_ALERT=false

# Authentication

If the target Cloud Run sink does not allow unauthenticated invocations, Pub/Sub will fail to send the event to the service. 
This issue will be fixed soon, but for now, you can get around the issue by manually enabling authentication on the Pub/Sub subscription. 
The easiest way to do this is to find the generated Pub/Sub subscription in the UI, click “EDIT”, click “Enable authentication”, 
select the default compute service account ([PROJECT-NUM]-compute@developer.gseserviceaccount.com) from the dropdown for “Service account” 
and paste the URL for your target service under “Audience”. Finally, click “update” at the bottom of the page and the Pub/Sub subscription 
should now work as expected.
