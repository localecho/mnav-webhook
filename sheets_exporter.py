#!/usr/bin/env python3
"""
Google Sheets Exporter for mNAV Strategy Data
Syncs strategy signals and metrics to Google Sheets for executive dashboards
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Google Sheets API imports (optional - graceful fallback)
try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    logger.warning("Google Sheets API not available. Install with: pip install google-api-python-client google-auth")


class SheetsExporter:
    """
    Export mNAV strategy data to Google Sheets.
    """

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, spreadsheet_id: Optional[str] = None, credentials_path: Optional[str] = None):
        self.spreadsheet_id = spreadsheet_id or os.environ.get('GOOGLE_SHEET_ID')
        self.credentials_path = credentials_path or os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
        self.service = None

        if SHEETS_AVAILABLE and self.credentials_path and self.spreadsheet_id:
            self._init_service()

    def _init_service(self):
        """Initialize Google Sheets service."""
        try:
            # Handle credentials as JSON string or file path
            if self.credentials_path.startswith('{'):
                creds_dict = json.loads(self.credentials_path)
                creds = Credentials.from_service_account_info(creds_dict, scopes=self.SCOPES)
            else:
                creds = Credentials.from_service_account_file(self.credentials_path, scopes=self.SCOPES)

            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("Google Sheets service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Sheets service: {e}")
            self.service = None

    def append_strategy_signal(self, signal_data: Dict) -> bool:
        """
        Append strategy signal to the Strategy Log tab.
        """
        if not self.service:
            logger.warning("Sheets service not available, storing locally")
            return self._store_locally(signal_data)

        try:
            # Format row data
            row = [
                signal_data.get('timestamp', datetime.utcnow().isoformat()),
                signal_data.get('current_mnav', 0),
                signal_data.get('signal', 'NEUTRAL'),
                signal_data.get('score', 0),
                signal_data.get('confidence', 0),
                len(signal_data.get('leading_indicators', [])),
                len(signal_data.get('lagging_indicators', [])),
                signal_data.get('recommendation', '')
            ]

            body = {'values': [row]}

            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='Strategy Log!A:H',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

            logger.info("Strategy signal appended to Sheets")
            return True

        except Exception as e:
            logger.error(f"Failed to append to Sheets: {e}")
            return self._store_locally(signal_data)

    def update_dashboard(self, signal_data: Dict, mnav_data: Dict) -> bool:
        """
        Update the executive dashboard tab with current metrics.
        """
        if not self.service:
            return False

        try:
            # Dashboard data layout (assumes specific cell positions)
            updates = [
                # Current metrics
                {'range': 'Dashboard!B2', 'values': [[signal_data.get('current_mnav', 0)]]},
                {'range': 'Dashboard!B3', 'values': [[signal_data.get('signal', 'NEUTRAL')]]},
                {'range': 'Dashboard!B4', 'values': [[signal_data.get('score', 0)]]},
                {'range': 'Dashboard!B5', 'values': [[f"{signal_data.get('confidence', 0)}%"]]},

                # mNAV metrics from mnav_data
                {'range': 'Dashboard!B7', 'values': [[mnav_data.get('btc_price', 0)]]},
                {'range': 'Dashboard!B8', 'values': [[mnav_data.get('stock_price', 0)]]},
                {'range': 'Dashboard!B9', 'values': [[mnav_data.get('btc_holdings', 0)]]},
                {'range': 'Dashboard!B10', 'values': [[mnav_data.get('market_cap', 0)]]},

                # Timestamp
                {'range': 'Dashboard!B12', 'values': [[datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')]]},
            ]

            body = {'data': updates, 'valueInputOption': 'USER_ENTERED'}

            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()

            logger.info("Dashboard updated")
            return True

        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")
            return False

    def append_indicator_snapshot(self, signal_data: Dict) -> bool:
        """
        Append detailed indicator snapshot to Indicators tab.
        """
        if not self.service:
            return False

        try:
            timestamp = signal_data.get('timestamp', datetime.utcnow().isoformat())

            rows = []

            # Leading indicators
            for ind in signal_data.get('leading_indicators', []):
                rows.append([
                    timestamp,
                    'LEADING',
                    ind.get('name', ''),
                    ind.get('value', ''),
                    ind.get('signal', ''),
                    ind.get('description', '')
                ])

            # Lagging indicators
            for ind in signal_data.get('lagging_indicators', []):
                rows.append([
                    timestamp,
                    'LAGGING',
                    ind.get('name', ''),
                    ind.get('value', ''),
                    ind.get('signal', ''),
                    ind.get('description', '')
                ])

            if rows:
                body = {'values': rows}
                self.service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range='Indicators!A:F',
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()

            return True

        except Exception as e:
            logger.error(f"Failed to append indicators: {e}")
            return False

    def _store_locally(self, data: Dict) -> bool:
        """
        Fallback: store data locally when Sheets unavailable.
        """
        try:
            local_file = '/tmp/mnav_strategy_log.jsonl'
            with open(local_file, 'a') as f:
                f.write(json.dumps(data) + '\n')
            logger.info(f"Data stored locally: {local_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to store locally: {e}")
            return False

    def create_dashboard_template(self) -> bool:
        """
        Create the dashboard template structure if it doesn't exist.
        """
        if not self.service:
            return False

        try:
            # Check if sheets exist, create if not
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()

            existing_sheets = [s['properties']['title'] for s in spreadsheet['sheets']]

            sheets_to_create = []
            if 'Dashboard' not in existing_sheets:
                sheets_to_create.append({'properties': {'title': 'Dashboard'}})
            if 'Strategy Log' not in existing_sheets:
                sheets_to_create.append({'properties': {'title': 'Strategy Log'}})
            if 'Indicators' not in existing_sheets:
                sheets_to_create.append({'properties': {'title': 'Indicators'}})

            if sheets_to_create:
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': [{'addSheet': sheet} for sheet in sheets_to_create]}
                ).execute()

            # Set up headers
            headers = {
                'Dashboard!A1:B1': [['Metric', 'Value']],
                'Dashboard!A2:A12': [
                    ['Current mNAV'],
                    ['Signal'],
                    ['Score'],
                    ['Confidence'],
                    [''],
                    ['BTC Price'],
                    ['MSTR Price'],
                    ['BTC Holdings'],
                    ['Market Cap'],
                    [''],
                    ['Last Updated']
                ],
                'Strategy Log!A1:H1': [[
                    'Timestamp', 'mNAV', 'Signal', 'Score',
                    'Confidence', 'Leading Count', 'Lagging Count', 'Recommendation'
                ]],
                'Indicators!A1:F1': [[
                    'Timestamp', 'Type', 'Name', 'Value', 'Signal', 'Description'
                ]]
            }

            for range_name, values in headers.items():
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    body={'values': values}
                ).execute()

            logger.info("Dashboard template created")
            return True

        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            return False


# Global exporter instance
sheets_exporter = SheetsExporter()


def export_to_sheets(signal_data: Dict, mnav_data: Optional[Dict] = None) -> Dict:
    """
    Main entry point for exporting to Google Sheets.
    """
    results = {
        'signal_logged': sheets_exporter.append_strategy_signal(signal_data),
        'indicators_logged': sheets_exporter.append_indicator_snapshot(signal_data),
        'dashboard_updated': False
    }

    if mnav_data:
        results['dashboard_updated'] = sheets_exporter.update_dashboard(signal_data, mnav_data)

    return results
