import math
from typing import Optional, Dict
from binance.client import Client
from binance.exceptions import BinanceAPIException
from .data_manager import TradingDataManager


class BinanceBot:
    """
    Clase base para interactuar con la API de Binance, permitiendo ejecutar órdenes de
    compra y venta en el mercado de criptomonedas.

    Attributes:
        client (Client): Una instancia del cliente de la API de Binance configurada con la API key y el API secret.

    Args:
        api_key (str): La llave API proporcionada por Binance.
        api_secret (str): El secreto API proporcionado por Binance.
    """

    def __init__(self, api_key: str, api_secret: str) -> None:
        """
        Inicializa una instancia de BinanceBot con las credenciales para interactuar con la API de Binance.
        """
        self.client = Client(api_key, api_secret)

    def execute_order(
        self, symbol: str, amount: float, is_buy: bool, is_amount_in_usd: bool = False
    ) -> Optional[Dict]:
        """
        Ejecuta una orden de compra o venta en el mercado para un símbolo específico, permitiendo
        operar en términos de la criptomoneda misma o su equivalente en USD.

        Args:
            symbol (str): El símbolo del par de trading, e.g., 'BTCUSDT'.
            amount (float): La cantidad a operar, en criptomoneda o USD.
            is_buy (bool): Especifica si la orden es de compra (True) o de venta (False).
            is_amount_in_usd (bool): Indica si la cantidad especificada está en USD (True) o en la criptomoneda del par (False).

        Returns:
            Optional[Dict]: La respuesta de la API de Binance si la operación es exitosa, None de lo contrario.

        Raises:
            BinanceAPIException: Si ocurre un error al realizar la operación con la API de Binance.
        """
        try:
            if is_amount_in_usd:
                price = float(self.client.get_symbol_ticker(symbol=symbol)["price"])
                amount = amount / price

            info = self.client.get_symbol_info(symbol)
            step_size = float(
                next(filter(lambda f: f["filterType"] == "LOT_SIZE", info["filters"]))[
                    "stepSize"
                ]
            )
            amount = self.round_down(amount, -math.log10(step_size))

            order_func = (
                self.client.order_market_buy
                if is_buy
                else self.client.order_market_sell
            )
            order = order_func(symbol=symbol, quantity=amount)
            return order
        except BinanceAPIException as e:
            print(f"Error al realizar la operación: {e}")
            return None

    def get_current_price(self, symbol):
        return float(self.client.get_symbol_ticker(symbol=symbol)["price"])

    def get_account_balances(self) -> Dict[str, float]:
        """
        Obtiene los saldos de la cuenta en criptomonedas y su equivalente en USD.

        Returns:
            Dict[str, float]: Un diccionario con las criptomonedas como claves y una tupla como valor,
            donde el primer elemento es el saldo en la criptomoneda y el segundo elemento es el equivalente en USD.

        Raises:
            BinanceAPIException: Si ocurre un error al realizar la operación con la API de Binance.
        """
        try:
            # Obtiene todos los balances de la cuenta
            account_info = self.client.get_account()
            balances = {
                balance["asset"]: float(balance["free"])
                for balance in account_info["balances"]
                if float(balance["free"]) > 0
            }

            # Preparar el diccionario para los saldos con su equivalente en USD
            balances_in_usd = {}

            for asset, balance in balances.items():
                if asset != "USDT":
                    # Consultar el precio actual de la criptomoneda en USD
                    symbol = asset + "USDT"
                    try:
                        price = self.client.get_symbol_ticker(symbol=symbol)["price"]
                    except BinanceAPIException:
                        print(f"No se encontró precio para {asset}, omitiendo...")
                        continue
                    if float(price) * balance > 10:
                        balances_in_usd[asset] = (balance, float(price) * balance)
                else:
                    # Si el activo es USD, no es necesario convertirlo
                    balances_in_usd["USD"] = (balance, balance)

            return balances_in_usd
        except BinanceAPIException as e:
            print(f"Error al obtener los balances de la cuenta: {e}")
            return {}

    @staticmethod
    def round_down(value: float, decimals: int) -> float:
        """
        Redondea hacia abajo el valor a la cantidad de decimales especificada, útil para ajustar
        las cantidades de criptomoneda a las restricciones de precisión de Binance.

        Args:
            value (float): El valor a redondear hacia abajo.
            decimals (int): El número de decimales a los que redondear el valor.

        Returns:
            float: El valor redondeado hacia abajo.
        """
        factor = 10**decimals
        return math.floor(value * factor) / factor


