import requests
import datetime
import time
import os
from datetime import datetime


def set_working_directory_to_tradingbot() -> None:
    """
    Cambia el directorio de trabajo actual al directorio que contiene la carpeta 'TradingBot'.

    La función busca en la ruta actual del directorio de trabajo para encontrar la carpeta 'TradingBot'.
    Si la encuentra, cambia el directorio de trabajo a ese nivel. Si no, imprime un mensaje de error.

    Raises:
        ValueError: Si la carpeta 'TradingBot' no se encuentra en ninguna parte de la ruta del directorio actual.
    """
    # Obtiene el directorio actual
    current_dir = os.getcwd()
    # Separa el directorio actual en partes
    path_parts = current_dir.split(os.sep)

    # Busca el índice de la carpeta "TradingBot" en la ruta actual
    try:
        tradingbot_index = path_parts.index("TradingBot")
    except ValueError as e:
        print("La carpeta 'TradingBot' no se encontró en la ruta actual.")
        raise e

    # Re-ensambla la ruta al nivel de la carpeta "TradingBot"
    tradingbot_path = os.sep.join(path_parts[: tradingbot_index + 1])

    # Cambia el directorio de trabajo al nivel de la carpeta "TradingBot"
    os.chdir(tradingbot_path)
    print(f"El directorio de trabajo se cambió a: {tradingbot_path}")


def verificar_sincronizacion_con_binance():
    try:
        # URL del endpoint para obtener el tiempo del servidor de Binance
        url = "https://api.binance.com/api/v3/time"

        # Realizar la solicitud a la API de Binance
        response = requests.get(url)
        response.raise_for_status()  # Asegurarse de que la solicitud fue exitosa

        # Extraer el tiempo del servidor de la respuesta
        server_time = response.json()["serverTime"]

        # Convertir el tiempo del servidor en milisegundos a un objeto datetime
        server_time = datetime.datetime.utcfromtimestamp(server_time / 1000.0)

        # Obtener la hora actual del sistema en UTC
        local_time = datetime.datetime.utcnow()

        # Calcular la diferencia en segundos
        diferencia = (local_time - server_time).total_seconds()

        # Imprimir los resultados
        print(f"Hora del servidor de Binance (UTC): {server_time}")
        print(f"Hora local del sistema (UTC): {local_time}")
        print(f"Diferencia de tiempo: {diferencia} segundos")

        # Considerar una pequeña tolerancia, por ejemplo, 1 segundo
        if abs(diferencia) > 1:
            print(
                "El reloj del sistema parece estar desincronizado con el servidor de Binance."
            )
        else:
            print(
                "El reloj del sistema está sincronizado con el servidor de Binance dentro de una tolerancia aceptable."
            )
    except Exception as e:
        print(
            f"Hubo un error al intentar verificar la sincronización con el servidor de Binance: {e}"
        )


def obtener_diferencia_de_tiempo() -> float:
    """
    Calcula la diferencia de tiempo en segundos entre el sistema local y el servidor de Binance.

    Realiza una petición a la API de Binance para obtener el tiempo del servidor y compara este tiempo
    con el tiempo local del sistema. La diferencia se devuelve en segundos y puede ser positiva
    si el tiempo local está adelantado o negativa si está atrasado.

    Returns:
        float: La diferencia de tiempo en segundos entre el tiempo local y el tiempo del servidor de Binance.
    """
    url = "https://api.binance.com/api/v3/time"
    response = requests.get(url)
    server_time = (
        response.json()["serverTime"] / 1000.0
    )  # Convertir milisegundos a segundos
    local_time = time.time()
    return local_time - server_time
