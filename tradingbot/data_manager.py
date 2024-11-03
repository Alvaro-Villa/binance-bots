import sqlite3
from datetime import datetime


class TradingDataManager:
    """
    Gestiona la interacción con la base de datos para registrar y recuperar
    transacciones de compra/venta y KPIs para un bot de trading.

    Attributes:
        db_path (str): Ruta al archivo de la base de datos SQLite.
        conn (sqlite3.Connection): Conexión a la base de datos SQLite.

    Args:
        db_path (str): Ruta al archivo de la base de datos. Por defecto, 'trading_data.db'.
    """

    def __init__(self, db_path: str = "trading_data.db") -> None:
        """
        Inicializa la conexión a la base de datos y crea las tablas necesarias.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self) -> None:
        """
        Crea las tablas en la base de datos si no existen: Open, Close y KPI.
        """
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Open (
                Id INTEGER PRIMARY KEY,
                BuyDate TEXT NOT NULL,
                BuyAmountUSD REAL NOT NULL,
                AmountBTC REAL NOT NULL,
                BuyPrice REAL NOT NULL
            );
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Close (
                Id INTEGER PRIMARY KEY,
                BuyDate TEXT NOT NULL,
                SellDate TEXT NOT NULL,
                BuyAmountUSD REAL NOT NULL,
                SellAmountUSD REAL NOT NULL,
                AmountBTC REAL NOT NULL,
                BuyPrice REAL NOT NULL,
                SellPrice REAL NOT NULL,
                Profit REAL NOT NULL
            );
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS KPI (
                Date TEXT PRIMARY KEY,
                TotalProfit REAL,
                TotalInvestment REAL,
                TotalOperations INTEGER,
                WinningTrades INTEGER,
                LosingTrades INTEGER,
                AverageProfitPerTrade REAL,
                ROI REAL
            );
            """
        )
        self.conn.commit()

    def record_buy(
        self, buy_amount_usd: float, amount_btc: float, buy_price: float
    ) -> None:
        """
        Registra una transacción de compra en la base de datos.

        Args:
            buy_amount_usd (float): Cantidad de la compra en USD.
            amount_btc (float): Cantidad de BTC comprada.
            buy_price (float): Precio de compra por BTC.
        """
        buy_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute(
            """
            INSERT INTO Open (BuyDate, BuyAmountUSD, AmountBTC, BuyPrice) VALUES (?, ?, ?, ?);
            """,
            (buy_date, buy_amount_usd, amount_btc, buy_price),
        )
        self.conn.commit()

    def record_sell(self, id: int, sell_amount_usd: float, sell_price: float) -> None:
        """
        Registra una transacción de venta en la base de datos, moviendo la transacción
        de la tabla Open a la tabla Close y calculando el beneficio.

        Args:
            id (int): Identificador de la transacción de compra relacionada.
            sell_amount_usd (float): Cantidad de la venta en USD.
            sell_price (float): Precio de venta por BTC.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Open WHERE Id = ?", (id,))
        transaction = cursor.fetchone()

        if transaction:
            buy_date, buy_amount_usd, amount_btc, buy_price = transaction[1:]
            sell_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            profit = sell_amount_usd - buy_amount_usd

            cursor.execute(
                """
                INSERT INTO Close (BuyDate, SellDate, BuyAmountUSD, SellAmountUSD, AmountBTC, BuyPrice, SellPrice, Profit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    buy_date,
                    sell_date,
                    buy_amount_usd,
                    sell_amount_usd,
                    amount_btc,
                    buy_price,
                    sell_price,
                    profit,
                ),
            )
            cursor.execute("DELETE FROM Open WHERE Id = ?", (id,))
            self.conn.commit()

    def close(self) -> None:
        """
        Cierra la conexión con la base de datos.
        """
        self.conn.close()

    def get_open_positions(self) -> list:
        """
        Recupera todas las posiciones abiertas de la tabla Open.

        Returns:
            list: Lista de diccionarios con los detalles de las posiciones abiertas.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Open")
        open_positions = cursor.fetchall()

        positions = [
            {
                "Id": position[0],
                "BuyDate": position[1],
                "BuyAmountUSD": position[2],
                "AmountBTC": position[3],
                "BuyPrice": position[4],
            }
            for position in open_positions
        ]
        return positions

    def get_close_positions(self) -> list:
        """
        Recupera todas las posiciones abiertas de la tabla Open.

        Returns:
            list: Lista de diccionarios con los detalles de las posiciones abiertas.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Close")
        close_positions = cursor.fetchall()

        positions = [
            {
                "BuyDate": position[1],
                "SellDate": position[2],
                "BuyAmountUSD": position[3],
                "SellAmountUSD": position[4],
                "AmountBTC": position[5],
                "BuyPrice": position[6],
                "SellPrice": position[7],
                "Profit": round(position[8], 2),
            }
            for position in close_positions
        ]
        return positions

    def insert_kpis(self, kpis: dict) -> None:
        """
        Inserta los KPIs calculados en la base de datos.

        Args:
            kpis (dict): Diccionario con los KPIs calculados.
        """
        self.conn.execute(
            """
            INSERT INTO KPI (Date, TotalProfit, TotalInvestment, TotalOperations, WinningTrades, LosingTrades, AverageProfitPerTrade, ROI)
            VALUES (:Date, :TotalProfit, :TotalInvestment, :TotalOperations, :WinningTrades, :LosingTrades, :AverageProfitPerTrade, :ROI);
            """,
            kpis,
        )
        self.conn.commit()

    def get_kpis(self) -> list:
        """
        Recupera los KPIs registrados de la base de datos.

        Returns:
            list: Lista de diccionarios con los KPIs registrados.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM KPI ORDER BY Date DESC")
        kpis = cursor.fetchall()

        return [
            {
                "Date": kpi[0],
                "TotalProfit": kpi[1],
                "TotalInvestment": kpi[2],
                "TotalOperations": kpi[3],
                "WinningTrades": kpi[4],
                "LosingTrades": kpi[5],
                "AverageProfitPerTrade": kpi[6],
                "ROI": kpi[7],
            }
            for kpi in kpis
        ]
