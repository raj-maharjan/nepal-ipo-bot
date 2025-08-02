# Floorsheet Data Fetcher

This script fetches floorsheet data from the Chukul API for a given date range and stores it in a PostgreSQL database.

## Features

- Fetches floorsheet data from Chukul API for specified date ranges
- Handles pagination automatically to fetch all available data
- Stores data in PostgreSQL database with proper schema
- Comprehensive logging for monitoring and debugging
- Error handling and retry logic
- Bulk insert for better performance

## Prerequisites

1. **PostgreSQL Database**: Make sure you have PostgreSQL installed and running
2. **Python Dependencies**: Install required packages

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your database configuration by creating a `.env` file:
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=floorsheet_db
DB_USER=postgres
DB_PASSWORD=your_password_here
```

## Database Setup

The script will automatically create the `floorsheet` table if it doesn't exist. The table schema is:

```sql
CREATE TABLE floorsheet (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    transaction VARCHAR(20) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    buyer VARCHAR(10) NOT NULL,
    seller VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    rate NUMERIC(10, 2) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    date DATE NOT NULL
);
```

## Usage

### Basic Usage

Fetch floorsheet data for a specific date range:

```bash
python floorsheet_fetcher.py --start-date 2024-01-01 --end-date 2024-01-02
```

### Examples

1. **Fetch data for a single day:**
```bash
python floorsheet_fetcher.py --start-date 2024-01-01 --end-date 2024-01-01
```

2. **Fetch data for a week:**
```bash
python floorsheet_fetcher.py --start-date 2024-01-01 --end-date 2024-01-07
```

3. **Fetch data for a month:**
```bash
python floorsheet_fetcher.py --start-date 2024-01-01 --end-date 2024-01-31
```

## API Details

The script calls the Chukul API endpoint:
```
https://chukul.com/api/data/v2/floorsheet/bydate/?date={date}&page={page}&size=500
```

### Response Format

The API returns data in the following format:
```json
{
  "data": [
    {
      "transaction": "2024010103010592",
      "symbol": "SIFC",
      "buyer": "49",
      "seller": "49",
      "quantity": 500,
      "rate": 360,
      "amount": 180000
    }
  ],
  "last_page": 206
}
```

## Features

### Pagination Handling
- Automatically detects the `last_page` property from API responses
- Fetches all pages for each date to ensure complete data collection
- Includes small delays between requests to be respectful to the API

### Error Handling
- Comprehensive error handling for API requests
- Database connection error handling
- Continues processing remaining dates even if one date fails
- Detailed logging for troubleshooting

### Performance
- Bulk insert operations for better database performance
- Connection pooling and proper resource management
- Progress logging to monitor data collection

## Logging

The script provides detailed logging:

- **Console Output**: Real-time progress updates
- **Log File**: Detailed logs saved to `floorsheet_fetcher.log`
- **Log Levels**: INFO, WARNING, ERROR for different types of messages

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check database credentials in `.env` file
   - Ensure database exists

2. **API Request Errors**
   - Check internet connectivity
   - Verify API endpoint is accessible
   - Check if API requires authentication

3. **Date Format Errors**
   - Ensure dates are in YYYY-MM-DD format
   - Start date should not be after end date

### Debug Mode

To enable more detailed logging, modify the logging level in the script:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Data Integrity

- Uses `ON CONFLICT (transaction) DO NOTHING` to prevent duplicate records
- Validates data before insertion
- Proper transaction handling with rollback on errors

## Performance Considerations

- Processes one date at a time to avoid overwhelming the API
- Includes small delays between requests
- Uses bulk insert for better database performance
- Proper connection management to avoid resource leaks 