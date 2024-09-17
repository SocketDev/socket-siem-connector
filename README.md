# socket-issues-export

## Purpose
This script provides a method to export the alerts from the Socket Health reports into other tools.

This tool supports the following connectors:

- CSV
- Google BigQuery
- Panther SIEM
- Elasticsearch
- WebHook
- Slack

### Other SIEM Integrations

Some SIEM tools have different ways of getting the data into their system.

- Splunk - App found [here](https://splunkbase.splunk.com/app/7158)

## Required Configuration

The connectors supported by this script have some shared configuration in order to pull the data from Socket.

### Options
| Option              | Required | Format           | Description                                                                                                                                 |
|---------------------|----------|------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| api_key             | True     | string           | This is the Socket API Key created in the Socket dashboard. This should have the scoped permissions to access reports                       |
| from_time           | False    | int              | This is the number of seconds to pull reports from. If this is not defined then it will pull the last 30 days of reports.                   |
| report_id           | False    | Socket Report ID | If this is provided then only the specified report ID will be processed                                                                     |
| request_timeout     | False    | int              | This is the number of seconds to wait for an API request to complete before killing it and returning an error. Defaults to 30 seconds       |
| default_branches    | False    | list[str]        | Only required if `default_branch_only` is set to specify the names patterns of default branches like `main` or `master`                     |
| default_branch_only | False    | boolean          | If enabled only reports where the branch name matches what is in `default_branches` will be kept                                            |
| from_time           | False    | int              | Period in seconds to pull reports when not specifying a specific `report_id`. If not set defaults to 30 days                                |
| actions_override    | False    | list[str]        | List of acceptable values to override the security policy configuration of issues to include. I.E. `error`, `warn`, `monitor`, and `ignore` |


### Example

```python
import os
from socketsync.core import Core

if __name__ == '__main__':
    socket_org = os.getenv("SOCKET_ORG") or exit(1)
    api_key = os.getenv("SOCKET_API_KEY") or exit(1)
    start_date = os.getenv("START_DATE")
    core = Core(
        api_key=api_key,
        start_date=start_date,
        report_id=report_id,
        request_timeout=300
    )
    issue_data = core.get_issues()
```


## Examples for each supported connector

### CSV

The CSV Export function will output to a specified CSV file. Currently, it will overwrite the file if it already exists.

Initializing Options:

| Option  | Required | Default     | Description                                                                                                                                         |
|---------|----------|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| file    | True     | None        | The name of the file to write the CSV results out to                                                                                                |
| columns | False    | All Columns | The names of the column headers and the order for the columns. Must match the property names for the issues. If not passed default columns are used |

```python
import os
from socketsync.core import Core
from socketsync.connectors.csv import CSV

if __name__ == '__main__':
    socket_org = os.getenv("SOCKET_ORG") or exit(1)
    api_key = os.getenv("SOCKET_API_KEY") or exit(1)
    start_date = os.getenv("START_DATE")
    report_id = os.getenv("SOCKET_REPORT_ID")
    core = Core(
        api_key=api_key,
        start_date=start_date,
        report_id=report_id
    )
    issue_data = core.get_issues()

    csv_file = "CSV_FILE"
    csv = CSV(
        file=csv_file
    )
    csv.write_csv(issue_data)
```

### Google BigQuery

The BigQuery connector will send data to the specified Table within BigQuery. Currently, in order to be authenticated you will need to do the following before running the code.

1. Install the [GCloud CLI](https://cloud.google.com/sdk/docs/install)
2. In a terminal run `gcloud auth login`
3. In a terminal run `gcloud config set project $MY_PROJECT_ID`

Initializing Options:

| Option | Required | Default | Description                                                                      |
|--------|----------|---------|----------------------------------------------------------------------------------|
| table  | True     | None    | This is the table in the format of `dataset.table` that results will be added to |

```python
import os
from socketsync.core import Core
from socketsync.connectors.bigquery import BigQuery

if __name__ == '__main__':
    socket_org = os.getenv("SOCKET_ORG") or exit(1)
    api_key = os.getenv("SOCKET_API_KEY") or exit(1)
    start_date = os.getenv("START_DATE")
    report_id = os.getenv("SOCKET_REPORT_ID")
    core = Core(
        api_key=api_key,
        start_date=start_date,
        report_id=report_id
    )
    issue_data = core.get_issues()
    bigquery_table = os.getenv('GOOGLE_TABLE') or exit(1)
    bigquery = BigQuery(bigquery_table)
    errors = bigquery.add_dataset(issue_data, streaming=True)
```

### Panther
The Panther connector requires you to have an HTTP connector setup in the Panther UI. In this example I used a bearer token but this can be overriden by using custom headers if desired.

Configuration can be found [here](panther/README.md)

Initializing Options:

| Option  | Required | Default | Description                                                                                           |
|---------|----------|---------|-------------------------------------------------------------------------------------------------------|
| token   | False    | None    | Token to use if you are using Bearer token. Default method if custom headers are not passed to `send` |
| url     | True     | None    | Panther Webhook URL to POST data to                                                                   |
| timeout | False    | 10      | Timeout in seconds for requests                                                                       |

```python
import os
from socketsync.core import Core
from socketsync.connectors.panther import Panther

if __name__ == '__main__':
    socket_org = os.getenv("SOCKET_ORG") or exit(1)
    api_key = os.getenv("SOCKET_API_KEY") or exit(1)
    start_date = os.getenv("START_DATE")
    report_id = os.getenv("SOCKET_REPORT_ID")
    core = Core(
        api_key=api_key,
        start_date=start_date,
        report_id=report_id
    )
    issue_data = core.get_issues()
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
```

### Elasticsearch
The Elasticsearch connector should work with on prem or cloud hosted Elastic search configurations. The configuration when loading `Elastic` is the same as from the [Elasticsearch documentation](https://elasticsearch-py.readthedocs.io/en/v8.11.1/quickstart.html#connecting)

```python
import os
from socketsync.core import Core
from socketsync.connectors.elastic import Elastic

if __name__ == '__main__':
    socket_org = os.getenv("SOCKET_ORG") or exit(1)
    api_key = os.getenv("SOCKET_API_KEY") or exit(1)
    start_date = os.getenv("START_DATE")
    report_id = os.getenv("SOCKET_REPORT_ID")
    core = Core(
        api_key=api_key,
        start_date=start_date,
        report_id=report_id
    )
    issue_data = core.get_issues()
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

### WebHook
The WebHook integration is a simple wrapper for sending an HTTP(s) Request to the desired URL.

Initialize Options:

| Option       | Required | Default                                                                                                        | Description                                                      |
|--------------|----------|----------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| url          | True     | None                                                                                                           | URL for the WebHook                                              |
| headers      | False    | `{'User-Agent': 'SocketPythonScript/0.0.1', "accept": "application/json", 'Content-Type': "application/json"}` | Default set of headers to use if not specified                   |
| auth_headers | False    | None                                                                                                           | Dictionary of auth headers to use to authenticate to the WebHook |
| params       | False    | None                                                                                                           | Dictionary of query params to use if needed                      |
| timeout      | False    | 10                                                                                                             | Time in seconds to timeout out a request                         |

```python
import os
from socketsync.core import Core
from socketsync.connectors.webhook import Webhook

if __name__ == '__main__':
    socket_org = os.getenv("SOCKET_ORG") or exit(1)
    api_key = os.getenv("SOCKET_API_KEY") or exit(1)
    start_date = os.getenv("START_DATE")
    report_id = os.getenv("SOCKET_REPORT_ID")
    core = Core(
        api_key=api_key,
        start_date=start_date,
        report_id=report_id
    )
    issue_data = core.get_issues()
    webhook_url = os.getenv("WEBHOOK_URL") or exit(1)
    webhook_auth_headers = os.getenv("WEBHOOK_AUTH_HEADERS") or {
        'Authorization': 'Bearer EXAMPLE'
    }
    webhook = Webhook(webhook_url)
    for issue in issue_data:
        issue_json = json.loads(str(issue))
        webhook.send(issue_json)
```

### Slack WebHook
The Slack WebHook integration is a simple wrapper for sending an HTTP(s) Request to the desired Slack Webhook URL.

Initialize Options:

| Option       | Required | Default                                                                                                        | Description                                                      |
|--------------|----------|----------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| url          | True     | None                                                                                                           | URL for the WebHook                                              |
| headers      | False    | `{'User-Agent': 'SocketPythonScript/0.0.1', "accept": "application/json", 'Content-Type': "application/json"}` | Default set of headers to use if not specified                   |
| params       | False    | None                                                                                                           | Dictionary of query params to use if needed                      |
| timeout      | False    | 10                                                                                                             | Time in seconds to timeout out a request                         |

```python
import os
from socketsync.core import Core
from socketsync.connectors.slack import Slack

if __name__ == '__main__':
    socket_org = os.getenv("SOCKET_ORG") or exit(1)
    api_key = os.getenv("SOCKET_API_KEY") or exit(1)
    start_date = os.getenv("START_DATE")
    report_id = os.getenv("SOCKET_REPORT_ID")
    core = Core(
        api_key=api_key,
        start_date=start_date,
        report_id=report_id
    )
    issue_data = core.get_issues()
    slack_url = os.getenv("SLACK_WEBHOOK_URL") or exit(1)
    slack = Slack(slack_url)
    for issue in issue_data:
        issue_json = json.loads(str(issue))
        slack.send(issue_json)
```