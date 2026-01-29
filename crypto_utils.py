"""
Utilidades para obtener precios de criptomonedas
- CryptoCompare API para precios directos en MXN
- Historicos confiables
- Requiere API key gratuita
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import time
import os
import logging

logger = logging.getLogger(__name__)

# API Key de CryptoCompare
# IMPORTANTE: Reemplazar con tu API key real o usar variable de entorno
CRYPTOCOMPARE_API_KEY = os.environ.get('CRYPTOCOMPARE_API_KEY', '8b9c30fc082fb321f78e1f2ed4f3bb3669aae6d2841151845896ad725c0e1eac')

# Cryptos soportadas (simbolos directos)
SUPPORTED_CRYPTOS = ['BTC', 'ETH', 'SOL', 'XRP', 'PAXG']

# Cache
_price_cache = {}
_cache_duration = 300  # 5 minutos


class CryptoCompareAPI:
    """Cliente para CryptoCompare API"""

    BASE_URL = "https://min-api.cryptocompare.com/data"

    @staticmethod
    def get_current_price(symbol: str, currency: str = 'MXN') -> Optional[float]:
        """
        Obtiene precio actual en MXN

        Args:
            symbol: Simbolo (BTC, ETH, etc.)
            currency: Moneda destino (MXN por defecto)

        Returns:
            Precio en MXN o None
        """
        try:
            url = f"{CryptoCompareAPI.BASE_URL}/price"
            params = {
                'fsym': symbol.upper(),
                'tsyms': currency.upper(),
                'api_key': CRYPTOCOMPARE_API_KEY
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if currency.upper() in data:
                price = float(data[currency.upper()])
                logger.info(f"CryptoCompare: {symbol} = ${price:,.2f} {currency.upper()}")
                return price

            logger.warning(f"CryptoCompare: No se encontro precio para {symbol}")
            return None

        except Exception as e:
            logger.error(f"Error en CryptoCompare para {symbol}: {e}")
            return None

    @staticmethod
    def get_historical_price(symbol: str, date_str: str, currency: str = 'MXN') -> Optional[float]:
        """
        Obtiene precio historico para una fecha especifica

        Args:
            symbol: Simbolo (BTC, ETH, etc.)
            date_str: Fecha en formato YYYY-MM-DD
            currency: Moneda destino (MXN)

        Returns:
            Precio historico en MXN o None
        """
        try:
            # Convertir fecha a timestamp
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            timestamp = int(date_obj.timestamp())

            url = f"{CryptoCompareAPI.BASE_URL}/pricehistorical"
            params = {
                'fsym': symbol.upper(),
                'tsyms': currency.upper(),
                'ts': timestamp,
                'api_key': CRYPTOCOMPARE_API_KEY
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if symbol.upper() in data and currency.upper() in data[symbol.upper()]:
                price = float(data[symbol.upper()][currency.upper()])
                logger.info(f"CryptoCompare historico: {symbol} ({date_str}) = ${price:,.2f} {currency.upper()}")
                return price

            logger.warning(f"CryptoCompare: No se encontro precio historico para {symbol} en {date_str}")
            return None

        except Exception as e:
            logger.error(f"Error obteniendo precio historico: {e}")
            return None

    @staticmethod
    def get_daily_history(symbol: str, days: int = 365, currency: str = 'MXN') -> List[Dict]:
        """
        Obtiene historico diario para multiples dias
        Util para graficos

        Args:
            symbol: Simbolo (BTC, ETH, etc.)
            days: Cantidad de dias hacia atras
            currency: Moneda destino (MXN)

        Returns:
            Lista de dicts con {time, close}
        """
        try:
            url = f"{CryptoCompareAPI.BASE_URL}/v2/histoday"
            params = {
                'fsym': symbol.upper(),
                'tsym': currency.upper(),
                'limit': days,
                'api_key': CRYPTOCOMPARE_API_KEY
            }

            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if 'Data' in data and 'Data' in data['Data']:
                logger.info(f"CryptoCompare: Obtenidos {len(data['Data']['Data'])} dias de historico para {symbol}")
                return data['Data']['Data']

            logger.warning(f"CryptoCompare: No se encontro historico diario para {symbol}")
            return []

        except Exception as e:
            logger.error(f"Error obteniendo historico diario: {e}")
            return []

    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Valida si un simbolo crypto es soportado"""
        return symbol.upper() in SUPPORTED_CRYPTOS


# Mapeo para compatibilidad con codigo existente
CRYPTO_SYMBOLS_MAP = {s: s.lower() for s in SUPPORTED_CRYPTOS}


