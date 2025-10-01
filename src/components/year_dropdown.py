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
            html.Label("Select Year:", style={"width": "120px", "margin-left": "10px", "margin-right": "10px", 
                                              "align-self": "center", "flex": "0 0 auto" }),
            dcc.Dropdown(
                id=ids.YEAR_DROPDOWN,
                multi=True,
                placeholder="Select year(s)...",
                style={ "flex": "1", "margin-right": "10px"}
            ),
            html.Button(
                className="dropdown-button",
                children=["Select All"],
                id=ids.SELECT_ALL_YEARS_BUTTON,
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
#     all_years: list[str] = data[DataSchema.YEAR].tolist()
#     unique_years = sorted(set(all_years), key=int)

#     @app.callback(
#         Output(ids.YEAR_DROPDOWN, "value"),
#         Input(ids.SELECT_ALL_YEARS_BUTTON, "n_clicks"),
#     )
#     def select_all_years(_: int) -> list[str]:
#         return unique_years

#     return html.Div(
#         children=[
#             html.H6("Year"),
#             dcc.Dropdown(
#                 id=ids.YEAR_DROPDOWN,
#                 options=[{"label": year, "value": year} for year in unique_years],
#                 value=unique_years,
#                 multi=True,
#             ),
#             html.Button(
#                 className="dropdown-button",
#                 children=["Select All"],
#                 id=ids.SELECT_ALL_YEARS_BUTTON,
#                 n_clicks=0,
#             ),
#         ]
#     )
