# IPO Bot

A FastAPI-based bot that automates IPO applications for users via Telegram. It integrates with the CDSC MeroShare API and Google Sheets for user data management, and supports fuzzy keyword search for company names.

## Features

- **Telegram Bot Integration:** Users can apply for IPOs by sending Telegram messages to the bot.
- **CDSC MeroShare API Integration:** Automated login and IPO application.
- **Google Sheets Integration:** User data management and storage.
- **Fuzzy Keyword Search:** Intelligent company name matching.
- **Flexible Message Parsing:** Supports various Telegram message formats, including kitta (share quantity) extraction.
- **Error Handling:** Comprehensive error handling and user feedback.
- **Multi-User Support:** Handles multiple users with different credentials.

## Prerequisites

- Python 3.8+
- Telegram Bot Token
- Google Sheets API credentials
- CDSC MeroShare account credentials
- Google Sheets account

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ipo-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in a `.env` file:
```bash
# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/credentials.json
SPREADSHEET_ID=your_spreadsheet_id

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# CDSC API (optional, for direct testing)
CDSC_USERNAME=your_cdsc_username
CDSC_PASSWORD=your_cdsc_password
CDSC_CLIENT_ID=your_cdsc_client_id
```

4. Set up Google Sheets:
   - Create a Google Sheet with user data
   - Share it with the service account email
   - Update the `SPREADSHEET_ID` in your `.env` file

5. Set up Telegram Bot:
   - Create a bot via [@BotFather](https://t.me/botfather)
   - Get the bot token and add it to your `.env` file
   - Set up webhook to point to your server's `/webhook` endpoint

6. Run the application:
```bash
python main.py
```

## Usage

### Telegram Bot Commands

Users can interact with the bot by sending messages in the following format:

```
[person] [company] [kitta]
```

Examples:
- `john abc 10` - Apply for ABC company with 10 kitta for John
- `jane xyz 5` - Apply for XYZ company with 5 kitta for Jane

The bot will:
1. Parse the message to extract person, company, and kitta
2. Find the user in the Google Sheet
3. Login to CDSC using the user's credentials
4. Search for applicable IPO issues
5. Apply for the IPO if found
6. Send feedback via Telegram

### API Endpoints

- `POST /webhook` - Telegram bot webhook endpoint
- `POST /apply` - Apply for all IPOs for a specific user (used by GitHub Actions)
- `GET /apply/{user_name}` - Apply for all IPOs for a specific user (GET version)

## File Structure

- `main.py` - FastAPI app, webhook, Telegram bot integration
- `api.py` - CDSC API integration functions
- `sheets.py` - Google Sheets integration
- `parser.py` - Message parsing and fuzzy search logic
- `requirements.txt` - Python dependencies

## Telegram Bot Setup

1. Create a bot via [@BotFather](https://t.me/botfather):
   - Send `/newbot` to @BotFather
   - Choose a name for your bot
   - Choose a username (must end with 'bot')
   - Copy the bot token

2. Set up webhook:
   - Deploy your application to a server with HTTPS
   - Set the webhook URL: `https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://your-domain.com/webhook`

3. Test the bot:
   - Send a message to your bot in the format: `[person] [company] [kitta]`
   - The bot should respond with the application status

## Environment Variables

```bash
# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/credentials.json
SPREADSHEET_ID=your_spreadsheet_id

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# CDSC API (optional)
CDSC_USERNAME=your_cdsc_username
CDSC_PASSWORD=your_cdsc_password
CDSC_CLIENT_ID=your_cdsc_client_id
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Resources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [CDSC MeroShare API Documentation](https://meroshare.cdsc.com.np/)
- [Google Sheets API Documentation](https://developers.google.com/sheets/api) 