def get_crypto_price(symbol: str) -> Optional[float]:
    """
    Obtiene precio actual de una crypto en MXN

    Args:
        symbol: Simbolo (BTC, ETH, SOL, XRP, PAXG)

    Returns:
        Precio en MXN o None
    """
    symbol = symbol.upper()

    # Verificar cache
    cache_key = f"{symbol}_current"
    if cache_key in _price_cache:
        cached_time, cached_price = _price_cache[cache_key]
        if time.time() - cached_time < _cache_duration:
            logger.debug(f"Cache hit para {symbol}: ${cached_price:,.2f} MXN")
            return cached_price

    # Verificar que sea soportada
    if symbol not in SUPPORTED_CRYPTOS:
        logger.warning(f"Crypto no soportada: {symbol}")
        return None

    # Obtener precio
    price = CryptoCompareAPI.get_current_price(symbol, 'MXN')

    if price:
        _price_cache[cache_key] = (time.time(), price)

    return price


def get_crypto_historical_price(symbol: str, date: str) -> Optional[float]:
    """
    Obtiene precio historico de una crypto en MXN

    Args:
        symbol: Simbolo (BTC, ETH, SOL, XRP, PAXG)
        date: Fecha en formato YYYY-MM-DD

    Returns:
        Precio historico en MXN o None
    """
    symbol = symbol.upper()

    if symbol not in SUPPORTED_CRYPTOS:
        return None

    return CryptoCompareAPI.get_historical_price(symbol, date, 'MXN')


def get_crypto_price_series(symbol: str, start_date: str, end_date: str) -> Dict[str, float]:
    """
    Obtiene serie de precios historicos (para graficos)

    Args:
        symbol: Simbolo
        start_date: Fecha inicio YYYY-MM-DD
        end_date: Fecha fin YYYY-MM-DD

    Returns:
        Dict con {fecha: precio}
    """
    symbol = symbol.upper()

    if symbol not in SUPPORTED_CRYPTOS:
        return {}

    # Calcular dias
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    days = (end - start).days + 1

    # Obtener historico
    history = CryptoCompareAPI.get_daily_history(symbol, days, 'MXN')

    if not history:
        return {}

    # Convertir a dict {fecha: precio}
    result = {}
    for item in history:
        timestamp = item['time']
        price = item['close']
        date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        result[date_str] = float(price)

    return result


def validate_crypto_symbol(symbol: str) -> bool:
    """Valida si un simbolo crypto es soportado"""
    return symbol.upper() in SUPPORTED_CRYPTOS


def is_crypto(ticker: str) -> bool:
    """Determina si un ticker es criptomoneda"""
    return validate_crypto_symbol(ticker)


# Alias para compatibilidad
class CoinGeckoAPI:
    """Alias de compatibilidad - redirige a CryptoCompareAPI"""

    @staticmethod
    def get_current_price(symbol: str, currency: str = 'mxn') -> Optional[float]:
        return CryptoCompareAPI.get_current_price(symbol, currency)

    @staticmethod
    def get_historical_price(symbol: str, date: str, currency: str = 'mxn') -> Optional[float]:
        return CryptoCompareAPI.get_historical_price(symbol, date, currency)

    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        return CryptoCompareAPI.validate_symbol(symbol)

    @staticmethod
    def get_price_range(symbol: str, start_date: str, end_date: str, currency: str = 'mxn') -> Optional[List[Dict]]:
        """Obtiene precios en un rango de fechas"""
        series = get_crypto_price_series(symbol, start_date, end_date)
        if series:
            return [{'date': date, 'price': price} for date, price in series.items()]
        return None


# Testing
if __name__ == '__main__':
    import sys

    # Configurar encoding para Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 70)
    print("TESTING CRYPTO UTILS - CRYPTOCOMPARE")
    print("=" * 70)

    if CRYPTOCOMPARE_API_KEY == "TU_API_KEY_AQUI":
        print("\n[!] ADVERTENCIA: Necesitas configurar tu API key de CryptoCompare")
        print("    Opciones:")
        print("    1. Edita crypto_utils.py y reemplaza CRYPTOCOMPARE_API_KEY")
        print("    2. Configura la variable de entorno CRYPTOCOMPARE_API_KEY")
        print("    Obten tu key en: https://www.cryptocompare.com/cryptopian/api-keys")
        print("\n    Intentando sin API key (funcionalidad limitada)...")

    print("\n[PRECIOS ACTUALES]\n")
    for symbol in SUPPORTED_CRYPTOS:
        price = get_crypto_price(symbol)
        if price:
            print(f"  [OK] {symbol:5s}: ${price:>15,.2f} MXN")
        else:
            print(f"  [ERROR] {symbol:5s}: No disponible")

    print("\n[PRECIO HISTORICO (hace 30 dias)]\n")
    date_30_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    btc_historical = get_crypto_historical_price('BTC', date_30_days_ago)
    if btc_historical:
        print(f"  [OK] BTC ({date_30_days_ago}): ${btc_historical:,.2f} MXN")
    else:
        print(f"  [ERROR] No se pudo obtener precio historico")

    print("\n[SERIE DE PRECIOS (ultimos 7 dias)]\n")
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    series = get_crypto_price_series('BTC', start_date, end_date)

    if series:
        for date, price in list(series.items())[-7:]:
            print(f"  {date}: ${price:,.2f} MXN")
    else:
        print("  [ERROR] No se pudo obtener serie de precios")

    print("\n" + "=" * 70)
    print("Prueba completada")
    print("=" * 70)
