from dash import Dash, Input, Output, State, html, no_update, callback_context
from dash_bootstrap_components.themes import MATERIA
import plotly.graph_objects as go
import pandas as pd

# Local Imports
from src.components.layout import (create_layout, render_overview_tab,
                                   render_sleep_tab, render_recovery_tab, 
                                   render_trends_tab, create_cycle_overlay_plot, 
                                   create_phase_legend, render_stats_tab)
from src.components import ids
from src.data.loader import parse_contents, load_data, process_data, filter_data

def main() -> None:
    # load the data and create the data manager
    # data = load_transaction_data(DATA_PATH)

    # Initialize the Dash app
    app = Dash(__name__, suppress_callback_exceptions=True, 
               external_stylesheets=[MATERIA])
    app.title = "Whoop Cycle Analysis Dashboard"

    # Define the app layout
    app.layout = create_layout(app)

    @app.callback(
        Output(ids.UPLOAD_SECTION_COLLAPSE, "is_open"),
        Output(ids.UPLOAD_ARROW, "children"),
        Input(ids.TOGGLE_UPLOAD_BUTTON, "n_clicks"),
        State(ids.UPLOAD_SECTION_COLLAPSE, "is_open"),
        prevent_initial_call=True
    )
    def toggle_upload_section(n_clicks, is_open):
        if n_clicks is None:
            return no_update, no_update
        new_state = not is_open
        arrow = "▼" if new_state else "▶"
        return new_state, arrow

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

    # Combined callback for year dropdown
    @app.callback(
        Output(ids.YEAR_DROPDOWN, 'options'),
        Output(ids.YEAR_DROPDOWN, 'value'),
        [Input(ids.PROCESSED_DATA, 'children'),
        Input(ids.SELECT_ALL_YEARS_BUTTON, 'n_clicks')],
        [State(ids.YEAR_DROPDOWN, 'options'),
        State(ids.YEAR_DROPDOWN, 'value')]
    )
    def manage_year_dropdown(processed_data, n_clicks, current_options, current_value):
        ctx = callback_context
        
        if not ctx.triggered:
            return [], None
        
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # If data was just processed, populate the dropdown
        if trigger_id == ids.PROCESSED_DATA:
            if processed_data is None:
                return [], None
            
            df = load_data(processed_data=processed_data)
            
            # Extract years
            df[ids.CYCLE_START_DATE] = pd.to_datetime(df[ids.CYCLE_START_DATE])
            years = sorted(df[ids.CYCLE_START_DATE].dt.year.unique())
            year_options = [{'label': str(year), 'value': year} for year in years]
            
            # Select all by default
            return year_options, years
        
        # If "Select All" button was clicked
        elif trigger_id == ids.SELECT_ALL_YEARS_BUTTON:
            if n_clicks is None or n_clicks == 0:
                return no_update, no_update
            
            # Toggle: if all selected, deselect all; otherwise select all
            if current_options and current_value and len(current_value) == len(current_options):
                return no_update, []
            
            if current_options:
                return no_update, [option['value'] for option in current_options]
        
        return no_update, no_update

    # Combined callback for month dropdown
    @app.callback(
        Output(ids.MONTH_DROPDOWN, 'options'),
        Output(ids.MONTH_DROPDOWN, 'value'),
        [Input(ids.PROCESSED_DATA, 'children'),
        Input(ids.SELECT_ALL_MONTHS_BUTTON, 'n_clicks')],
        [State(ids.MONTH_DROPDOWN, 'options'),
        State(ids.MONTH_DROPDOWN, 'value')]
    )
    def manage_month_dropdown(processed_data, n_clicks, current_options, current_value):
        ctx = callback_context
        
        if not ctx.triggered:
            return [], None
        
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # If data was just processed, populate the dropdown
        if trigger_id == ids.PROCESSED_DATA:
            if processed_data is None:
                return [], None
            
            # Month options (always the same)
            months = [
                {'label': 'January', 'value': 1},
                {'label': 'February', 'value': 2},
                {'label': 'March', 'value': 3},
                {'label': 'April', 'value': 4},
                {'label': 'May', 'value': 5},
                {'label': 'June', 'value': 6},
                {'label': 'July', 'value': 7},
                {'label': 'August', 'value': 8},
                {'label': 'September', 'value': 9},
                {'label': 'October', 'value': 10},
                {'label': 'November', 'value': 11},
                {'label': 'December', 'value': 12}
            ]
            
            # Select all by default
            return months, list(range(1, 13))
        
        # If "Select All" button was clicked
        elif trigger_id == ids.SELECT_ALL_MONTHS_BUTTON:
            if n_clicks is None or n_clicks == 0:
                return no_update, no_update
            
            # Toggle: if all selected, deselect all; otherwise select all
            if current_options and current_value and len(current_value) == len(current_options):
                return no_update, []
            
            if current_options:
                return no_update, [option['value'] for option in current_options]
        
        return no_update, no_update
    
    # Callback for tab content
    @app.callback(
        Output(ids.TAB_CONTENT, 'children'),
        [Input(ids.TABS, 'value'),
        Input(ids.PROCESSED_DATA, 'children'),
        Input(ids.YEAR_DROPDOWN, 'value'),
        Input(ids.MONTH_DROPDOWN, 'value')]
    )
    def render_tab_content(active_tab, processed_data, 
                           selected_years, selected_months):
        if processed_data is None:
            return html.Div("Please upload physiological and journal data to continue.")
        
        df = load_data(processed_data=processed_data)

        # Apply filters
        df = filter_data(df, selected_years, selected_months)
        
        if active_tab == 'overview':
            return render_overview_tab(df)
        elif active_tab == 'sleep':
            return render_sleep_tab(df)
        elif active_tab == 'recovery':
            return render_recovery_tab(df)
        elif active_tab == 'trends':
            return render_trends_tab(df)
        elif active_tab == 'stats':
            return render_stats_tab(df)

    # Callback for updating calendar visualizations
    @app.callback(
        [Output(ids.CYCLE_OVERLAY_PLOT, 'figure'), 
         Output(ids.CYCLE_OVERLAY_LEGEND, 'figure')], 
        [Input(ids.TREND_METRIC_DROPDOWN, 'value'),
        Input(ids.PROCESSED_DATA, 'children'),
        Input(ids.YEAR_DROPDOWN, 'value'),
        Input(ids.MONTH_DROPDOWN, 'value')]
    )
    def update_calendar_plots(selected_metric, processed_data, 
                              selected_years, selected_months):
        if processed_data is None or selected_metric is None:
            return go.Figure(), go.Figure()
        
        df = load_data(processed_data=processed_data)
        # Apply filters
        df = filter_data(df, selected_years, selected_months)
        
        # Create cycle overlay plot
        overlay_fig = create_cycle_overlay_plot(df, selected_metric, 
                                                f"Cycle Overlay - {selected_metric}")
        legend_fig = create_phase_legend()
        
        return [overlay_fig, legend_fig]

    # Run app
    app.run(debug=True)

if __name__ == "__main__":
    main()
