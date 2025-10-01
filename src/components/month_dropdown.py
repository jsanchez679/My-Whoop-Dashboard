# import pandas as pd
# from dash import Dash, dcc, html
# from dash.dependencies import Input, Output

# from ..data.loader import DataSchema
# from . import ids

from dash import Dash, html, dcc
from src.components import ids

def render(app: Dash) -> html.Div:
    return html.Div(
        children=[
            html.Label("Select Month:", style={"width": "120px", "margin-left": "10px", "margin-right": "10px", 
                                              "align-self": "center", "flex": "0 0 auto" }),
            dcc.Dropdown(
                id=ids.MONTH_DROPDOWN,
                multi=True,
                placeholder="Select month(s)...", 
                style={"flex": "1", "margin-right": "10px"}, 
            ),
            html.Button(
                className="dropdown-button",
                children=["Select All"],
                id=ids.SELECT_ALL_MONTHS_BUTTON,
                n_clicks=0,
                style={"width": "120px",         # fixed width for button
                        "flex": "0 0 auto"}
            ),
        ],
        style={
                "display": "flex",
                "flexDirection": "row",
                "alignItems": "center",   # vertically centers label/button with dropdown
                "width": "48%",
                "margin-right": "2%",
            },
    )

# def render(app: Dash, data: pd.DataFrame) -> html.Div:
#     all_months: list[str] = data[DataSchema.MONTH].tolist()
#     unique_months = sorted(set(all_months))

#     @app.callback(
#         Output(ids.MONTH_DROPDOWN, "value"),
#         [
#             Input(ids.YEAR_DROPDOWN, "value"),
#             Input(ids.SELECT_ALL_MONTHS_BUTTON, "n_clicks"),
#         ],
#     )
#     def select_all_months(years: list[str], _: int) -> list[str]:
#         filtered_data = data.query("year in @years")
#         return sorted(set(filtered_data[DataSchema.MONTH].tolist()))

#     return html.Div(
#         children=[
#             html.H6("Month"),
#             dcc.Dropdown(
#                 id=ids.MONTH_DROPDOWN,
#                 options=[{"label": month, "value": month} for month in unique_months],
#                 value=unique_months,
#                 multi=True,
#             ),
#             html.Button(
#                 className="dropdown-button",
#                 children=["Select All"],
#                 id=ids.SELECT_ALL_MONTHS_BUTTON,
#                 n_clicks=0,
#             ),
#         ]
#     )
