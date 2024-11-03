import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output


class TradingBotDashboard:
    """
    Clase para crear y manejar un dashboard de Dash para visualizar los KPIs (Indicadores Clave de Rendimiento)
    de un bot de trading.

    Attributes:
        data_manager: Una instancia de una clase que gestiona los datos para el dashboard.
        app: La aplicación Dash que sirve el dashboard.

    Methods:
        setup_layout: Configura el layout inicial de la aplicación Dash.
        register_callbacks: Registra los callbacks para interactividad en la aplicación Dash.
        run_server: Ejecuta el servidor Dash para visualizar el dashboard.
    """

    def __init__(self, data_manager):
        """
        Inicializa la instancia de TradingBotDashboard con un gestor de datos y configura la aplicación Dash.

        Args:
            data_manager: Una instancia de una clase que gestiona los datos para el dashboard.
        """
        self.data_manager = data_manager
        self.app = dash.Dash(__name__)
        self.setup_layout()
        self.register_callbacks()

    def setup_layout(self):
        """
        Configura el layout de la aplicación Dash, incluyendo un título, un contenedor para KPIs, un Dropdown para
        la selección de KPIs y un Graph para visualizar los datos de los KPIs.
        """
        self.app.layout = html.Div(
            children=[
                html.H1(children="Dashboard de Trading Bot"),
                html.Div(id="kpis-container", children=[]),
                dcc.Dropdown(
                    id="kpi-selection",
                    options=[
                        {"label": "Ganancia Total (USD)", "value": "total_profit_usd"},
                        {
                            "label": "Inversión Total (USD)",
                            "value": "total_investment_usd",
                        },
                        # Más opciones de KPIs aquí
                    ],
                    value="total_profit_usd",
                ),
                dcc.Graph(id="kpi-graph"),
            ]
        )

    def register_callbacks(self):
        """
        Registra los callbacks para la aplicación Dash, permitiendo interactividad como la actualización
        de los KPIs mostrados y la generación del gráfico basado en la selección del usuario.
        """

        @self.app.callback(
            Output("kpis-container", "children"), [Input("kpi-selection", "value")]
        )
        def update_kpis(_):
            """
            Actualiza el contenedor de KPIs basado en la selección del usuario.

            Args:
                _: El valor seleccionado en el Dropdown de KPIs.

            Returns:
                Una lista de componentes html.Div para cada KPI.
            """
            current_kpis = self.data_manager.get_current_kpis()
            return [html.Div(f"{kpi}: {value}") for kpi, value in current_kpis.items()]

        @self.app.callback(
            Output("kpi-graph", "figure"), [Input("kpi-selection", "value")]
        )
        def update_graph(selected_kpi):
            """
            Actualiza el gráfico basado en el KPI seleccionado por el usuario.

            Args:
                selected_kpi: El KPI seleccionado para ser visualizado.

            Returns:
                Un diccionario con los datos y la configuración del layout para el gráfico.
            """
            kpi_df = self.data_manager.get_kpi_history(selected_kpi)

            return {
                "data": [
                    {
                        "x": kpi_df["date"],
                        "y": kpi_df[selected_kpi],
                        "type": "line",
                        "name": selected_kpi,
                    },
                ],
                "layout": {"title": f"Historial de {selected_kpi}"},
            }

    def run_server(self):
        """
        Ejecuta el servidor Dash, haciendo accesible el dashboard en el navegador.
        """
        self.app.run_server(debug=True)
