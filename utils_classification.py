"""
Sistema de clasificacion de activos segun modelo Swensen adaptado a Mexico.

Este modulo proporciona funciones para clasificar automaticamente activos
financieros en categorias para analisis de diversificacion de portfolio.
"""

from typing import Optional, Dict, List

# Definicion de clases de activos con metas Swensen adaptadas a Mexico
# Incluye paleta de colores consistente para graficos
ASSET_CLASSES = {
    'acciones_mexico': {
        'name': 'Acciones Mexico',
        'emoji': '🇲🇽',
        'description': 'Empresas mexicanas',
        'swensen_target': 15,  # % recomendado
        'color': '#006847'  # Verde Mexico
    },
    'acciones_usa': {
        'name': 'Acciones Estados Unidos',
        'emoji': '🇺🇸',
        'description': 'Empresas estadounidenses',
        'swensen_target': 30,
        'color': '#3C3B6E'  # Azul USA
    },
    'acciones_internacionales': {
        'name': 'Acciones Internacionales',
        'emoji': '🌍',
        'description': 'Mercados desarrollados (Europa, Asia)',
        'swensen_target': 15,
        'color': '#17A2B8'  # Cyan
    },
    'mercados_emergentes': {
        'name': 'Mercados Emergentes',
        'emoji': '🌎',
        'description': 'Paises en desarrollo',
        'swensen_target': 5,
        'color': '#20C997'  # Teal
    },
    'fibras': {
        'name': 'FIBRAs',
        'emoji': '🏢',
        'description': 'Bienes raices',
        'swensen_target': 20,
        'color': '#6F42C1'  # Purpura
    },
    'cetes': {
        'name': 'CETES',
        'emoji': '🏦',
        'description': 'Certificados del Tesoro',
        'swensen_target': 5,
        'color': '#28A745'  # Verde
    },
    'bonos_gubernamentales': {
        'name': 'Bonos Gubernamentales',
        'emoji': '📜',
        'description': 'Bonos largo plazo',
        'swensen_target': 5,
        'color': '#007BFF'  # Azul
    },
    'udibonos': {
        'name': 'UDIBONOS',
        'emoji': '🛡️',
        'description': 'Bonos anti-inflacion',
        'swensen_target': 5,
        'color': '#FD7E14'  # Naranja
    },
    'oro_materias_primas': {
        'name': 'Oro y Materias Primas',
        'emoji': '🥇',
        'description': 'Commodities',
        'swensen_target': 0,  # Swensen no lo incluye, pero lo dejamos
        'color': '#FFC107'  # Dorado
    },
    'criptomonedas': {
        'name': 'Criptomonedas',
        'emoji': '🪙',
        'description': 'Activos digitales',
        'swensen_target': 0,  # No tradicional
        'color': '#E83E8C'  # Rosa
    }
}

# FIBRAs conocidas en Mexico
KNOWN_FIBRAS = [
    'FUNO11', 'FUNO', 'DANHOS13', 'DANHOS', 'FIHO14', 'FIHO',
    'FINN13', 'FINN', 'FMTY14', 'FMTY', 'FIBRAMQ12', 'FIBRAMQ',
    'FIBRAPL14', 'FIBRAPL', 'TERRA13', 'TERRA', 'FSHOP13', 'FSHOP'
]

# Criptomonedas conocidas
KNOWN_CRYPTOS = ['BTC', 'ETH', 'SOL', 'XRP', 'PAXG', 'USDT', 'USDC', 'ADA', 'DOT', 'MATIC']

# Oro y Materias Primas
KNOWN_COMMODITIES = ['PAXG', 'GLD', 'SLV', 'GDX', 'IAU', 'GOLD']

# ETFs de USA listados en BMV (Sistema Internacional de Cotizaciones - SIC)
US_ETFS_ON_BMV = [
    'VOO', 'VTI', 'SPY', 'QQQ', 'IVV', 'VEA', 'VWO', 'IEMG',
    'VGK', 'EFA', 'EEM', 'VNQ', 'VNQI', 'BND', 'AGG', 'TLT',
    'IWM', 'DIA', 'ARKK', 'XLF', 'XLK', 'XLE', 'XLV', 'SCHD'
]

# ETFs de mercados emergentes
EMERGING_MARKET_ETFS = ['VWO', 'IEMG', 'EEM', 'SCHE']

# ETFs internacionales (desarrollados, no US)
INTERNATIONAL_ETFS = ['VEA', 'VGK', 'EFA', 'IEFA', 'VPL', 'VXUS']


