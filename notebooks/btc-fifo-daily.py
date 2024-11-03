# trading_daily.py
import os
import sys

os.chdir("C://Users//Usuario//Desktop//Proyectos//TradingBot")
sys.path.append("C://Users//Usuario//Desktop//Proyectos//TradingBot")

import datetime
import json
from tradingbot.bots import PriceTrendTradingBot


# Abrir un archivo JSON y cargar su contenido en una variable
with open("config/config.json", "r") as archivo:
    config = json.load(archivo)

# Configura tus claves API de Binance aquí
api_key = config["api-key"]
api_secret = config["api-secret"]
db_path = config["db_path"]
invest_amount_usd = config[
    "invest_amount_usd"
]  # Cantidad de USD que deseas invertir en cada operación
symbol = config["symbol"]  # Define el par de criptomonedas que deseas operar

# Crea una instancia de tu bot
bot = PriceTrendTradingBot(api_key, api_secret, db_path, invest_amount_usd)

print(f"[{datetime.datetime.now()}] - Iniciando operaciones de trading diarias...")

# Ejecuta las funcionalidades de tu bot
try:
    bot.compare_and_buy(symbol)
    bot.check_and_close_positions(symbol)
    print(f"[{datetime.datetime.now()}] - Operaciones de trading completadas.")
except Exception as e:
    print(f"Ocurrió un error durante la ejecución del bot: {e}")
