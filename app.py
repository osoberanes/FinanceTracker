"""Flask application for Portfolio Tracker."""

from flask import Flask, render_template, request, jsonify
from database import init_db, get_db, close_db
from models import Transaction, Custodian
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

            # Calculate values - convert Decimal to float for calculations
            purchase_price_float = float(trans.purchase_price)
            quantity_float = float(trans.quantity)

            invested_value = purchase_price_float * quantity_float
            current_value = current_price * quantity_float if current_price else None

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

        # Get asset_type and market
        asset_type = data.get('asset_type', 'stock')
        market = data.get('market', 'MX').upper()
        ticker = data['ticker'].upper().strip()

        # Handle crypto tickers separately
        if market == 'CRYPTO' or asset_type == 'crypto':
            asset_type = 'crypto'
            # Crypto tickers don't need formatting, just validate
            if not validate_ticker(ticker):
                return jsonify({'error': f'Invalid crypto ticker: {ticker}. Supported: BTC, ETH, SOL, XRP, PAXG'}), 400
        else:
            # Stock ticker formatting
            # Remove .MX suffix if user added it
            ticker = ticker.replace('.MX', '').replace('.US', '')

            # Add appropriate suffix based on market
            if market == 'MX':
                ticker = ticker + '.MX'
            # For US market, no suffix needed

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

        # Get crypto-specific fields
        generates_staking = data.get('generates_staking', False)
        staking_rewards = float(data.get('staking_rewards', 0.0))

        # Create transaction
        db = get_db()
        transaction = Transaction(
            asset_type=asset_type,
            ticker=ticker,
            market=market,
            purchase_date=purchase_date,
            purchase_price=purchase_price,
            quantity=quantity,
            currency='MXN',
            custodian_id=data.get('custodian_id'),
            generates_staking=generates_staking,
            staking_rewards=staking_rewards
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


@app.route('/api/transactions/<int:id>', methods=['GET'])
def get_transaction(id):
    """
    Get a specific transaction by ID.

    Args:
        id: Transaction ID

    Returns:
        JSON with transaction details
    """
    try:
        db = get_db()
        transaction = db.query(Transaction).filter(Transaction.id == id).first()

        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404

        trans_dict = transaction.to_dict()

        # Format date for frontend
        trans_dict['purchase_date_formatted'] = transaction.purchase_date.strftime('%d/%m/%Y')

        return jsonify(trans_dict)

    except Exception as e:
        logger.error(f"Error fetching transaction {id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/transactions/<int:id>', methods=['PUT'])
def update_transaction(id):
    """
    Update an existing transaction.

    Args:
        id: Transaction ID

    Expected JSON body (all fields optional):
        {
            "ticker": "AAPL",
            "market": "US",
            "asset_type": "stock" or "crypto",
            "purchase_date": "2024-01-15",
            "purchase_price": 150.50,
            "quantity": 10,
            "generates_staking": false,
            "staking_rewards": 0.0
        }

    Returns:
        JSON with success message or error
    """
    try:
        db = get_db()
        transaction = db.query(Transaction).filter(Transaction.id == id).first()

        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404

        data = request.get_json()

        # Handle ticker update if provided
        if 'ticker' in data:
            market = data.get('market', transaction.market or 'MX').upper()
            asset_type = data.get('asset_type', transaction.asset_type or 'stock')
            ticker = data['ticker'].upper().strip()

            # Check if crypto
            if market == 'CRYPTO' or asset_type == 'crypto':
                asset_type = 'crypto'
                if not validate_ticker(ticker):
                    return jsonify({'error': f'Invalid crypto ticker: {ticker}. Supported: BTC, ETH, SOL, XRP, PAXG'}), 400
                transaction.ticker = ticker
                transaction.asset_type = 'crypto'
                transaction.market = 'CRYPTO'
            else:
                # Stock ticker
                ticker = ticker.replace('.MX', '').replace('.US', '')
                if market == 'MX':
                    ticker = ticker + '.MX'

                if not validate_ticker(ticker):
                    return jsonify({'error': f'Invalid ticker: {ticker}. Ticker not found.'}), 400

                transaction.ticker = ticker
                transaction.asset_type = 'stock'
                transaction.market = market

        # Handle date update if provided
        if 'purchase_date' in data:
            try:
                purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
                if purchase_date > datetime.now().date():
                    return jsonify({'error': 'Purchase date cannot be in the future'}), 400
                transaction.purchase_date = purchase_date
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Handle numeric values if provided
        if 'purchase_price' in data:
            try:
                purchase_price = float(data['purchase_price'])
                if purchase_price <= 0:
                    return jsonify({'error': 'Purchase price must be greater than 0'}), 400
                transaction.purchase_price = purchase_price
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid purchase_price value'}), 400

        if 'quantity' in data:
            try:
                quantity = float(data['quantity'])
                if quantity <= 0:
                    return jsonify({'error': 'Quantity must be greater than 0'}), 400
                transaction.quantity = quantity
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid quantity value'}), 400

        # Handle staking fields (crypto only)
        if 'generates_staking' in data:
            transaction.generates_staking = bool(data['generates_staking'])

        if 'staking_rewards' in data:
            try:
                transaction.staking_rewards = float(data['staking_rewards'])
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid staking_rewards value'}), 400

        # Handle custodian if provided
        if 'custodian_id' in data:
            transaction.custodian_id = data.get('custodian_id')

        # Handle notes if provided
        if 'notes' in data:
            transaction.notes = data.get('notes')

        transaction.updated_at = datetime.now()

        db.commit()

        logger.info(f"Transaction {id} updated: {transaction.ticker}")

        return jsonify({
            'message': 'Transaction updated successfully',
            'transaction': transaction.to_dict()
        })

    except Exception as e:
        logger.error(f"Error updating transaction {id}: {str(e)}")
        db.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/transactions/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    """
    Delete a transaction.

    Args:
        id: Transaction ID

    Returns:
        JSON with success message or error
    """
    try:
        db = get_db()
        transaction = db.query(Transaction).filter(Transaction.id == id).first()

        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404

        ticker = transaction.ticker
        quantity = transaction.quantity

        db.delete(transaction)
        db.commit()

        logger.info(f"Transaction {id} deleted: {ticker} - {quantity} shares")

        return jsonify({'message': 'Transaction deleted successfully'})

    except Exception as e:
        logger.error(f"Error deleting transaction {id}: {str(e)}")
        db.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# RUTAS DE AJUSTES
# ============================================

@app.route('/settings')
def settings():
    """Página de configuración"""
    return render_template('settings.html')


# ============================================
# API DE CUSTODIOS
# ============================================

@app.route('/api/custodians', methods=['GET'])
def get_custodians():
    """Obtener todos los custodios activos"""
    try:
        db = get_db()
        custodians = db.query(Custodian).filter_by(is_active=True).order_by(Custodian.name).all()
        return jsonify([c.to_dict() for c in custodians])
    except Exception as e:
        logger.error(f"Error fetching custodians: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/custodians', methods=['POST'])
def create_custodian():
    """Crear nuevo custodio"""
    try:
        db = get_db()
        data = request.get_json()

        # Validar que no exista
        existing = db.query(Custodian).filter_by(name=data['name']).first()
        if existing:
            return jsonify({'error': 'El custodio ya existe'}), 400

        custodian = Custodian(
            name=data['name'],
            type=data.get('type', 'other'),
            notes=data.get('notes', '')
        )

        db.add(custodian)
        db.commit()
        db.refresh(custodian)

        logger.info(f"Custodian created: {custodian.name}")

        return jsonify(custodian.to_dict()), 201

    except Exception as e:
        logger.error(f"Error creating custodian: {str(e)}")
        db.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/custodians/<int:id>', methods=['PUT'])
def update_custodian(id):
    """Actualizar custodio"""
    try:
        db = get_db()
        custodian = db.query(Custodian).filter(Custodian.id == id).first()

        if not custodian:
            return jsonify({'error': 'Custodio no encontrado'}), 404

        data = request.get_json()

        custodian.name = data.get('name', custodian.name)
        custodian.type = data.get('type', custodian.type)
        custodian.notes = data.get('notes', custodian.notes)

        db.commit()

        logger.info(f"Custodian updated: {custodian.name}")

        return jsonify(custodian.to_dict())

    except Exception as e:
        logger.error(f"Error updating custodian {id}: {str(e)}")
        db.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/custodians/<int:id>', methods=['DELETE'])
def delete_custodian(id):
    """Desactivar custodio (soft delete)"""
    try:
        db = get_db()
        custodian = db.query(Custodian).filter(Custodian.id == id).first()

        if not custodian:
            return jsonify({'error': 'Custodio no encontrado'}), 404

        # Verificar si tiene transacciones asociadas
        transaction_count = db.query(Transaction).filter(Transaction.custodian_id == id).count()

        if transaction_count > 0:
            custodian.is_active = False  # Soft delete
            db.commit()
            logger.info(f"Custodian deactivated: {custodian.name} ({transaction_count} transactions)")
            return jsonify({'message': f'Custodio desactivado (tiene {transaction_count} transacciones asociadas)'})
        else:
            db.delete(custodian)  # Hard delete si no tiene transacciones
            db.commit()
            logger.info(f"Custodian deleted: {custodian.name}")
            return jsonify({'message': 'Custodio eliminado'})

    except Exception as e:
        logger.error(f"Error deleting custodian {id}: {str(e)}")
        db.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/by-custodian', methods=['GET'])
def portfolio_by_custodian():
    """Resumen de cartera agrupado por custodio"""
    try:
        db = get_db()
        transactions = db.query(Transaction).all()

        if not transactions:
            return jsonify([])

        # Agrupar por custodio
        custodian_summary = {}

        for trans in transactions:
            # Obtener nombre del custodio
            if trans.custodian_obj:
                custodian_name = trans.custodian_obj.name
            else:
                custodian_name = 'Sin asignar'

            if custodian_name not in custodian_summary:
                custodian_summary[custodian_name] = {
                    'invested': 0,
                    'current_value': 0
                }

            # Obtener precio actual
            current_price = get_current_price(trans.ticker)
            if current_price:
                invested = float(trans.purchase_price) * float(trans.quantity)
                current_val = current_price * float(trans.quantity)

                custodian_summary[custodian_name]['invested'] += invested
                custodian_summary[custodian_name]['current_value'] += current_val

        # Convertir a lista
        result = []
        for custodian, data in custodian_summary.items():
            gain_loss_dollar, gain_loss_percent = calculate_gain_loss(
                data['invested'],
                data['current_value']
            )

            result.append({
                'custodian': custodian,
                'invested': round(data['invested'], 2),
                'current_value': round(data['current_value'], 2),
                'gain_loss_dollar': round(gain_loss_dollar, 2),
                'gain_loss_percent': round(gain_loss_percent, 2)
            })

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error fetching portfolio by custodian: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*50)
    print("Portfolio Tracker - Starting Application")
    print("="*50)
    print("\nAccess the application at: http://localhost:5000")
    print("\nPress CTRL+C to stop the server\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
