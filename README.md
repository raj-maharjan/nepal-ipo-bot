# Nepal IPO Bot

A FastAPI-based bot that automates IPO applications for users via WhatsApp using Twilio. It integrates with the CDSC MeroShare API and Google Sheets for user data management, and supports fuzzy keyword search for company names.

## Features
- **WhatsApp Integration:** Users can apply for IPOs by sending WhatsApp messages.
- **Telegram Notifications:** Receive detailed notifications about IPO application results via Telegram.
- **Fuzzy Search:** Finds applicable IPO issues using fuzzy matching on company names.
- **Google Sheets Integration:** Reads user credentials and info from a Google Sheet.
- **CDSC API Automation:** Logs in and applies for IPOs automatically.
- **Flexible Message Parsing:** Supports various WhatsApp message formats, including kitta (share quantity) extraction.
- **Detailed Logging & Error Handling:** Provides clear feedback and logs for debugging.

## Requirements
- Python 3.8+
- Twilio account (for WhatsApp API)
- Google Cloud service account (for Sheets API)
- CDSC MeroShare account credentials (stored in Google Sheet)

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/raj-maharjan/nepal-ipo-bot.git
cd nepal-ipo-bot
```

### 2. Create and Activate a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Google Sheets Setup
- Create a Google Cloud project and enable the Google Sheets API.
- Create a service account and download the `service_account.json` key file.
- Share your Google Sheet (e.g., "meroshare credentials") with the service account email.
- Place `service_account.json` in the project root (already in .gitignore).

### 5. Environment Variables
Create a `.env` file in the project root with the following:
```
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### 6. Telegram Setup (Optional)
1. Create a Telegram bot:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Send `/newbot` command
   - Follow the instructions to create your bot
   - Save the bot token provided by BotFather
2. Get your Chat ID:
   - Message your bot or add it to a group
   - Send a message to the bot
   - Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat_id in the response
3. Add the credentials to your `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

### 7. Twilio WhatsApp Setup
1. Sign up or log in to [Twilio](https://www.twilio.com/).
2. Go to the [Twilio Console](https://console.twilio.com/).
3. Get your Account SID and Auth Token.
4. Activate the WhatsApp Sandbox:
   - Go to [Twilio WhatsApp Sandbox](https://www.twilio.com/console/sms/whatsapp/sandbox)
   - Note the sandbox number (e.g., `whatsapp:+14155238886`).
   - Join the sandbox by sending the join code to the number via WhatsApp.
5. Set the sandbox number in your code (already set as `TWILIO_NUMBER` in `main.py`).
6. Set your webhook URL in the Twilio Console to point to your server's `/webhook` endpoint (e.g., `https://your-domain.com/webhook`).

### 8. Run the Bot
```bash
uvicorn main:app --reload
```

## Usage
- Send a WhatsApp message to your Twilio sandbox number in one of the following formats:
  - `apply ipo for john in himstar`
  - `apply ipo for kaka for company himstar 10 kitta`
  - `ipo nene urja`
- The bot will parse the message, find the user and company, and apply for the IPO if possible.
- You will receive WhatsApp feedback for each step (login, issue found, application success/failure).

## Message Format Examples
- `apply ipo for john in himstar`
- `apply ipo for kaka for company himstar 10 kitta`
- `ipo nene urja`
- `apply for sarah company def`

## Project Structure
- `main.py` - FastAPI app, webhook, WhatsApp/Twilio integration
- `api.py` - CDSC API logic (login, get issues, apply IPO)
- `parser.py` - Message parsing and fuzzy matching
- `sheets.py` - Google Sheets integration
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (not committed)
- `service_account.json` - Google service account key (not committed)

## Security Notes
- Never commit your `.env` or `service_account.json` files.
- The bot expects user credentials and info in a Google Sheet named "meroshare credentials".

## References
- [Twilio WhatsApp Sandbox Documentation](https://www.twilio.com/docs/whatsapp/sandbox)
- [CDSC MeroShare](https://meroshare.cdsc.com.np/)
- [Google Sheets API Python Quickstart](https://developers.google.com/sheets/api/quickstart/python)

---

For any issues, open an issue on the [GitHub repo](https://github.com/raj-maharjan/nepal-ipo-bot). 