def classify_asset(ticker: str, market: str, asset_type: str) -> Optional[str]:
    """
    Clasifica automaticamente un activo segun ticker y mercado.

    Args:
        ticker: Simbolo del activo (ej. 'AAPL', 'FUNO11.MX', 'BTC')
        market: Mercado ('MX', 'US', 'CRYPTO')
        asset_type: Tipo de activo ('stock', 'crypto')

    Returns:
        Codigo de asset_class o None si no se puede clasificar
    """
    ticker_upper = ticker.upper().replace('.MX', '')

    # 1. Criptomonedas
    if asset_type == 'crypto' or market == 'CRYPTO':
        # PAXG es oro tokenizado, no crypto generica
        if ticker_upper == 'PAXG':
            return 'oro_materias_primas'
        return 'criptomonedas'

    # 2. Verificar si es crypto conocida (por si viene mal clasificada)
    if ticker_upper in KNOWN_CRYPTOS:
        if ticker_upper == 'PAXG':
            return 'oro_materias_primas'
        return 'criptomonedas'

    # 3. Oro y Materias Primas
    if ticker_upper in KNOWN_COMMODITIES:
        return 'oro_materias_primas'

    # 4. FIBRAs (Bienes Raices)
    if market == 'MX':
        # Verificar si es FIBRA conocida
        if any(fibra in ticker_upper for fibra in KNOWN_FIBRAS):
            return 'fibras'

        # Detectar por patron FIBRA* o *FIBRA*
        if 'FIBRA' in ticker_upper:
            return 'fibras'

        # Verificar si es ETF de mercados emergentes listado en BMV
        if ticker_upper in EMERGING_MARKET_ETFS:
            return 'mercados_emergentes'

        # Verificar si es ETF internacional listado en BMV
        if ticker_upper in INTERNATIONAL_ETFS:
            return 'acciones_internacionales'

        # Verificar si es ETF de USA listado en BMV (SIC)
        if ticker_upper in US_ETFS_ON_BMV:
            return 'acciones_usa'

        # Es accion mexicana
        return 'acciones_mexico'

    # 5. Acciones Estados Unidos
    if market == 'US':
        return 'acciones_usa'

    # 6. Por defecto, si no sabemos
    return None


def get_asset_class_info(asset_class: str) -> Dict:
    """
    Obtiene informacion de una clase de activo.

    Args:
        asset_class: Codigo de la clase (ej. 'acciones_mexico')

    Returns:
        Dict con name, emoji, description, swensen_target, color
    """
    return ASSET_CLASSES.get(asset_class, {
        'name': 'Sin Clasificar',
        'emoji': '❓',
        'description': 'No clasificado',
        'swensen_target': 0,
        'color': '#6C757D'  # Gris por defecto
    })


def get_asset_class_color(asset_class: str) -> str:
    """
    Obtiene el color asociado a una clase de activo.

    Args:
        asset_class: Codigo de la clase (ej. 'acciones_mexico')

    Returns:
        String con codigo de color hex (ej. '#006847')
    """
    info = ASSET_CLASSES.get(asset_class, {})
    return info.get('color', '#6C757D')  # Gris por defecto


def get_all_asset_class_colors() -> Dict[str, str]:
    """
    Retorna un diccionario con todos los colores de clases de activo.

    Returns:
        Dict con {asset_class: color_hex}
    """
    return {
        asset_class: info.get('color', '#6C757D')
        for asset_class, info in ASSET_CLASSES.items()
    }


def get_all_asset_classes() -> Dict:
    """
    Retorna todas las clases de activos disponibles.

    Returns:
        Dict con todas las clases y su informacion
    """
    return ASSET_CLASSES


def get_swensen_ideal_allocation() -> Dict[str, int]:
    """
    Retorna la asignacion ideal segun Swensen adaptado a Mexico.
    Usa valores por defecto del diccionario ASSET_CLASSES.

    Returns:
        Dict con {asset_class: porcentaje_ideal}
    """
    return {
        asset_class: info['swensen_target']
        for asset_class, info in ASSET_CLASSES.items()
    }


def get_swensen_target_allocation_from_db(db_session) -> Dict[str, float]:
    """
    Retorna la asignacion objetivo desde BD o valores por defecto.

    Args:
        db_session: Sesion de base de datos SQLAlchemy

    Returns:
        Dict con {asset_class: porcentaje_objetivo}
    """
    from models import SwensenConfig

    configs = db_session.query(SwensenConfig).filter_by(is_active=True).all()

    if configs:
        # Usar configuracion de BD
        return {config.asset_class: float(config.target_percentage) for config in configs}
    else:
        # Usar valores por defecto
        return get_swensen_ideal_allocation()


