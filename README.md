# AppScan Bot

## Overview

AppScanBot is a Slack-integrated automation solution designed to identify security vulnerabilities in web applications exposed to the internet using OWASP ZAP

---

## Architecture Summary

* **Slack Integration**: Enables triggering scans and receiving reports via Slack messages.
* **Python API Server**: Listens for Slack events, parses commands, and orchestrates scans.
* **OWASP ZAP**: Performs spidering and vulnerability scanning.
* **HTML Report Delivery**: Generates and uploads ZAP scan reports to Slack channels.

```
Slack -> Flask App (Python) -> OWASP ZAP API
```

---

## System Requirements

* Host with:

  * Python 3.11+
  * Expose 3000/tcp port
  * Java Runtime (OpenJDK 17+)
    
* Tools:

  * [OWASP ZAP](https://github.com/zaproxy/zaproxy/releases/download/v2.16.1/ZAP_2_16_1_unix.sh)
  * Slack Bot User OAuth Token

* Dependencies:

  * `slack_sdk`
  * `flask`
  * `requests`

---

## Installation Steps

### 1. Install Dependencies

```bash
sudo apt install openjdk-17-jre
pip install slack_sdk flask requests --break-system-packages
wget https://github.com/zaproxy/zaproxy/releases/download/v2.16.1/ZAP_2_16_1_unix.sh
sudo bash ZAP_2_16_1_unix.sh
```

### 2. Configure Slack Bot

* Go to: [https://api.slack.com/apps](https://api.slack.com/apps)
* Create a new App → From Scratch
* Add OAuth scopes:
  * `chat:write`
  * `commands`

* Install to Workspace and copy the **Bot User OAuth Token**

### 4. Update Python Script

* Insert your **Slack Token** and **ZAP API Key** into the integration script

### 3. Start OWASP ZAP

```bash
zap.sh -daemon -config api.key=<YOUR_API_KEY>
```

### 4. Start Python Scrypt

```python3 appscan.py```

### 5. Set webhook URL under Slack 

* Go to: [https://api.slack.com/apps](https://api.slack.com/apps)
* Access de App created
* Click Event Subscriptions
* Enable Events
* Inform the Request URL
  * ```http://<IP or Domain>:3000/slack/events```
* Add Subscribe to bot events
  * `app_mention'
* Save Configuration
* Reinstall App
  
---

## Usage

### Slack Commands

Send a message in Slack:

```
@bot scan http://yourtarget.com
```

## Demo

![alt-text](https://gifyu.com/image/bxOSA)

## Recommendations for Production

* Harden OWASP ZAP host (TLS, auth headers, firewall rules)
* Store API keys securely (use dotenv or secret managers)
* Monitor and rate-limit Slack bot traffic to avoid abuse
