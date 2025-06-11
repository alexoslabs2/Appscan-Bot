import os
import time
import re
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Replace with your Slack token and ZAP details
SLACK_BOT_TOKEN = ''
ZAP_API_URL = 'http://localhost:8080'  # ZAP Proxy URL
ZAP_API_KEY = ''  # ZAP Proxy API Key
ZAP_REPORT_DIR = '/home/alexos'  # Directory where the HTML report will be saved

client = WebClient(token=SLACK_BOT_TOKEN)
processed_events = set()

@app.route('/slack/events', methods=['POST'])
def slack_events():
    data = request.json
    if 'challenge' in data:
        return jsonify({'challenge': data['challenge']})

    if 'event' in data:
        event = data['event']
        event_id = data.get('event_id')  # Each event has a unique ID

        # Checks if the event has already been processed
        if event_id in processed_events:
            return '', 501

        # Adds the event to the set of processed events
        processed_events.add(event_id)

        if event.get('type') == 'app_mention':
            handle_mention(event)

    return '', 200


def handle_mention(event):
    text = event.get('text')
    channel_id = event.get('channel')

    if 'scan' in text.lower():
        url_to_scan = text.split('scan')[-1].strip()
        if url_to_scan:
            # Starts the spider on the URL
            spider_result = start_zap_spider(url_to_scan)
            send_message(channel_id, f'Spider started for {url_to_scan}. Spider ID: {spider_result}')

            # Waits for the spider to finish
            wait_for_spider_completion(spider_result)
            send_message(channel_id, 'Spider completed. Starting vulnerability scan...')

            # Starts the vulnerability scan
            scan_result = start_zap_scan(url_to_scan)
            send_message(channel_id, f'Vulnerability scan started. Scan ID: {scan_result}')

            # Waits for the scan to complete
            wait_for_scan_completion(scan_result)
            send_message(channel_id, 'Scan completed. Generating report...')

            # Generates the HTML report with the scanned URL name
            report_file_path = generate_html_report(url_to_scan)

            # Sends the HTML report as an attachment in Slack
            send_html_report(channel_id, report_file_path)
            remove_all_zap_sites()
        else:
            send_message(channel_id, "Please provide a valid URL for the scan, e.g., @bot scan http://example.com")
    else:
        send_message(channel_id, "Please provide a URL to perform spider and scan, e.g., @bot scan http://example.com")

def send_message(channel, text):
    try:
        client.chat_postMessage(channel=channel, text=text)
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

def start_zap_spider(url):
    spider_url = f'{ZAP_API_URL}/JSON/spider/action/scan/?apikey={ZAP_API_KEY}&url={url}'
    response = requests.get(spider_url)
    return response.json().get('scan')

def wait_for_spider_completion(scan_id):
    while True:
        status_url = f'{ZAP_API_URL}/JSON/spider/view/status/?apikey={ZAP_API_KEY}&scanId={scan_id}'
        status_response = requests.get(status_url)
        status = int(status_response.json().get('status'))

        if status >= 100:
            break
        time.sleep(5)  # Waits 5 seconds before checking again

def start_zap_scan(url):
    scan_url = f'{ZAP_API_URL}/JSON/ascan/action/scan/?apikey={ZAP_API_KEY}&url={url}'
    response = requests.get(scan_url)
    return response.json().get('scan')

def wait_for_scan_completion(scan_id):
    while True:
        status_url = f'{ZAP_API_URL}/JSON/ascan/view/status/?apikey={ZAP_API_KEY}&scanId={scan_id}'
        status_response = requests.get(status_url)
        status = int(status_response.json().get('status'))

        if status >= 100:
            break
        time.sleep(5)  # Waits 5 seconds before checking again

def generate_html_report(url):
    report_url = f'{ZAP_API_URL}/OTHER/core/other/htmlreport/?apikey={ZAP_API_KEY}'
    response = requests.get(report_url)

    report_file_path = os.path.join(ZAP_REPORT_DIR, f'zap_report_{int(time.time())}.html')

    # Saves the report to the generated file
    with open(report_file_path, 'w') as report_file:
        report_file.write(response.text)

    return report_file_path

def send_html_report(channel, file_path):
    try:
        with open(file_path, 'rb') as file_content:
            client.files_upload_v2(
                channels=channel,
                file=file_content,
                filename=os.path.basename(file_path),
                title="Vulnerability Report"
            )
    except SlackApiError as e:
        print(f"Error sending the report: {e.response['error']}")

def remove_all_zap_sites():
    # Gets the list of all OWASP ZAP sites
    sites_url = f'{ZAP_API_URL}/JSON/core/view/sites/?apikey={ZAP_API_KEY}'
    response = requests.get(sites_url)
    sites = response.json().get('sites', [])

    # Removes all sites from the OWASP ZAP site list
    for site in sites:
        remove_url = f'{ZAP_API_URL}/JSON/core/action/deleteSiteNode/?apikey={ZAP_API_KEY}&url={site}'
        remove_response = requests.get(remove_url)
        if remove_response.status_code == 200:
            print(f"Site {site} successfully removed.")
        else:
            print(f"Error removing site {site}: {remove_response.text}")

if __name__ == '__main__':
    if not os.path.exists(ZAP_REPORT_DIR):
        os.makedirs(ZAP_REPORT_DIR)
    app.run(host='0.0.0.0', port=3000)