class PriceTrendTradingBot(BinanceBot):
    """
    Bot de trading basado en tendencias para operar en Binance. Este bot compara
    el precio de un símbolo específico de un día para el otro. Si el precio ha aumentado,
    realiza una compra. También verifica y cierra posiciones abiertas basadas en la tendencia
    de los precios y los registra adecuadamente.

    Args:
        api_key (str): La llave API para Binance.
        api_secret (str): El secreto API para Binance.
        db_path (str): La ruta al archivo de base de datos SQLite para registrar operaciones.
        invest_amount_usd (float): La cantidad de USD a invertir en cada operación.
    """

    def __init__(
        self, api_key: str, api_secret: str, db_path: str, invest_amount_usd: float
    ) -> None:
        super().__init__(api_key, api_secret)
        self.data_manager = TradingDataManager(db_path)
        self.invest_amount_usd = invest_amount_usd

    def compare_and_buy(self, symbol: str) -> None:
        """
        Compara el precio de cierre de ayer con  para un el precio de compra mínimo de las posiciones abierta de un símbolo específico.
        Si el precio de hoy es mayor, realiza una compra usando el monto de inversión definido.

        Args:
            symbol (str): El símbolo del par de trading, por ejemplo, 'BTCUSDT'.
        """
        positions = self.data_manager.get_open_positions()
        min_buy_price = self._get_minimum_buy_price(positions)
        prices = self.client.get_historical_klines(
            symbol, self.client.KLINE_INTERVAL_1DAY, "2 day ago UTC"
        )
        price_yesterday = float(prices[0][4])
        price_today = float(prices[1][4])

        if (
            (price_today * 1.01 < price_yesterday)
            and (price_today * 1.01 < min_buy_price)
            and (self.invest_amount_usd < self.get_account_balances()["USD"][1])
        ):
            order = self.execute_order(
                symbol, self.invest_amount_usd, is_buy=True, is_amount_in_usd=True
            )
            if order:
                print(f"Compra realizada: {order}")
                self.data_manager.record_buy(
                    self.invest_amount_usd,
                    order["fills"][0]["qty"],
                    order["fills"][0]["price"],
                )

    def check_and_close_positions(self, symbol: str) -> None:
        """
        Revisa todas las posiciones abiertas para un símbolo específico. Si el precio actual
        es mayor que el precio de compra, cierra la posición vendiendo al precio de mercado.

        Args:
            symbol (str): El símbolo del par de trading, por ejemplo, 'BTCUSDT'.
        """
        open_positions = self.data_manager.get_open_positions()
        current_price = float(self.client.get_symbol_ticker(symbol=symbol)["price"])

        for position in open_positions:
            if current_price > float(position["BuyPrice"]) * 1.01:
                amount_to_sell = position["AmountBTC"] 
                order = self.execute_order(
                    symbol, amount_to_sell, is_buy=False, is_amount_in_usd=False
                )
                if order:
                    print(f"Posición cerrada: {order}")
                    self.data_manager.record_sell(
                        position["Id"],
                        amount_to_sell * current_price,
                        current_price,
                    )

    @staticmethod
    def _get_minimum_buy_price(positions):
        # Verificar si la lista está vacía
        if not positions:
            return None  # O podrías manejar de otra manera como levantar una excepción

        # Extraer todos los precios de compra en una lista
        buy_prices = [
            position["BuyPrice"] for position in positions if "BuyPrice" in position
        ]

        # Obtener el precio mínimo
        if buy_prices:  # Verificar si la lista de precios no está vacía
            return min(buy_prices)
        else:
            return None  # Si no hay precios, retorna None o maneja de otra manera


class PriceTrendTradingBotTest(PriceTrendTradingBot):
    """
    Versión de prueba del bot de trading basado en tendencias para operar en Binance.
    Este bot utiliza datos de mercado reales pero simula las operaciones sin ejecutarlas,
    utilizando el método create_test_order de la API de Binance.
    """

    def execute_order(
        self, symbol: str, amount: float, is_buy: bool, is_amount_in_usd: bool = False
    ) -> dict:
        """
        Simula la ejecución de una orden de compra o venta en el mercado para un símbolo específico,
        utilizando el método create_test_order de la API de Binance para no realizar transacciones reales.

        Args:
            symbol (str): El símbolo del par de trading, e.g., 'BTCUSDT'.
            amount (float): La cantidad a operar, en criptomoneda o USD.
            is_buy (bool): Especifica si la orden es de compra (True) o de venta (False).
            is_amount_in_usd (bool): Indica si la cantidad especificada está en USD (True) o en la criptomoneda del par (False).

        Returns:
            dict: Un diccionario simulado que representa la respuesta de una orden que se habría ejecutado.
        """
        # Determina la cantidad en la criptomoneda del par si se especificó en USD
        if is_amount_in_usd:
            price = float(self.client.get_symbol_ticker(symbol=symbol)["price"])
            quantity = amount / price
        else:
            quantity = amount

        # Construye los parámetros de la orden
        order_params = {
            "symbol": symbol,
            "side": self.client.SIDE_BUY if is_buy else self.client.SIDE_SELL,
            "type": self.client.ORDER_TYPE_MARKET,
            "quantity": quantity,
        }

        try:
            # Simula la orden sin ejecutarla realmente
            response = self.client.create_test_order(**order_params)
            print(
                f"Orden simulada: {'Compra' if is_buy else 'Venta'} de {quantity} {symbol}"
            )
            return response
        except BinanceAPIException as e:
            print(f"Error al simular la orden: {e}")
            return {}
