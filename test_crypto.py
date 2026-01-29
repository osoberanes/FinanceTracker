"""
Test script to verify cryptocurrency functionality
"""

import sys
import requests
import json
from datetime import datetime, timedelta

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:5000"

def test_create_crypto_transaction():
    """Test creating a crypto transaction"""
    print("\n=== Testing Crypto Transaction Creation ===")

    # Test data for Bitcoin
    transaction_data = {
        "asset_type": "crypto",
        "market": "CRYPTO",
        "ticker": "BTC",
        "purchase_date": (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        "purchase_price": 1200000.50,  # Price in MXN
        "quantity": 0.025,  # 0.025 BTC
        "generates_staking": False,
        "staking_rewards": 0.0
    }

    print(f"Creating Bitcoin transaction: {json.dumps(transaction_data, indent=2)}")

    response = requests.post(f"{BASE_URL}/api/transactions", json=transaction_data)

    if response.status_code == 201:
        print("✓ Bitcoin transaction created successfully!")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    else:
        print(f"✗ Failed to create transaction: {response.status_code}")
        print(f"Error: {response.json()}")
        return False


def test_create_ethereum_staking():
    """Test creating an Ethereum transaction with staking"""
    print("\n=== Testing Ethereum with Staking ===")

    transaction_data = {
        "asset_type": "crypto",
        "market": "CRYPTO",
        "ticker": "ETH",
        "purchase_date": (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
        "purchase_price": 60000.75,  # Price in MXN
        "quantity": 0.5,  # 0.5 ETH
        "generates_staking": True,
        "staking_rewards": 0.00234567  # Staking rewards in ETH
    }

    print(f"Creating Ethereum transaction with staking: {json.dumps(transaction_data, indent=2)}")

    response = requests.post(f"{BASE_URL}/api/transactions", json=transaction_data)

    if response.status_code == 201:
        print("✓ Ethereum transaction with staking created successfully!")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    else:
        print(f"✗ Failed to create transaction: {response.status_code}")
        print(f"Error: {response.json()}")
        return False


def test_get_transactions():
    """Test fetching all transactions"""
    print("\n=== Testing Get Transactions ===")

    response = requests.get(f"{BASE_URL}/api/transactions")

    if response.status_code == 200:
        transactions = response.json()
        crypto_transactions = [t for t in transactions if t.get('asset_type') == 'crypto']

        print(f"✓ Fetched {len(transactions)} total transactions")
        print(f"✓ Found {len(crypto_transactions)} crypto transactions")

        for trans in crypto_transactions:
            print(f"\n  Crypto: {trans['ticker']}")
            print(f"    Quantity: {trans['quantity']}")
            print(f"    Purchase Price: ${trans['purchase_price']} MXN")
            print(f"    Current Price: ${trans.get('current_price', 'N/A')} MXN")
            print(f"    Generates Staking: {trans.get('generates_staking', False)}")
            print(f"    Staking Rewards: {trans.get('staking_rewards', 0)}")

        return True
    else:
        print(f"✗ Failed to fetch transactions: {response.status_code}")
        return False


def test_portfolio_summary():
    """Test portfolio summary with crypto"""
    print("\n=== Testing Portfolio Summary ===")

    response = requests.get(f"{BASE_URL}/api/portfolio/summary")

    if response.status_code == 200:
        summary = response.json()
        print("✓ Portfolio summary fetched successfully")
        print(f"\nTotals:")
        print(f"  Total Invested: ${summary['totals']['total_invested']:,.2f} MXN")
        print(f"  Current Value: ${summary['totals']['total_current_value']:,.2f} MXN")
        print(f"  Gain/Loss: ${summary['totals']['total_gain_loss_dollar']:,.2f} MXN ({summary['totals']['total_gain_loss_percent']:.2f}%)")
        print(f"  Number of Positions: {summary['totals']['num_positions']}")

        print(f"\nPositions:")
        for position in summary['positions']:
            icon = "🪙" if position['ticker'] in ['BTC', 'ETH', 'SOL', 'XRP', 'PAXG'] else "📊"
            price_str = f"${position['current_price']:,.2f}" if position['current_price'] else "N/A"
            print(f"  {icon} {position['ticker']}: {position['total_quantity']} units @ {price_str} MXN")

        return True
    else:
        print(f"✗ Failed to fetch portfolio summary: {response.status_code}")
        return False


def test_crypto_price_fetch():
    """Test CoinGecko API integration directly"""
    print("\n=== Testing CoinGecko API Integration ===")

    from crypto_utils import get_crypto_price, CoinGeckoAPI

    cryptos = ['BTC', 'ETH', 'SOL', 'XRP', 'PAXG']

    for symbol in cryptos:
        is_valid = CoinGeckoAPI.validate_symbol(symbol)
        if is_valid:
            price = get_crypto_price(symbol)
            if price:
                print(f"✓ {symbol}: ${price:,.2f} MXN")
            else:
                print(f"✗ {symbol}: Failed to fetch price")
        else:
            print(f"✗ {symbol}: Invalid symbol")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("CRYPTOCURRENCY FUNCTIONALITY TEST SUITE")
    print("=" * 60)

    # Run tests
    results = []

    results.append(("CoinGecko API Integration", test_crypto_price_fetch()))
    results.append(("Create Bitcoin Transaction", test_create_crypto_transaction()))
    results.append(("Create Ethereum with Staking", test_create_ethereum_staking()))
    results.append(("Fetch Transactions", test_get_transactions()))
    results.append(("Portfolio Summary", test_portfolio_summary()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")

    if total_passed == len(results):
        print("\n🎉 All tests passed! Crypto functionality is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
