import json
import os
from socketsync.core import Core
from socketsync.connectors.elastic import Elastic
from socketsync.connectors.bigquery import BigQuery
from socketsync.connectors.panther import Panther
from socketsync.connectors.csv import CSV
from socketsync.connectors.webhook import Webhook
from socketsync.connectors.slack import Slack


if __name__ == '__main__':
    api_key = os.getenv("SOCKET_API_KEY") or exit(1)
    from_time = os.getenv("FROM_TIME") or 300
    default_branches = [
        "master",
        "main"
    ]
    core = Core(
        api_key=api_key,
        from_time=from_time,
        default_branch_only=False
    )
    issue_data = core.get_issues()

    # CSV Example
    csv_file = "example.csv"
    csv = CSV(
        file=csv_file
    )
    csv.write_csv(issue_data)

    # Elasticsearch Example
    elastic_token = os.getenv('ELASTIC_TOKEN') or exit(1)
    elastic_cloud_id = os.getenv('ELASTIC_CLOUD_ID') or exit(1)
    elastic_index = os.getenv('ELASTIC_ID') or exit(1)
    es = Elastic(
        api_key=elastic_token,
        cloud_id=elastic_cloud_id
    )
    for issue in issue_data:
        es.add_document(issue, elastic_index)

    # Big Query Example
    bigquery_table = os.getenv('GOOGLE_TABLE') or exit(1)
    bigquery = BigQuery(bigquery_table)
    errors = bigquery.add_dataset(issue_data, streaming=True)

    # Panther SIEM Integration
    panther_url = os.getenv('PANTHER_URL') or exit(1)
    panther_token = os.getenv('PANTHER_TOKEN') or exit(1)
    panther = Panther(
        token=panther_token,
        url=panther_url
    )
    for issue in issue_data:
        issue_json = json.loads(str(issue))
        panther.send(str(issue))
        print(f"Processed issue id: {issue.id}")

    # Webhook Example
    webhook_url = os.getenv("WEBHOOK_URL") or exit(1)
    webhook_auth_headers = os.getenv("WEBHOOK_AUTH_HEADERS") or {
        'Authorization': 'Bearer EXAMPLE'
    }
    webhook = Webhook(webhook_url)
    for issue in issue_data:
        issue_json = json.loads(str(issue))
        webhook.send(issue_json)

    slack_url = os.getenv("SLACK_WEBHOOK_URL") or exit(1)
    slack = Slack(slack_url)
    for issue in issue_data:
        issue_json = json.loads(str(issue))
        slack.send(issue_json)
