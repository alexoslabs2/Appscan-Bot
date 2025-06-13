from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Flask, request, jsonify
import requests
import re
import time
import os

app = Flask(__name__)

# Replace with your Slack token and ZAP details
# SLACK_BOT_TOKEN = 'xoxb-'
# ZAP_API_URL = 'http://localhost:8080'  # ZAP Proxy URL
# ZAP_API_KEY = ''                      # ZAP API Key
# ZAP_REPORT_DIR = '/tmp/'       # Directory where the HTML report will be stored

client = WebClient(token=SLACK_BOT_TOKEN)
processed_events = set()
session = requests.Session()

@app.route('/slack/events', methods=['POST'])
def slack_events():
    data = request.json
    if 'challenge' in data:
        return jsonify({'challenge': data['challenge']})

    if 'event' in data:
        event = data['event']
        event_id = data.get('event_id')  # Every event has a unique ID

        # Check whether the event has already been processed
        if event_id in processed_events:
            return '', 409

        # Add the event to the set of processed events
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
            # Start the spider for the URL
            spider_result = start_zap_spider(url_to_scan)
            send_message(channel_id, f'Spider started for {url_to_scan}. Spider ID: {spider_result}')

            # Wait for the spider to finish
            wait_for_spider_completion(spider_result)
            send_message(channel_id, 'Spider finished. Starting vulnerability scan...')

            # Start the vulnerability scan
            scan_result = start_zap_scan(url_to_scan)
            send_message(channel_id, f'Vulnerability scan started. Scan ID: {scan_result}')

            # Track the scan until completion
            wait_for_scan_completion(scan_result)
            send_message(channel_id, 'Scan finished. Generating report...')

            # Generate the HTML report
            report_file_path = generate_html_report(url_to_scan)

            # Send the HTML report as an attachment in Slack
            send_html_report(channel_id, report_file_path)
            remove_all_zap_sites()
        else:
            send_message(
                channel_id,
                "Please provide a valid URL to scan, e.g., @bot scan http://example.com"
            )
    else:
        send_message(
            channel_id,
            "Please provide a URL so I can run the spider and scan, e.g., @bot scan http://example.com"
        )


def send_message(channel, text):
    try:
        client.chat_postMessage(channel=channel, text=text)
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")


def start_zap_spider(url):
    spider_url = f'{ZAP_API_URL}/JSON/spider/action/scan/?url={url}'
    response = session.get(spider_url)
    return response.json().get('scan')


def wait_for_spider_completion(scan_id):
    while True:
        status_url = f'{ZAP_API_URL}/JSON/spider/view/status/?scanId={scan_id}'
        status_response = session.get(status_url)
        status = int(status_response.json().get('status'))

        if status >= 100:
            break
        time.sleep(5)  # Wait 5 seconds before checking again


def start_zap_scan(url):
    scan_url = f'{ZAP_API_URL}/JSON/ascan/action/scan/?url={url}'
    response = session.get(scan_url)
    return response.json().get('scan')


def wait_for_scan_completion(scan_id):
    while True:
        status_url = f'{ZAP_API_URL}/JSON/ascan/view/status/?scanId={scan_id}'
        status_response = session.get(status_url)
        status = int(status_response.json().get('status'))

        if status >= 100:
            break
        time.sleep(5)  # Wait 5 seconds before checking again


def generate_html_report(url):
    report_url = f'{ZAP_API_URL}/OTHER/core/other/htmlreport/'
    response = session.get(report_url)

    report_file_path = os.path.join(
        ZAP_REPORT_DIR, f'zap_report_{int(time.time())}.html'
    )
    with open(report_file_path, 'w') as report_file:
        report_file.write(response.text)

    return report_file_path


def send_html_report(channel, file_path):
    try:
        with open(file_path, 'rb') as file_content:
            client.files_upload_v2(
                channel=channel,
                file=file_content,
                filename=os.path.basename(file_path),
                title="Vulnerability Report"
            )
    except SlackApiError as e:
        print(f"Error sending report: {e.response['error']}")


def remove_all_zap_sites():
    # Retrieve all sites registered in OWASP ZAP
    sites_url = f'{ZAP_API_URL}/JSON/core/view/sites/'
    response = session.get(sites_url)
    sites = response.json().get('sites', [])

    # Remove each site from the ZAP site tree
    for site in sites:
        remove_url = f'{ZAP_API_URL}/JSON/core/action/deleteSiteNode/?url={site}'
        remove_response = session.get(remove_url)
        if remove_response.status_code == 200:
            print(f"Site {site} removed successfully.")
        else:
            print(f"Error removing site {site}: {remove_response.text}")


@app.route("/actuator/health", methods=["GET"])
def actuator_health():
    return jsonify({"status": "health"}), 200


if __name__ == '__main__':
    if not os.path.exists(ZAP_REPORT_DIR):
        os.makedirs(ZAP_REPORT_DIR)
    app.run(host='0.0.0.0', port=3000)
