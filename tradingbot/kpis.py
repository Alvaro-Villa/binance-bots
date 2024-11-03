from datetime import datetime
from data_manager import TradingDataManager


class TradingBotKPIs:
    """
    Clase para calcular y presentar los principales KPIs de un bot de trading.

    Args:
        db_path (str): La ruta al archivo de base de datos SQLite que contiene las transacciones.

    Attributes:
        data_manager (TradingDataManager): Instancia de TradingDataManager para acceder a los datos de trading.
    """

    def __init__(self, db_path: str):
        self.data_manager = TradingDataManager(db_path)

    def calculate_total_return(self):
        """
        Calcula el retorno total de las operaciones de trading.

        Returns:
            float: El retorno total en porcentaje.
        """
        closed_positions = self.data_manager.get_closed_positions()
        total_invested = sum(pos["BuyAmountUSD"] for pos in closed_positions)
        total_returned = sum(pos["SellAmountUSD"] for pos in closed_positions)

        if total_invested == 0:
            return 0
        total_return = ((total_returned - total_invested) / total_invested) * 100
        return total_return

    def calculate_win_rate(self):
        """
        Calcula el porcentaje de operaciones ganadoras.

        Returns:
            float: El porcentaje de operaciones ganadoras.
        """
        closed_positions = self.data_manager.get_closed_positions()
        wins = sum(1 for pos in closed_positions if pos["Profit"] > 0)
        total = len(closed_positions)

        if total == 0:
            return 0
        win_rate = (wins / total) * 100
        return win_rate

    def calculate_max_drawdown(self):
        """
        Calcula el drawdown máximo experimentado.

        Returns:
            float: El drawdown máximo en porcentaje.
        """
        # Este método requeriría una implementación más compleja que analice la serie temporal
        # de los valores de la cartera para identificar el drawdown máximo.
        # Aquí se presenta una estructura básica como ejemplo.
        return -10.0  # Ejemplo simplificado

    # Puedes añadir más métodos para calcular otros KPIs relevantes según tus necesidades.

    def calculate_unrealized_losses(self):
        """
        Calcula las pérdidas no realizadas de las operaciones abiertas.

        Retorna el total de pérdidas (o ganancias) no realizadas en USD y el número de posiciones que actualmente están en pérdida.

        Returns:
            tuple: Contiene el total de pérdidas no realizadas en USD y el número de posiciones en pérdida.
        """
        open_positions = self.data_manager.get_open_positions()
        total_unrealized_losses = 0
        losing_positions_count = 0

        for position in open_positions:
            current_price = float(
                self.client.get_symbol_ticker(symbol=position["Symbol"])["price"]
            )
            buy_price = position["BuyPrice"]
            amount_btc = position["AmountBTC"]
            unrealized_loss = (buy_price - current_price) * amount_btc

            if unrealized_loss > 0:
                total_unrealized_losses += unrealized_loss
                losing_positions_count += 1

        return total_unrealized_losses, losing_positions_count

    def get_total_profit(self):
        closed_positions = self.data_manager.get_closed_positions()
        total_profit = sum(pos["Profit"] for pos in closed_positions)
        return total_profit

    def get_total_investment(self):
        closed_positions = self.data_manager.get_closed_positions()
        total_investment = sum(pos["BuyAmountUSD"] for pos in closed_positions)
        return total_investment

    def get_total_operations(self):
        closed_positions = self.data_manager.get_closed_positions()
        return len(closed_positions)

    def get_winning_trades(self):
        closed_positions = self.data_manager.get_closed_positions()
        winning_trades = sum(1 for pos in closed_positions if pos["Profit"] > 0)
        return winning_trades

    def get_losing_trades(self):
        closed_positions = self.data_manager.get_closed_positions()
        losing_trades = sum(1 for pos in closed_positions if pos["Profit"] <= 0)
        return losing_trades

    def get_average_profit_per_trade(self):
        total_profit = self.get_total_profit()
        total_operations = self.get_total_operations()
        average_profit_per_trade = (
            total_profit / total_operations if total_operations > 0 else 0
        )
        return average_profit_per_trade

    def get_roi_percentage(self):
        total_profit = self.get_total_profit()
        total_investment = self.get_total_investment()
        roi_percentage = (
            (total_profit / total_investment) * 100 if total_investment > 0 else 0
        )
        return roi_percentage

    def get_performance_metrics(self):
        """
        Calcula y retorna métricas clave de rendimiento (KPIs) para el bot de trading.

        Returns:
            dict: Un diccionario de KPIs incluyendo ganancias totales, número de operaciones, ROI, y más.
        """

        kpis = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_profit_usd": self.get_total_profit(),
            "total_investment_usd": self.get_total_investment(),
            "total_operations": self.get_total_operations(),
            "winning_trades": self.get_winning_trades(),
            "losing_trades": self.get_losing_trades(),
            "average_profit_per_trade_usd": self.get_average_profit_per_trade(),
            "roi_percentage": self.get_roi_percentage(),
            "unralized_losses": self.calculate_unrealized_losses()[0],
            "losing_positions_count": self.calculate_unrealized_losses()[1],
            "calculate_win_rate": self.calculate_win_rate(),
            "calculate_total_return": self.calculate_total_return(),
        }
        self.data_manager.insert_kpis(kpis)

        return kpis