def initialize_default_swensen_config(db_session) -> None:
    """
    Inicializa configuracion por defecto de Swensen en BD.

    Args:
        db_session: Sesion de base de datos SQLAlchemy
    """
    from models import SwensenConfig

    # Verificar si ya existe configuracion
    existing = db_session.query(SwensenConfig).first()
    if existing:
        return

    # Crear configuracion por defecto
    for asset_class, info in ASSET_CLASSES.items():
        config = SwensenConfig(
            asset_class=asset_class,
            target_percentage=info['swensen_target'],
            is_active=True
        )
        db_session.add(config)

    db_session.commit()


def calculate_rebalancing_recommendations_with_db(
    current_allocation: Dict[str, Dict],
    total_value: float,
    db_session,
    threshold: float = 5.0
) -> List[Dict]:
    """
    Calcula recomendaciones de rebalanceo usando configuracion de BD.

    Args:
        current_allocation: Dict con {asset_class: {'percentage': X, 'value': Y}}
        total_value: Valor total del portfolio
        db_session: Sesion de base de datos
        threshold: Diferencia minima en % para generar recomendacion

    Returns:
        Lista de dicts con recomendaciones ordenadas por severidad
    """
    ideal = get_swensen_target_allocation_from_db(db_session)
    recommendations = []

    for asset_class, ideal_pct in ideal.items():
        current_pct = current_allocation.get(asset_class, {}).get('percentage', 0)
        current_value = current_allocation.get(asset_class, {}).get('value', 0)

        diff_pct = current_pct - ideal_pct

        if abs(diff_pct) > threshold:
            info = get_asset_class_info(asset_class)

            if diff_pct > 0:
                amount_to_adjust = (diff_pct / 100) * total_value
                recommendations.append({
                    'asset_class': asset_class,
                    'name': info['name'],
                    'emoji': info['emoji'],
                    'action': 'reduce',
                    'current_pct': round(current_pct, 2),
                    'ideal_pct': ideal_pct,
                    'diff_pct': round(diff_pct, 2),
                    'amount': round(amount_to_adjust, 2),
                    'current_value': round(current_value, 2),
                    'severity': 'high' if abs(diff_pct) > 15 else 'medium'
                })
            else:
                amount_to_adjust = (abs(diff_pct) / 100) * total_value
                recommendations.append({
                    'asset_class': asset_class,
                    'name': info['name'],
                    'emoji': info['emoji'],
                    'action': 'increase',
                    'current_pct': round(current_pct, 2),
                    'ideal_pct': ideal_pct,
                    'diff_pct': round(diff_pct, 2),
                    'amount': round(amount_to_adjust, 2),
                    'current_value': round(current_value, 2),
                    'severity': 'high' if abs(diff_pct) > 15 else 'medium'
                })

    recommendations.sort(key=lambda x: abs(x['diff_pct']), reverse=True)
    return recommendations


def calculate_investment_allocation(
    new_investment: float,
    current_allocation: Dict[str, Dict],
    total_value: float,
    db_session
) -> List[Dict]:
    """
    Calcula como distribuir nueva inversion para acercarse al modelo ideal.

    Args:
        new_investment: Monto a invertir
        current_allocation: Distribucion actual {asset_class: {'percentage': X, 'value': Y}}
        total_value: Valor actual total del portfolio
        db_session: Sesion de base de datos

    Returns:
        Lista de dicts con distribucion sugerida
    """
    ideal = get_swensen_target_allocation_from_db(db_session)
    future_total = total_value + new_investment

    recommendations = []

    for asset_class, ideal_pct in ideal.items():
        if ideal_pct <= 0:
            continue  # Ignorar clases con 0% objetivo

        current_value = current_allocation.get(asset_class, {}).get('value', 0)
        ideal_future_value = (ideal_pct / 100) * future_total

        # Cantidad que deberia tener en el futuro
        deficit = ideal_future_value - current_value

        if deficit > 0:
            info = get_asset_class_info(asset_class)
            recommendations.append({
                'asset_class': asset_class,
                'name': info['name'],
                'emoji': info['emoji'],
                'current_value': round(current_value, 2),
                'ideal_future_value': round(ideal_future_value, 2),
                'deficit': round(deficit, 2),
                'priority': deficit / new_investment if new_investment > 0 else 0
            })

    # Normalizar para que sume exactamente new_investment
    total_deficit = sum(r['deficit'] for r in recommendations)

    if total_deficit > 0:
        for rec in recommendations:
            rec['suggested_amount'] = round((rec['deficit'] / total_deficit) * new_investment, 2)
            rec['suggested_pct'] = round((rec['suggested_amount'] / new_investment) * 100, 2)
    else:
        # Si no hay deficit, distribuir equitativamente entre clases activas
        active_count = len(recommendations) if recommendations else 1
        for rec in recommendations:
            rec['suggested_amount'] = round(new_investment / active_count, 2)
            rec['suggested_pct'] = round(100 / active_count, 2)

    # Ordenar por prioridad (mayor deficit primero)
    recommendations.sort(key=lambda x: x.get('priority', 0), reverse=True)

    return recommendations


