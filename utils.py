"""Utility functions for portfolio calculations and data fetching."""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache for storing prices during session
price_cache = {}
historical_cache = {}


def get_current_price(ticker: str) -> Optional[float]:
    """
    Get current price from Yahoo Finance.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Current price or None if error
    """
    cache_key = f"{ticker}_current"

    # Check cache (valid for 5 minutes)
    if cache_key in price_cache:
        cached_time, cached_price = price_cache[cache_key]
        if datetime.now() - cached_time < timedelta(minutes=5):
            return cached_price

    try:
        stock = yf.Ticker(ticker)

        # Try fast_info first (faster and more reliable in yfinance 1.1.0+)
        try:
            current_price = stock.fast_info.get('lastPrice')
            if current_price and current_price > 0:
                price_cache[cache_key] = (datetime.now(), current_price)
                return float(current_price)
        except Exception:
            pass

        # Fallback to history
        data = stock.history(period='1d')
        if data.empty:
            logger.warning(f"No data returned for ticker: {ticker}")
            return None

        current_price = data['Close'].iloc[-1]
        price_cache[cache_key] = (datetime.now(), current_price)
        return float(current_price)

    except Exception as e:
        logger.error(f"Error fetching current price for {ticker}: {str(e)}")
        return None


def get_historical_prices(ticker: str, start_date: str, end_date: str = None) -> pd.DataFrame:
    """
    Get historical prices from Yahoo Finance.

    Args:
        ticker: Stock ticker symbol
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format (default: today)

    Returns:
        DataFrame with historical prices or empty DataFrame if error
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    cache_key = f"{ticker}_{start_date}_{end_date}"

    # Check cache
    if cache_key in historical_cache:
        return historical_cache[cache_key]

    try:
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=end_date)

        if data.empty:
            logger.warning(f"No historical data for {ticker} from {start_date} to {end_date}")
            return pd.DataFrame()

        historical_cache[cache_key] = data
        return data

    except Exception as e:
        logger.error(f"Error fetching historical prices for {ticker}: {str(e)}")
        return pd.DataFrame()


def validate_ticker(ticker: str) -> bool:
    """
    Validate if ticker exists in Yahoo Finance.

    Args:
        ticker: Stock ticker symbol

    Returns:
        True if ticker is valid, False otherwise
    """
    try:
        stock = yf.Ticker(ticker)

        # Try to get recent history - most reliable method
        data = stock.history(period='5d')
        if not data.empty and len(data) > 0:
            return True

        # Try fast_info as fallback
        try:
            last_price = stock.fast_info.get('lastPrice')
            if last_price and last_price > 0:
                return True
        except Exception:
            pass

        # If no price data available, ticker is invalid or delisted
        return False

    except Exception as e:
        logger.error(f"Error validating ticker {ticker}: {str(e)}")
        return False


def calculate_portfolio_evolution(transactions: List[Dict]) -> Dict:
    """
    Calculate portfolio value evolution over time.

    Args:
        transactions: List of transaction dictionaries

    Returns:
        Dictionary with dates and portfolio values
    """
    if not transactions:
        return {'dates': [], 'values': []}

    # Convert transactions to DataFrame
    df = pd.DataFrame(transactions)
    df['purchase_date'] = pd.to_datetime(df['purchase_date'])
    df = df.sort_values('purchase_date')

    # Get date range
    start_date = df['purchase_date'].min()
    end_date = datetime.now()

    # Create date range (daily)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    # For large date ranges, sample weekly to improve performance
    if len(date_range) > 180:  # More than 6 months
        date_range = pd.date_range(start=start_date, end=end_date, freq='W')

    portfolio_values = []
    dates_list = []

    for current_date in date_range:
        # Get all transactions up to this date
        active_transactions = df[df['purchase_date'] <= current_date]

        if active_transactions.empty:
            continue

        # Group by ticker to get positions
        positions = active_transactions.groupby('ticker').agg({
            'quantity': 'sum',
            'purchase_price': 'first'  # We'll recalculate if needed
        }).reset_index()

        # Calculate portfolio value for this date
        total_value = 0
        all_prices_available = True

        for _, position in positions.iterrows():
            ticker = position['ticker']
            quantity = position['quantity']

            # Get historical price for this date
            hist_data = get_historical_prices(
                ticker,
                current_date.strftime('%Y-%m-%d'),
                (current_date + timedelta(days=5)).strftime('%Y-%m-%d')  # Add buffer for weekends
            )

            if not hist_data.empty:
                # Get the closest available price
                price = hist_data['Close'].iloc[0]
                total_value += quantity * price
            else:
                all_prices_available = False
                break

        if all_prices_available:
            dates_list.append(current_date.strftime('%Y-%m-%d'))
            portfolio_values.append(round(total_value, 2))

    return {
        'dates': dates_list,
        'values': portfolio_values
    }


def calculate_weighted_average_price(transactions: List[Dict]) -> float:
    """
    Calculate weighted average purchase price.

    Args:
        transactions: List of transaction dictionaries for same ticker

    Returns:
        Weighted average price
    """
    total_cost = sum(t['purchase_price'] * t['quantity'] for t in transactions)
    total_quantity = sum(t['quantity'] for t in transactions)

    if total_quantity == 0:
        return 0.0

    return total_cost / total_quantity


def format_currency(value: float) -> str:
    """Format value as currency."""
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.2f}%"


def calculate_gain_loss(invested: float, current: float) -> tuple:
    """
    Calculate gain/loss in dollars and percentage.

    Args:
        invested: Total amount invested
        current: Current value

    Returns:
        Tuple of (gain_loss_dollar, gain_loss_percent)
    """
    gain_loss_dollar = current - invested

    if invested == 0:
        gain_loss_percent = 0.0
    else:
        gain_loss_percent = (gain_loss_dollar / invested) * 100

    return gain_loss_dollar, gain_loss_percent
