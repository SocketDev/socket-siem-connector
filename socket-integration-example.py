import json
import os
from core.socket_reports import Reports
from core.connectors.elastic import Elastic
from core.connectors.bigquery import BigQuery
from core.connectors.panther import Panther
from core.connectors.socket_csv import SocketCSV


if __name__ == '__main__':
    socket_org = os.getenv("SOCKET_ORG") or exit(1)
    api_key = os.getenv("SOCKET_API_KEY") or exit(1)
    start_date = os.getenv("START_DATE") or exit(1)
    reports = Reports(
        org=socket_org,
        api_key=api_key,
        start_date=start_date
    )
    issue_data = reports.get_issues()

    # CSV Example
    csv_file = "CSV_FILE"
    csv = SocketCSV(
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
        panther.send_to_webhook(str(issue))
        print(f"Processed issue id: {issue.id}")