def calculate_rebalancing_recommendations(
    current_allocation: Dict[str, Dict],
    total_value: float,
    threshold: float = 5.0
) -> List[Dict]:
    """
    Calcula recomendaciones de rebalanceo basadas en modelo Swensen.

    Args:
        current_allocation: Dict con {asset_class: {'percentage': X, 'value': Y}}
        total_value: Valor total del portfolio
        threshold: Diferencia minima en % para generar recomendacion (default 5%)

    Returns:
        Lista de dicts con recomendaciones ordenadas por severidad
    """
    ideal = get_swensen_ideal_allocation()
    recommendations = []

    for asset_class, ideal_pct in ideal.items():
        current_pct = current_allocation.get(asset_class, {}).get('percentage', 0)
        current_value = current_allocation.get(asset_class, {}).get('value', 0)

        diff_pct = current_pct - ideal_pct

        if abs(diff_pct) > threshold:  # Diferencia significativa
            info = get_asset_class_info(asset_class)

            if diff_pct > 0:
                # Sobrepeso - reducir
                amount_to_adjust = (diff_pct / 100) * total_value
                recommendations.append({
                    'asset_class': asset_class,
                    'name': info['name'],
                    'emoji': info['emoji'],
                    'action': 'reduce',
                    'current_pct': round(current_pct, 2),
                    'ideal_pct': ideal_pct,
                    'diff_pct': round(diff_pct, 2),
                    'amount': round(amount_to_adjust, 2),
                    'severity': 'high' if abs(diff_pct) > 15 else 'medium'
                })
            else:
                # Subpeso - aumentar
                amount_to_adjust = (abs(diff_pct) / 100) * total_value
                recommendations.append({
                    'asset_class': asset_class,
                    'name': info['name'],
                    'emoji': info['emoji'],
                    'action': 'increase',
                    'current_pct': round(current_pct, 2),
                    'ideal_pct': ideal_pct,
                    'diff_pct': round(diff_pct, 2),
                    'amount': round(amount_to_adjust, 2),
                    'severity': 'high' if abs(diff_pct) > 15 else 'medium'
                })

    # Ordenar por severidad (mayor diferencia primero)
    recommendations.sort(key=lambda x: abs(x['diff_pct']), reverse=True)

    return recommendations


# Testing
if __name__ == '__main__':
    print("=" * 70)
    print("TESTING SISTEMA DE CLASIFICACION SWENSEN")
    print("=" * 70)

    # Test de clasificacion
    test_cases = [
        ('FUNO11.MX', 'MX', 'stock'),
        ('DANHOS13.MX', 'MX', 'stock'),
        ('AGUILASCPO.MX', 'MX', 'stock'),
        ('AMXB.MX', 'MX', 'stock'),
        ('AAPL', 'US', 'stock'),
        ('MSFT', 'US', 'stock'),
        ('GOOGL', 'US', 'stock'),
        ('BTC', 'CRYPTO', 'crypto'),
        ('ETH', 'CRYPTO', 'crypto'),
        ('PAXG', 'CRYPTO', 'crypto'),
    ]

    print("\n📊 CLASIFICACION AUTOMATICA:\n")
    for ticker, market, asset_type in test_cases:
        classification = classify_asset(ticker, market, asset_type)
        info = get_asset_class_info(classification)
        print(f"  {ticker:15s} ({market:6s}) → {info['emoji']} {info['name']}")

    print("\n" + "-" * 70)
    print("\n🎯 MODELO SWENSEN ADAPTADO A MEXICO:\n")
    for asset_class, pct in get_swensen_ideal_allocation().items():
        if pct > 0:
            info = get_asset_class_info(asset_class)
            print(f"  {info['emoji']} {info['name']:30s} → {pct}%")

    print("\n" + "=" * 70)
