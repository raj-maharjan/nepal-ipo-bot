import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet_data(sheet_name="Sheet1"):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("meroshare credentials").worksheet(sheet_name)
    
    # Get all values as strings to preserve leading zeros
    all_values = sheet.get_all_values()
    
    if not all_values:
        return []
    
    # First row contains headers
    headers = all_values[0]
    data_rows = all_values[1:]
    
    # Convert to list of dictionaries while preserving string format
    records = []
    for row in data_rows:
        # Pad row to match header length
        while len(row) < len(headers):
            row.append("")
        
        # Create dictionary with headers as keys
        record = {}
        for i, header in enumerate(headers):
            value = row[i] if i < len(row) else ""
            # Preserve string format for all values
            record[header] = str(value) if value else ""
        
        records.append(record)
    
    return records
