"""Flask application for Portfolio Tracker."""

from flask import Flask, render_template, request, jsonify
from database import init_db, get_db, close_db
from models import Transaction, Custodian, SwensenConfig
from utils import (
    get_current_price,
    validate_ticker,
    calculate_portfolio_evolution,
    calculate_weighted_average_price,
    calculate_gain_loss
)
from utils_classification import (
    classify_asset,
    get_asset_class_info,
    get_all_asset_classes,
    get_swensen_ideal_allocation,
    calculate_rebalancing_recommendations,
    get_swensen_target_allocation_from_db,
    initialize_default_swensen_config,
    calculate_rebalancing_recommendations_with_db,
    calculate_investment_allocation,
    get_asset_class_color,
    get_all_asset_class_colors
)
from datetime import datetime, timedelta
from sqlalchemy import func
from collections import defaultdict
import logging
import traceback

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
            if market == 'MX':
                # Corregir formato de tickers mexicanos
                if ticker.endswith('MX') and '.MX' not in ticker:
                    # Tiene MX al final pero sin punto (ej: VWOMX)
                    base_symbol = ticker[:-2]  # Quita "MX"
                    ticker = f"{base_symbol}.MX"
                    logger.info(f"Auto-corregido ticker mexicano: {data['ticker']} → {ticker}")
                elif ticker.endswith('.MX'):
                    # Ya está correcto
                    pass
                else:
                    # No tiene .MX, agregarlo
                    ticker = f"{ticker}.MX"
                    logger.info(f"Agregado sufijo .MX: {data['ticker']} → {ticker}")
            elif market == 'US':
                # Remove .MX or .US suffix if present
                ticker = ticker.replace('.MX', '').replace('.US', '')
            # For other markets, use ticker as-is

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

        # Clasificacion: usar manual si se provee, sino auto-detectar
        asset_class = data.get('asset_class')
        if not asset_class or asset_class == '':
            asset_class = classify_asset(ticker, market, asset_type)

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
            staking_rewards=staking_rewards,
            asset_class=asset_class
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
    Obtiene historial del portfolio (VERSIÓN SIMPLIFICADA)

    Por ahora, retorna solo puntos basados en fechas de compra,
    sin intentar calcular precios históricos diarios (muy costoso y causa timeouts)

    Returns:
        JSON array con objetos {date, value}
    """
    try:
        print("=== DEBUG: Inicio get_portfolio_history ===")

        range_param = request.args.get('range', 'all')
        print(f"DEBUG: range_param = {range_param}")

        db = get_db()

        # Obtener todas las transacciones ordenadas
        transactions = db.query(Transaction).order_by(Transaction.purchase_date).all()

        if not transactions:
            print("DEBUG: No hay transacciones, retornando array vacío")
            return jsonify([])

        # Determinar rango de fechas
        end_date = datetime.now().date()
        first_txn_date = transactions[0].purchase_date

        if range_param == '1y':
            start_date = end_date - timedelta(days=365)
        elif range_param == '3y':
            start_date = end_date - timedelta(days=365*3)
        elif range_param == '5y':
            start_date = end_date - timedelta(days=365*5)
        else:  # 'all'
            start_date = first_txn_date

        print(f"DEBUG: Rango de fechas: {start_date} a {end_date}")

        # Filtrar transacciones en el rango
        relevant_txns = [t for t in transactions if start_date <= t.purchase_date <= end_date]

        if not relevant_txns:
            print("DEBUG: No hay transacciones en el rango, retornando array vacío")
            return jsonify([])

        print(f"DEBUG: Procesando {len(relevant_txns)} transacciones")

        # Crear puntos de historial basados en fechas de compra
        # (sin intentar calcular precios diarios - muy costoso)
        history = []
        cumulative_invested = 0

        # Agrupar por fecha
        txns_by_date = defaultdict(list)
        for txn in relevant_txns:
            txns_by_date[txn.purchase_date].append(txn)

        # Crear puntos de historial
        for date in sorted(txns_by_date.keys()):
            day_txns = txns_by_date[date]
            for txn in day_txns:
                cumulative_invested += float(txn.purchase_price) * float(txn.quantity)

            history.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': round(cumulative_invested, 2)
            })

        # Agregar punto actual con precios de mercado
        current_value = 0
        for txn in relevant_txns:
            try:
                current_price = get_current_price(txn.ticker)
                if current_price:
                    current_value += current_price * float(txn.quantity)
                else:
                    # Si falla obtener precio, usar precio de compra
                    current_value += float(txn.purchase_price) * float(txn.quantity)
            except Exception as price_error:
                logger.warning(f"Error obteniendo precio para {txn.ticker}: {price_error}")
                # Usar precio de compra como fallback
                current_value += float(txn.purchase_price) * float(txn.quantity)

        # Agregar punto final (hoy)
        if history:
            last_date = datetime.strptime(history[-1]['date'], '%Y-%m-%d').date()
            if last_date < end_date:
                history.append({
                    'date': end_date.strftime('%Y-%m-%d'),
                    'value': round(current_value, 2)
                })
            else:
                # Actualizar último punto con valor actual
                history[-1]['value'] = round(current_value, 2)

        print(f"DEBUG: Retornando {len(history)} puntos de historial")
        if history:
            print(f"DEBUG: Primera entrada: {history[0]}")
            print(f"DEBUG: Última entrada: {history[-1]}")

        return jsonify(history)

    except Exception as e:
        print(f"ERROR en get_portfolio_history: {str(e)}")
        traceback.print_exc()
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


# ============================================
# PAGINA DE ANALISIS SWENSEN
# ============================================

@app.route('/analysis')
def analysis():
    """Pagina de analisis de diversificacion Swensen"""
    return render_template('analysis.html')


# ============================================
# API DE ANALISIS DE DIVERSIFICACION
# ============================================

@app.route('/api/portfolio/by-asset-class', methods=['GET'])
def get_portfolio_by_asset_class():
    """
    Obtiene diversificacion por clase de activo (Swensen).

    Returns:
        JSON con analisis de diversificacion por asset_class
    """
    try:
        db = get_db()
        transactions = db.query(Transaction).all()

        if not transactions:
            return jsonify({
                'asset_classes': [],
                'total_value': 0
            })

        asset_class_summary = {}
        total_value = 0

        for trans in transactions:
            # Clasificar si no esta clasificado
            if not trans.asset_class:
                trans.asset_class = classify_asset(trans.ticker, trans.market, trans.asset_type)
                db.commit()

            asset_class = trans.asset_class or 'sin_clasificar'

            if asset_class not in asset_class_summary:
                asset_class_summary[asset_class] = {
                    'value': 0,
                    'invested': 0,
                    'positions': 0,
                    'tickers': []
                }

            current_price = get_current_price(trans.ticker)
            if current_price:
                current_value = current_price * float(trans.quantity)
                invested = float(trans.purchase_price) * float(trans.quantity)

                asset_class_summary[asset_class]['value'] += current_value
                asset_class_summary[asset_class]['invested'] += invested
                asset_class_summary[asset_class]['positions'] += 1

                if trans.ticker not in asset_class_summary[asset_class]['tickers']:
                    asset_class_summary[asset_class]['tickers'].append(trans.ticker)

                total_value += current_value

        # Calcular porcentajes
        result = []
        for asset_class, data in asset_class_summary.items():
            info = get_asset_class_info(asset_class)
            percentage = (data['value'] / total_value * 100) if total_value > 0 else 0
            gain_loss = data['value'] - data['invested']
            gain_loss_pct = (gain_loss / data['invested'] * 100) if data['invested'] > 0 else 0

            result.append({
                'asset_class': asset_class,
                'name': info['name'],
                'emoji': info['emoji'],
                'description': info['description'],
                'value': round(data['value'], 2),
                'invested': round(data['invested'], 2),
                'percentage': round(percentage, 2),
                'swensen_target': info['swensen_target'],
                'diff': round(percentage - info['swensen_target'], 2),
                'gain_loss': round(gain_loss, 2),
                'gain_loss_pct': round(gain_loss_pct, 2),
                'positions': data['positions'],
                'tickers': data['tickers']
            })

        # Ordenar por valor descendente
        result.sort(key=lambda x: x['value'], reverse=True)

        return jsonify({
            'asset_classes': result,
            'total_value': round(total_value, 2)
        })

    except Exception as e:
        logger.error(f"Error en diversificacion por asset class: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/rebalancing-recommendations', methods=['GET'])
def get_rebalancing_recommendations():
    """
    Obtiene recomendaciones de rebalanceo segun modelo Swensen.

    Returns:
        JSON con recomendaciones de ajuste
    """
    try:
        db = get_db()
        transactions = db.query(Transaction).all()

        if not transactions:
            return jsonify({
                'recommendations': [],
                'total_value': 0,
                'message': 'No hay transacciones en el portfolio'
            })

        # Calcular allocation actual
        asset_class_summary = {}
        total_value = 0

        for trans in transactions:
            if not trans.asset_class:
                trans.asset_class = classify_asset(trans.ticker, trans.market, trans.asset_type)
                db.commit()

            asset_class = trans.asset_class or 'sin_clasificar'

            if asset_class not in asset_class_summary:
                asset_class_summary[asset_class] = {'value': 0}

            current_price = get_current_price(trans.ticker)
            if current_price:
                current_value = current_price * float(trans.quantity)
                asset_class_summary[asset_class]['value'] += current_value
                total_value += current_value

        # Calcular porcentajes
        current_allocation = {}
        for asset_class, data in asset_class_summary.items():
            percentage = (data['value'] / total_value * 100) if total_value > 0 else 0
            current_allocation[asset_class] = {
                'percentage': percentage,
                'value': data['value']
            }

        # Calcular recomendaciones
        recommendations = calculate_rebalancing_recommendations(
            current_allocation,
            total_value
        )

        return jsonify({
            'recommendations': recommendations,
            'total_value': round(total_value, 2)
        })

    except Exception as e:
        logger.error(f"Error en recomendaciones de rebalanceo: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/swensen-ideal', methods=['GET'])
def get_swensen_ideal():
    """
    Obtiene el modelo ideal de Swensen adaptado a Mexico.

    Returns:
        JSON con la asignacion ideal por clase de activo
    """
    try:
        ideal_allocation = get_swensen_ideal_allocation()
        all_classes = get_all_asset_classes()

        result = []
        for asset_class, target_pct in ideal_allocation.items():
            info = all_classes.get(asset_class, {})
            result.append({
                'asset_class': asset_class,
                'name': info.get('name', asset_class),
                'emoji': info.get('emoji', ''),
                'description': info.get('description', ''),
                'target_percentage': target_pct
            })

        # Ordenar por porcentaje descendente
        result.sort(key=lambda x: x['target_percentage'], reverse=True)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error obteniendo modelo Swensen: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================
# API DE CONFIGURACION SWENSEN PERSONALIZADA
# ============================================

@app.route('/api/swensen-config', methods=['GET'])
def get_swensen_config():
    """
    Obtiene configuracion actual de Swensen (personalizada o por defecto).

    Returns:
        JSON con configuracion por clase de activo
    """
    try:
        db = get_db()
        configs = db.query(SwensenConfig).all()
        all_classes = get_all_asset_classes()

        result = []
        for asset_class, info in all_classes.items():
            config = next((c for c in configs if c.asset_class == asset_class), None)

            result.append({
                'asset_class': asset_class,
                'name': info['name'],
                'emoji': info['emoji'],
                'description': info['description'],
                'target_percentage': float(config.target_percentage) if config else info['swensen_target'],
                'is_active': config.is_active if config else True,
                'notes': config.notes if config else ''
            })

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error obteniendo config Swensen: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/swensen-config', methods=['POST'])
def save_swensen_config():
    """
    Guarda configuracion personalizada de Swensen.

    Request JSON:
        {
            "configs": [
                {"asset_class": "acciones_usa", "target_percentage": 35, "is_active": true, "notes": ""}
            ]
        }

    Returns:
        JSON con mensaje de exito o error
    """
    try:
        db = get_db()
        data = request.get_json()
        configs = data.get('configs', [])

        # Validar suma = 100%
        total = sum(c['target_percentage'] for c in configs if c.get('is_active', True))
        if abs(total - 100) > 0.5:
            return jsonify({'error': f'Los porcentajes deben sumar 100%. Actual: {total:.1f}%'}), 400

        # Actualizar o crear
        for config_data in configs:
            config = db.query(SwensenConfig).filter_by(
                asset_class=config_data['asset_class']
            ).first()

            if config:
                config.target_percentage = config_data['target_percentage']
                config.is_active = config_data.get('is_active', True)
                config.notes = config_data.get('notes', '')
                config.updated_at = datetime.utcnow()
            else:
                config = SwensenConfig(
                    asset_class=config_data['asset_class'],
                    target_percentage=config_data['target_percentage'],
                    is_active=config_data.get('is_active', True),
                    notes=config_data.get('notes', '')
                )
                db.add(config)

        db.commit()
        logger.info("Swensen configuration saved successfully")

        return jsonify({'message': 'Configuracion guardada exitosamente'})

    except Exception as e:
        db.rollback()
        logger.error(f"Error guardando config Swensen: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/swensen-config/reset', methods=['POST'])
def reset_swensen_config():
    """
    Restaura configuracion Swensen a valores por defecto.

    Returns:
        JSON con mensaje de exito o error
    """
    try:
        db = get_db()

        # Eliminar configuracion actual
        db.query(SwensenConfig).delete()
        db.commit()

        # Inicializar por defecto
        initialize_default_swensen_config(db)

        logger.info("Swensen configuration reset to defaults")

        return jsonify({'message': 'Configuracion restaurada a valores por defecto'})

    except Exception as e:
        db.rollback()
        logger.error(f"Error reseteando config Swensen: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================
# API CALCULADORA DE INVERSION
# ============================================

@app.route('/api/investment-calculator', methods=['POST'])
def calculate_investment():
    """
    Calcula como distribuir nueva inversion para acercarse al modelo ideal.

    Request JSON:
        {
            "amount": 10000  // Monto a invertir
        }

    Returns:
        JSON con distribucion sugerida por clase de activo
    """
    try:
        data = request.get_json()
        new_investment = float(data.get('amount', 0))

        if new_investment <= 0:
            return jsonify({'error': 'El monto debe ser mayor a 0'}), 400

        db = get_db()
        transactions = db.query(Transaction).all()

        if not transactions:
            # Si no hay transacciones, distribuir segun modelo ideal
            ideal = get_swensen_target_allocation_from_db(db)
            distribution = []

            for asset_class, target_pct in ideal.items():
                if target_pct > 0:
                    info = get_asset_class_info(asset_class)
                    suggested_amount = (target_pct / 100) * new_investment
                    distribution.append({
                        'asset_class': asset_class,
                        'name': info['name'],
                        'emoji': info['emoji'],
                        'current_value': 0,
                        'ideal_future_value': suggested_amount,
                        'deficit': suggested_amount,
                        'suggested_amount': round(suggested_amount, 2),
                        'suggested_pct': target_pct
                    })

            return jsonify({
                'new_investment': new_investment,
                'current_total': 0,
                'future_total': new_investment,
                'distribution': distribution
            })

        # Calcular distribucion actual
        asset_class_summary = {}
        total_value = 0

        for trans in transactions:
            if not trans.asset_class:
                trans.asset_class = classify_asset(trans.ticker, trans.market, trans.asset_type)
                db.commit()

            asset_class = trans.asset_class or 'sin_clasificar'

            if asset_class not in asset_class_summary:
                asset_class_summary[asset_class] = {'value': 0}

            current_price = get_current_price(trans.ticker)
            if current_price:
                current_value = current_price * float(trans.quantity)
                asset_class_summary[asset_class]['value'] += current_value
                total_value += current_value

        # Preparar allocation actual
        current_allocation = {}
        for asset_class, data in asset_class_summary.items():
            percentage = (data['value'] / total_value * 100) if total_value > 0 else 0
            current_allocation[asset_class] = {
                'percentage': percentage,
                'value': data['value']
            }

        # Calcular distribucion
        distribution = calculate_investment_allocation(
            new_investment,
            current_allocation,
            total_value,
            db
        )

        return jsonify({
            'new_investment': new_investment,
            'current_total': round(total_value, 2),
            'future_total': round(total_value + new_investment, 2),
            'distribution': distribution
        })

    except Exception as e:
        logger.error(f"Error en calculadora de inversion: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================
# API DE CLASIFICACIONES (ADMIN)
# ============================================

@app.route('/api/classifications', methods=['GET'])
def get_classifications():
    """
    Obtiene lista de transacciones agrupadas por ticker con su clasificacion.

    Returns:
        JSON con lista de tickers y su clasificacion actual
    """
    try:
        db = get_db()

        # Obtener tickers unicos con su clasificacion
        results = db.query(
            Transaction.ticker,
            Transaction.market,
            Transaction.asset_type,
            Transaction.asset_class
        ).distinct().all()

        classifications = []
        for ticker, market, asset_type, asset_class in results:
            info = get_asset_class_info(asset_class) if asset_class else {
                'name': 'Sin Clasificar',
                'emoji': '?',
                'color': '#6C757D'
            }

            # Contar transacciones con este ticker
            count = db.query(Transaction).filter(Transaction.ticker == ticker).count()

            classifications.append({
                'ticker': ticker,
                'market': market,
                'asset_type': asset_type,
                'asset_class': asset_class,
                'asset_class_name': info.get('name', 'Sin Clasificar'),
                'asset_class_emoji': info.get('emoji', '?'),
                'asset_class_color': info.get('color', '#6C757D'),
                'transaction_count': count
            })

        # Ordenar por ticker
        classifications.sort(key=lambda x: x['ticker'])

        return jsonify(classifications)

    except Exception as e:
        logger.error(f"Error obteniendo clasificaciones: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/classifications/<ticker>', methods=['PUT'])
def update_classification(ticker):
    """
    Actualiza la clasificacion de todas las transacciones de un ticker.

    Args:
        ticker: El ticker a reclasificar

    Request JSON:
        {
            "asset_class": "acciones_usa"
        }

    Returns:
        JSON con mensaje de exito o error
    """
    try:
        db = get_db()
        data = request.get_json()

        new_asset_class = data.get('asset_class')

        # Validar que la clase de activo sea valida
        all_classes = get_all_asset_classes()
        if new_asset_class and new_asset_class not in all_classes:
            return jsonify({'error': f'Clase de activo invalida: {new_asset_class}'}), 400

        # Actualizar todas las transacciones de este ticker
        updated = db.query(Transaction).filter(
            Transaction.ticker == ticker
        ).update({
            'asset_class': new_asset_class,
            'updated_at': datetime.utcnow()
        })

        db.commit()

        logger.info(f"Reclasificacion: {ticker} -> {new_asset_class} ({updated} transacciones)")

        return jsonify({
            'message': f'Clasificacion actualizada para {ticker}',
            'ticker': ticker,
            'new_asset_class': new_asset_class,
            'transactions_updated': updated
        })

    except Exception as e:
        db.rollback()
        logger.error(f"Error reclasificando {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/classifications/auto-classify', methods=['POST'])
def auto_classify_all():
    """
    Reclasifica automaticamente todas las transacciones sin clasificar
    o todas si se especifica force=true.

    Request JSON:
        {
            "force": false  // Si true, reclasifica todo incluyendo ya clasificados
        }

    Returns:
        JSON con resultado de la reclasificacion
    """
    try:
        db = get_db()
        data = request.get_json() or {}
        force = data.get('force', False)

        if force:
            # Reclasificar todas
            transactions = db.query(Transaction).all()
        else:
            # Solo las sin clasificar
            transactions = db.query(Transaction).filter(
                (Transaction.asset_class == None) | (Transaction.asset_class == '')
            ).all()

        reclassified = 0
        for trans in transactions:
            new_class = classify_asset(trans.ticker, trans.market, trans.asset_type)
            if new_class != trans.asset_class:
                trans.asset_class = new_class
                reclassified += 1

        db.commit()

        logger.info(f"Auto-clasificacion completada: {reclassified} transacciones reclasificadas")

        return jsonify({
            'message': f'Auto-clasificacion completada',
            'total_processed': len(transactions),
            'reclassified': reclassified
        })

    except Exception as e:
        db.rollback()
        logger.error(f"Error en auto-clasificacion: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/asset-classes', methods=['GET'])
def get_asset_classes_api():
    """
    Obtiene todas las clases de activo disponibles con sus propiedades.

    Returns:
        JSON con lista de clases de activo
    """
    try:
        all_classes = get_all_asset_classes()
        result = []

        for asset_class, info in all_classes.items():
            result.append({
                'code': asset_class,
                'name': info['name'],
                'emoji': info['emoji'],
                'description': info['description'],
                'color': info.get('color', '#6C757D'),
                'swensen_target': info['swensen_target']
            })

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error obteniendo clases de activo: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/asset-class-colors', methods=['GET'])
def get_asset_class_colors_api():
    """
    Obtiene la paleta de colores de todas las clases de activo.

    Returns:
        JSON con {asset_class: color_hex}
    """
    try:
        colors = get_all_asset_class_colors()
        return jsonify(colors)

    except Exception as e:
        logger.error(f"Error obteniendo colores: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import os

    # Get port from environment variable (for Render) or default to 5000
    port = int(os.environ.get('PORT', 5000))

    # Determine if running in production
    is_production = os.environ.get('RENDER') is not None

    if not is_production:
        print("\n" + "="*50)
        print("Portfolio Tracker - Starting Application")
        print("="*50)
        print(f"\nAccess the application at: http://localhost:{port}")
        print("\nPress CTRL+C to stop the server\n")

    app.run(host='0.0.0.0', port=port, debug=not is_production)
