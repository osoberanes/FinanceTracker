"""Flask application for Portfolio Tracker."""

from flask import Flask, render_template, request, jsonify
from database import init_db, get_db, close_db
from models import Transaction
from utils import (
    get_current_price,
    validate_ticker,
    calculate_portfolio_evolution,
    calculate_weighted_average_price,
    calculate_gain_loss
)
from datetime import datetime
from sqlalchemy import func
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# Initialize database
with app.app_context():
    init_db()


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Close database session after request."""
    close_db()


@app.route('/')
def index():
    """Render main dashboard."""
    return render_template('index.html')


@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """
    Get all transactions with current prices and calculations.

    Returns:
        JSON array of transactions with enriched data
    """
    try:
        db = get_db()
        transactions = db.query(Transaction).order_by(Transaction.purchase_date.desc()).all()

        result = []
        for trans in transactions:
            current_price = get_current_price(trans.ticker)

            # Calculate values
            invested_value = trans.purchase_price * trans.quantity
            current_value = current_price * trans.quantity if current_price else None

            gain_loss_dollar = None
            gain_loss_percent = None

            if current_value is not None:
                gain_loss_dollar, gain_loss_percent = calculate_gain_loss(invested_value, current_value)

            trans_dict = trans.to_dict()
            trans_dict.update({
                'current_price': round(current_price, 2) if current_price else None,
                'invested_value': round(invested_value, 2),
                'current_value': round(current_value, 2) if current_value else None,
                'gain_loss_dollar': round(gain_loss_dollar, 2) if gain_loss_dollar is not None else None,
                'gain_loss_percent': round(gain_loss_percent, 2) if gain_loss_percent is not None else None
            })

            result.append(trans_dict)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/transactions', methods=['POST'])
def create_transaction():
    """
    Create a new transaction.

    Expected JSON body:
        {
            "ticker": "AAPL",
            "purchase_date": "2024-01-15",
            "purchase_price": 150.50,
            "quantity": 10
        }

    Returns:
        JSON with created transaction or error
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['ticker', 'purchase_date', 'purchase_price', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Validate and format ticker
        ticker = data['ticker'].upper().strip()

        # Validate ticker exists
        if not validate_ticker(ticker):
            return jsonify({'error': f'Invalid ticker: {ticker}. Ticker not found in Yahoo Finance.'}), 400

        # Validate date
        try:
            purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
            if purchase_date > datetime.now().date():
                return jsonify({'error': 'Purchase date cannot be in the future'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Validate numeric values
        try:
            purchase_price = float(data['purchase_price'])
            quantity = float(data['quantity'])

            if purchase_price <= 0:
                return jsonify({'error': 'Purchase price must be greater than 0'}), 400
            if quantity <= 0:
                return jsonify({'error': 'Quantity must be greater than 0'}), 400

        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid numeric values'}), 400

        # Create transaction
        db = get_db()
        transaction = Transaction(
            ticker=ticker,
            purchase_date=purchase_date,
            purchase_price=purchase_price,
            quantity=quantity
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        logger.info(f"Transaction created: {ticker} - {quantity} shares at ${purchase_price}")

        return jsonify({
            'message': 'Transaction created successfully',
            'transaction': transaction.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        db.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/summary', methods=['GET'])
def get_portfolio_summary():
    """
    Get consolidated portfolio summary grouped by ticker.

    Returns:
        JSON with portfolio positions and totals
    """
    try:
        db = get_db()
        transactions = db.query(Transaction).all()

        if not transactions:
            return jsonify({
                'positions': [],
                'totals': {
                    'total_invested': 0,
                    'total_current_value': 0,
                    'total_gain_loss_dollar': 0,
                    'total_gain_loss_percent': 0,
                    'num_positions': 0,
                    'num_transactions': 0
                }
            })

        # Group transactions by ticker
        positions_map = {}

        for trans in transactions:
            ticker = trans.ticker

            if ticker not in positions_map:
                positions_map[ticker] = []

            positions_map[ticker].append(trans.to_dict())

        # Calculate consolidated positions
        positions = []
        total_invested_all = 0
        total_current_value_all = 0

        for ticker, ticker_transactions in positions_map.items():
            # Calculate totals for this ticker
            total_quantity = sum(t['quantity'] for t in ticker_transactions)
            total_invested = sum(t['purchase_price'] * t['quantity'] for t in ticker_transactions)
            avg_price = calculate_weighted_average_price(ticker_transactions)

            # Get current price
            current_price = get_current_price(ticker)
            current_value = current_price * total_quantity if current_price else None

            gain_loss_dollar = None
            gain_loss_percent = None

            if current_value is not None:
                gain_loss_dollar, gain_loss_percent = calculate_gain_loss(total_invested, current_value)
                total_current_value_all += current_value

            total_invested_all += total_invested

            positions.append({
                'ticker': ticker,
                'total_quantity': round(total_quantity, 4),
                'avg_purchase_price': round(avg_price, 2),
                'current_price': round(current_price, 2) if current_price else None,
                'total_invested': round(total_invested, 2),
                'current_value': round(current_value, 2) if current_value else None,
                'gain_loss_dollar': round(gain_loss_dollar, 2) if gain_loss_dollar is not None else None,
                'gain_loss_percent': round(gain_loss_percent, 2) if gain_loss_percent is not None else None,
                'weight_percent': None  # Will calculate after totals
            })

        # Calculate portfolio weights
        if total_current_value_all > 0:
            for position in positions:
                if position['current_value'] is not None:
                    position['weight_percent'] = round(
                        (position['current_value'] / total_current_value_all) * 100, 2
                    )

        # Sort by weight (descending)
        positions.sort(key=lambda x: x['weight_percent'] if x['weight_percent'] else 0, reverse=True)

        # Calculate total gain/loss
        total_gain_loss_dollar, total_gain_loss_percent = calculate_gain_loss(
            total_invested_all, total_current_value_all
        )

        totals = {
            'total_invested': round(total_invested_all, 2),
            'total_current_value': round(total_current_value_all, 2),
            'total_gain_loss_dollar': round(total_gain_loss_dollar, 2),
            'total_gain_loss_percent': round(total_gain_loss_percent, 2),
            'num_positions': len(positions),
            'num_transactions': len(transactions)
        }

        return jsonify({
            'positions': positions,
            'totals': totals
        })

    except Exception as e:
        logger.error(f"Error fetching portfolio summary: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/history', methods=['GET'])
def get_portfolio_history():
    """
    Get portfolio value evolution over time.

    Returns:
        JSON with dates and portfolio values for charting
    """
    try:
        db = get_db()
        transactions = db.query(Transaction).all()

        if not transactions:
            return jsonify({'dates': [], 'values': []})

        # Convert to list of dicts
        transactions_list = [trans.to_dict() for trans in transactions]

        # Calculate portfolio evolution
        evolution_data = calculate_portfolio_evolution(transactions_list)

        return jsonify(evolution_data)

    except Exception as e:
        logger.error(f"Error fetching portfolio history: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*50)
    print("Portfolio Tracker - Starting Application")
    print("="*50)
    print("\nAccess the application at: http://localhost:5000")
    print("\nPress CTRL+C to stop the server\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
