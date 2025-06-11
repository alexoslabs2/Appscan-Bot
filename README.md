# Appscan Bot

AppScanBot was developed with the objective of discovering vulnerabilities in web applications exposed to the internet, in an easy and scalable manner.

The application was designed for use on Slack.

### Requirements

* OWASP ZAP

Download OWASP Zap - https://github.com/zaproxy/zaproxy/releases/download/v2.16.1/ZAP_2_16_1_unix.sh

$ sudo apt install openjdk-17-jre

$ pip install slack_sdk flask requests --break-system-packages  # For Debian 12

$ wget https://github.com/zaproxy/zaproxy/releases/download/v2.16.1/ZAP_2_16_1_unix.sh

$ sudo bash ZAP_2_16_1_unix.sh


Start OWASP ZAP

zap.sh -daemon -config api.key=<API_KEY>

Example:
zap.sh -daemon -config api.key=5e9fcd63-407a-4f6c-9b18-310ac44b3779

* Configure Slack
  
Access Your Apps

Click on Create New App → From scratch

Enter the app name and select your workspace

Click Create App

Go to OAuth & Permissions and add the following scopes:

chat:write

commands

Install the app in your workspace under the OAuth Tokens section

Copy the Bot User OAuth Token and insert it into the integration script

* Configure the Integration Script

Edit the script to insert:

Your Slack Bot Token

Your OWASP ZAP API Key

Execute the script:

python3 your_script_name.py

Configure Event Subscriptions

In your Slack App settings:

Go to Event Subscriptions

Enable events and set the URL where your integration script is hosted

* Final Steps

Add the bot to the desired Slack channel

Run a scan using the command:
@bot scan http://example.com
