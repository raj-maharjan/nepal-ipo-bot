import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet_data(sheet_name="Sheet1"):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("meroshare credentials").worksheet(sheet_name)
    return sheet.get_all_records()
