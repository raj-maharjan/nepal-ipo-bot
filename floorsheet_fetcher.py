#!/usr/bin/env python3
"""
Floorsheet Data Fetcher

This script fetches floorsheet data from the Chukul API for a given date range
and stores it in a PostgreSQL database.

Usage:
    python floorsheet_fetcher.py --start-date 2024-01-01 --end-date 2024-01-02
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import logging
import time
import math

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('floorsheet_fetcher.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class FloorsheetFetcher:
    def __init__(self):
        """Initialize the FloorsheetFetcher with database connection."""
        self.api_base_url = "https://chukul.com/api/data/v2/floorsheet/bydate/"
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'nepse'),
            'user': os.getenv('DB_USER', 'nepse_user'),
            'password': os.getenv('DB_PASSWORD', 'Admin123$'),
        }
        self.conn = None
        self.cursor = None
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def connect_to_database(self):
        """Establish connection to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            logger.info("Successfully connected to PostgreSQL database")
        except psycopg2.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def create_table_if_not_exists(self):
        """Create the floorsheet table if it doesn't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS floorsheet (
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
        """
        try:
            self.cursor.execute(create_table_sql)
            self.conn.commit()
            logger.info("Floorsheet table created/verified successfully")
        except psycopg2.Error as e:
            logger.error(f"Error creating table: {e}")
            raise

    def get_existing_record_count(self, date):
        """
        Get the count of existing records for a specific date.
        
        Args:
            date (str): Date in YYYY-MM-DD format
            
        Returns:
            int: Number of existing records for the date
        """
        try:
            self.cursor.execute(
                "SELECT COUNT(*) FROM floorsheet WHERE date = %s",
                (date,)
            )
            count = self.cursor.fetchone()[0]
            logger.info(f"Existing records for {date}: {count}")
            return count
        except psycopg2.Error as e:
            logger.error(f"Error getting record count for {date}: {e}")
            raise

    def fetch_floorsheet_data_with_retry(self, date, page=1, size=500):
        """
        Fetch floorsheet data for a specific date and page with retry logic.
        
        Args:
            date (str): Date in YYYY-MM-DD format
            page (int): Page number for pagination
            size (int): Number of records per page
            
        Returns:
            dict: API response containing data and last_page
        """
        url = f"{self.api_base_url}?date={date}&page={page}&size={size}"
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching data for date {date}, page {page} (attempt {attempt + 1})")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Successfully fetched {len(data.get('data', []))} records for date {date}, page {page}")
                return data
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for date {date}, page {page}: {e}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    self.retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"All {self.max_retries} attempts failed for date {date}, page {page}")
                    raise
        
        # Reset retry delay for next request
        self.retry_delay = 2

    def estimate_total_records_from_api(self, date):
        """
        Estimate total records for a date by fetching the first page.
        
        Args:
            date (str): Date in YYYY-MM-DD format
            
        Returns:
            tuple: (estimated_total_records, last_page, records_per_page)
        """
        try:
            response = self.fetch_floorsheet_data_with_retry(date, page=1, size=500)
            data = response.get('data', [])
            last_page = response.get('last_page', 1)
            records_per_page = len(data)
            
            # Estimate total records - last page will have fewer than 500 records
            estimated_total = (last_page - 1) * 500 + records_per_page
            
            logger.info(f"Estimated total records for {date}: {estimated_total} (pages: {last_page}, records per page: {records_per_page})")
            return estimated_total, last_page, records_per_page
            
        except Exception as e:
            logger.error(f"Error estimating total records for {date}: {e}")
            raise

    def is_data_complete(self, date):
        """
        Check if data for a date is complete by comparing existing count with estimated total.
        
        Args:
            date (str): Date in YYYY-MM-DD format
            
        Returns:
            tuple: (is_complete, existing_count, estimated_total, missing_pages)
        """
        try:
            existing_count = self.get_existing_record_count(date)
            estimated_total, last_page, records_per_page = self.estimate_total_records_from_api(date)
            
            # Check if data is complete using the 500 records per page logic
            # If existing_count is exactly divisible by 500, it's likely incomplete
            # If existing_count is not divisible by 500, it's likely complete (last page has fewer records)
            is_exactly_divisible_by_500 = existing_count % 500 == 0
            is_complete = not is_exactly_divisible_by_500 and existing_count > 0
            
            # Calculate missing pages if data is incomplete
            missing_pages = []
            if not is_complete:
                # Calculate which pages we have data for
                pages_with_data = existing_count // 500
                missing_pages = list(range(pages_with_data + 1, last_page + 1))
                logger.info(f"Data incomplete for {date}. Existing: {existing_count}, Estimated: {estimated_total}, Missing pages: {missing_pages}")
            else:
                logger.info(f"Data complete for {date}. Existing: {existing_count}, Estimated: {estimated_total}")
            
            return is_complete, existing_count, estimated_total, missing_pages
            
        except Exception as e:
            logger.error(f"Error checking data completeness for {date}: {e}")
            raise

    def insert_floorsheet_data(self, data_list, date):
        """
        Insert floorsheet data into the database.
        
        Args:
            data_list (list): List of floorsheet records
            date (str): Date in YYYY-MM-DD format
        """
        if not data_list:
            logger.warning(f"No data to insert for date {date}")
            return

        # Prepare data for bulk insert
        values = []
        for record in data_list:
            values.append((
                record['transaction'],
                record['symbol'],
                record['buyer'],
                record['seller'],
                record['quantity'],
                record['rate'],
                record['amount'],
                date
            ))

        insert_sql = """
        INSERT INTO floorsheet (transaction, symbol, buyer, seller, quantity, rate, amount, date)
        VALUES %s
        ON CONFLICT (transaction) DO NOTHING
        """

        try:
            execute_values(self.cursor, insert_sql, values)
            self.conn.commit()
            logger.info(f"Successfully inserted {len(values)} records for date {date}")
        except psycopg2.Error as e:
            # Check if it's a unique constraint violation
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                logger.warning(f"Duplicate transaction records detected for date {date}. Continuing with existing data.")
                self.conn.rollback()
                # Continue without raising the exception
            else:
                logger.error(f"Error inserting data for date {date}: {e}")
                self.conn.rollback()
                raise

    def fetch_missing_pages_for_date(self, date, missing_pages):
        """
        Fetch missing pages for a specific date.
        
        Args:
            date (str): Date in YYYY-MM-DD format
            missing_pages (list): List of page numbers to fetch
        """
        total_records = 0
        
        for page in missing_pages:
            try:
                response = self.fetch_floorsheet_data_with_retry(date, page)
                data = response.get('data', [])
                
                if data:
                    self.insert_floorsheet_data(data, date)
                    total_records += len(data)
                
                # Add a small delay to be respectful to the API
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to fetch page {page} for date {date}: {e}")
                # Continue with next page even if current one fails
        
        logger.info(f"Completed fetching {len(missing_pages)} missing pages for date {date}. Total new records: {total_records}")

    def fetch_all_data_for_date(self, date):
        """
        Fetch all floorsheet data for a specific date with completeness check.
        
        Args:
            date (str): Date in YYYY-MM-DD format
        """
        try:
            # Check if data is complete
            is_complete, existing_count, estimated_total, missing_pages = self.is_data_complete(date)
            
            if is_complete:
                logger.info(f"Data for {date} is already complete. Skipping.")
                return
            
            if missing_pages:
                logger.info(f"Fetching {len(missing_pages)} missing pages for {date}")
                self.fetch_missing_pages_for_date(date, missing_pages)
            else:
                # If no existing data, fetch all pages
                logger.info(f"No existing data for {date}. Fetching all pages.")
                response = self.fetch_floorsheet_data_with_retry(date, page=1)
                last_page = response.get('last_page', 1)
                
                # Insert first page data
                data = response.get('data', [])
                if data:
                    self.insert_floorsheet_data(data, date)
                
                # Fetch remaining pages
                for page in range(2, last_page + 1):
                    response = self.fetch_floorsheet_data_with_retry(date, page)
                    data = response.get('data', [])
                    
                    if data:
                        self.insert_floorsheet_data(data, date)
                    
                    # Add a small delay to be respectful to the API
                    time.sleep(0.1)
                
                logger.info(f"Completed fetching all data for date {date}")
            
        except Exception as e:
            logger.error(f"Error fetching all data for date {date}: {e}")
            raise

    def fetch_data_for_date_range(self, start_date, end_date):
        """
        Fetch floorsheet data for a date range.
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
        """
        try:
            # Parse dates
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Validate date range
            if start_dt > end_dt:
                raise ValueError("Start date cannot be after end date")
            
            # Generate date range
            current_dt = start_dt
            total_days = 0
            completed_days = 0
            
            while current_dt <= end_dt:
                current_date = current_dt.strftime('%Y-%m-%d')
                logger.info(f"Processing date: {current_date}")
                
                try:
                    self.fetch_all_data_for_date(current_date)
                    completed_days += 1
                except Exception as e:
                    logger.error(f"Failed to process date {current_date}: {e}")
                    # Continue with next date even if current one fails
                
                total_days += 1
                current_dt += timedelta(days=1)
            
            logger.info(f"Completed processing {completed_days}/{total_days} days from {start_date} to {end_date}")
            
        except Exception as e:
            logger.error(f"Error processing date range: {e}")
            raise

    def close_connection(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")


def main():
    """Main function to run the floorsheet fetcher."""
    parser = argparse.ArgumentParser(description='Fetch floorsheet data for a date range')
    parser.add_argument('--start-date', required=True, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', required=True, help='End date in YYYY-MM-DD format')
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        datetime.strptime(args.start_date, '%Y-%m-%d')
        datetime.strptime(args.end_date, '%Y-%m-%d')
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        sys.exit(1)
    
    fetcher = FloorsheetFetcher()
    
    try:
        # Connect to database
        fetcher.connect_to_database()
        
        # Create table if not exists
        fetcher.create_table_if_not_exists()
        
        # Fetch data for the date range
        fetcher.fetch_data_for_date_range(args.start_date, args.end_date)
        
        logger.info("Floorsheet data fetching completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        sys.exit(1)
    finally:
        fetcher.close_connection()


if __name__ == "__main__":
    main() 