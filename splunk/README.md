# Socket Splunk App

The Socket Splunk App has configurable inputs that will run on an interval and pull alerts from the Socket API.

## Installing

1. Log into your Splunk Instance (Where you want the data collection and searching to happen)
2. Go to Manage Apps
3. Browse more apps
4. Search for `socket.dev`
5. Install the App

## Configuration

### General Add-on settings

1. Login to the Splunk Instance where the socket.dev app is installed
2. Go to the socket.dev app
3. Go to configuration
4. Go to Add-on Settings
5. Enter your Socket API Key that you created in the socket.dev dashboard
6. Enter your Socket org name
    Note: You can find the org name after `gh` or `dummy` in the url like `socketdev-demo` is the org name in this url: https://socket.dev/dashboard/org/gh/socketdev-demo
7. Click Save

### Data Input Configuration

1. Login to the Splunk Instance where the socket.dev app is installed
2. Go to the socket.dev app
3. Go to configuration
4. Go to Inputs
5. Select `Create new Input`
6. Give it a Name
7. Set the interval to 300
8. Select the index you would like to use
9. Start Date is optional in the format of YYYY-MM-DD. If not specified it will be all reports. 