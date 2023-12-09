# socket-issues-export

## Purpose
This script provides a method to export the alerts from the Socket Health reports into other tools.

This tool supports the following connectors:

- CSV
- Google BigQuery
- Panther SIEM
- Elasticsearch

### Other SIEM Integrations

Some SIEM tools have different ways of getting the data into their system.

- Splunk - App found [here](https://splunkbase.splunk.com/app/7158)

## Required Configuration

The connectors supported by this script have some shared configuration in order to pull the data from Socket.

### Options
| Option     | Required | Format               | Description                                                                                                                                                             |
|------------|----------|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| org        | True     | string               | This is the Socket org as in the URL of the Socket Dashboard. Generally this should match your Github Org name                                                          |
| api_key    | True     | string               | This is the Socket API Key created in the Socket dashboard. This should have the scoped permissions to access reports                                                   |
| start_date | False    | string(`YYYY-MM-DD`) | If this is not defined then it will pull all reports and their corresponding issues. If defined only reports that match or are newer than the start_date will be pulled |



### Example
```python
import os
from core.socket_reports import Reports


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
```


## Examples for each supported connector

### CSV

The CSV Export function will output to a specified CSV file. Currently, it will overwrite the file if it already exists. 

```python
import os
from core.socket_reports import Reports
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

    csv_file = "CSV_FILE"
    csv = SocketCSV(
        file=csv_file
    )
    csv.write_csv(issue_data)
```

### Google BigQuery

The BigQuery connector will send data to the specified Table within BigQuery. Currently, in order to be authenticated you will need to do the following before running the code.

1. Install the [GCloud CLI](https://cloud.google.com/sdk/docs/install)
2. In a terminal run `gcloud auth login`
3. In a terminal run `gcloud config set project $MY_PROJECT_ID`

```python
import os
from core.socket_reports import Reports
from core.connectors.bigquery import BigQuery



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
    bigquery_table = os.getenv('GOOGLE_TABLE') or exit(1)
    bigquery = BigQuery(bigquery_table)
    errors = bigquery.add_dataset(issue_data, streaming=True)
```

### Panther
The Panther connector requires you to have an HTTP connector setup in the Panther UI. In this example I used a bearer token but this can be overriden by using custom headers if desired.

Configuration can be found [here](panther/README.md)

```python
import os
from core.socket_reports import Reports
from core.connectors.panther import Panther


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
```

### Elasticsearch
The Elasticsearch connector should work with on prem or cloud hosted Elastic search configurations. The configuration when loading `Elastic` is the same as from the [Elasticsearch documentation](https://elasticsearch-py.readthedocs.io/en/v8.11.1/quickstart.html#connecting)

```python
import os
from core.socket_reports import Reports
from core.connectors.elastic import Elastic


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
    elastic_token = os.getenv('ELASTIC_TOKEN') or exit(1)
    elastic_cloud_id = os.getenv('ELASTIC_CLOUD_ID') or exit(1)
    elastic_index = os.getenv('ELASTIC_ID') or exit(1)
    es = Elastic(
        api_key=elastic_token,
        cloud_id=elastic_cloud_id
    )
    for issue in issue_data:
        es.add_document(issue, elastic_index)
```
