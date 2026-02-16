"""
Date utility functions for Pokemon Sleep Strength Recorder
"""

import sys
import io

from datetime import date, timedelta


def calculate_row_number(target_date):
    """
    Calculate spreadsheet row number from date

    Args:
        target_date: date object

    Returns:
        int or None
    """
    # Base: 2026/2/1 (Sun) = H1152
    base_date = date(2026, 2, 1)
    base_row = 1152

    if target_date < base_date:
        return None

    # Calculate row by iterating through dates
    current_date = base_date
    current_row = base_row

    while current_date < target_date:
        next_date = current_date + timedelta(days=1)

        # Sunday to Monday: +3, otherwise: +1
        if current_date.weekday() == 6 and next_date.weekday() == 0:
            current_row += 3
        else:
            current_row += 1

        current_date = next_date

    return current_row
