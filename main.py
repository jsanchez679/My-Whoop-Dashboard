from dash import Dash, Input, Output, State, html
from dash_bootstrap_components.themes import MATERIA
import plotly.graph_objects as go
import pandas as pd

# Local Imports
from src.components.layout import (create_layout, render_overview_tab, 
                                   render_trends_tab, create_cycle_overlay_plot)
from src.components import ids
from src.data.loader import parse_contents, load_data, process_data

def main() -> None:
    # load the data and create the data manager
    # data = load_transaction_data(DATA_PATH)

    # Initialize the Dash app
    app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[MATERIA])
    app.title = "Whoop Cycle Analysis Dashboard"

    # Define the app layout
    app.layout = create_layout(app)#, data)

    # Callback for file uploads
    @app.callback(
        [Output(ids.STORED_DATA_PHYSIOLOGICAL, 'children'),
        Output(ids.UPLOAD_STATUS_PHYSIOLOGICAL, 'children')],
        [Input(ids.UPLOAD_PHYSIOLOGICAL, 'contents')],
        [State(ids.UPLOAD_PHYSIOLOGICAL, 'filename')]
    )
    def update_physiological_data(contents: str, filename: str):
        if contents is not None:
            df = parse_contents(contents, filename)
            if df is not None:
                return df.to_json(date_format='iso', orient='split'), f"✓ {filename} uploaded successfully"
            else:
                return None, f"✗ Error uploading {filename}"
        return None, ""

    @app.callback(
        [Output(ids.STORED_DATA_JOURNAL, 'children'),
        Output(ids.UPLOAD_STATUS_JOURNAL, 'children')],
        [Input(ids.UPLOAD_JOURNAL, 'contents')],
        [State(ids.UPLOAD_JOURNAL, 'filename')]
    )
    def update_journal_data(contents: str, filename: str):
        if contents is not None:
            df = parse_contents(contents, filename)
            if df is not None:
                return df.to_json(date_format='iso', orient='split'), f"✓ {filename} uploaded successfully"
            else:
                return None, f"✗ Error uploading {filename}"
        return None, ""

    @app.callback(
        [Output(ids.STORED_DATA_SLEEP, 'children'),
        Output(ids.UPLOAD_STATUS_SLEEP, 'children')],
        [Input(ids.UPLOAD_SLEEP, 'contents')],
        [State(ids.UPLOAD_SLEEP, 'filename')]
    )
    def update_sleep_data(contents: str, filename: str):
        if contents is not None:
            df = parse_contents(contents, filename)
            if df is not None:
                return df.to_json(date_format='iso', orient='split'), f"✓ {filename} uploaded successfully"
            else:
                return None, f"✗ Error uploading {filename}"
        return None, ""

    @app.callback(
        [Output(ids.STORED_DATA_WORKOUTS, 'children'),
        Output(ids.UPLOAD_STATUS_WORKOUTS, 'children')],
        [Input(ids.UPLOAD_WORKOUTS, 'contents')],
        [State(ids.UPLOAD_WORKOUTS, 'filename')]
    )
    def update_workouts_data(contents: str, filename: str):
        if contents is not None:
            df = parse_contents(contents, filename)
            if df is not None:
                return df.to_json(date_format='iso', orient='split'), f"✓ {filename} uploaded successfully"
            else:
                return None, f"✗ Error uploading {filename}"
        return None, ""

    # Callback to process data and show main content
    @app.callback(
        [Output(ids.PROCESSED_DATA, 'children'),
        Output(ids.MAIN_CONTENT, 'style')],
        [Input(ids.STORED_DATA_PHYSIOLOGICAL, 'children'),
        Input(ids.STORED_DATA_JOURNAL, 'children'),
        Input(ids.STORED_DATA_SLEEP, 'children'),
        Input(ids.STORED_DATA_WORKOUTS, 'children')]
    )
    def process_and_show_data(phys_data: pd.DataFrame, journal_data: pd.DataFrame, 
                                sleep_data: pd.DataFrame, workout_data: pd.DataFrame):
        if phys_data is not None and journal_data is not None:
            # Load data
            phys_df = pd.read_json(phys_data, orient='split')
            journal_df = pd.read_json(journal_data, orient='split')
            sleep_df = pd.read_json(sleep_data, orient='split') if sleep_data else None
            workout_df = pd.read_json(workout_data, orient='split') if workout_data else None
            
            # Process data
            processed_df = process_data(phys_df, journal_df, sleep_df, workout_df)
            
            if processed_df is not None:
                return processed_df.to_json(date_format='iso', orient='split'), {'display': 'block'}
        
        return None, {'display': 'none'}

    # Callback for tab content
    @app.callback(
        Output(ids.TAB_CONTENT, 'children'),
        [Input(ids.TABS, 'value'),
        Input(ids.PROCESSED_DATA, 'children')]
    )
    def render_tab_content(active_tab, processed_data):
        if processed_data is None:
            return html.Div("Please upload physiological and journal data to continue.")
        
        df = load_data(processed_data=processed_data)
        
        if active_tab == 'overview':
            return render_overview_tab(df)
        # elif active_tab == 'calendar':
        #     return render_calendar_tab(df)
        # elif active_tab == 'sleep':
        #     return render_sleep_tab(df)
        # elif active_tab == 'recovery':
        #     return render_recovery_tab(df)
        elif active_tab == 'trends':
            return render_trends_tab(df)
        # elif active_tab == 'stats':
        #     return render_stats_tab(df)

    # Callback for updating calendar visualizations
    @app.callback(
        [Output(ids.CYCLE_OVERLAY_PLOT, 'figure'), 
        Output(ids.CYCLE_OVERLAY_AVERAGE, 'figure')],
        [Input(ids.TREND_METRIC_DROPDOWN, 'value'),
        Input(ids.PROCESSED_DATA, 'children')]
    )
    def update_calendar_plots(selected_metric, processed_data):
        if processed_data is None or selected_metric is None:
            return go.Figure()
        
        df = load_data(processed_data=processed_data)
        
        # Create cycle overlay plot
        overlay_fig, overlay_ave = create_cycle_overlay_plot(df, selected_metric, 
                                                f"Cycle Overlay - {selected_metric}")
        
        return overlay_fig, overlay_ave

    # Run app
    app.run(debug=True)

if __name__ == "__main__":
    main()
