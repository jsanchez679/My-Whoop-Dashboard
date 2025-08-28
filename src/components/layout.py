from dash import Dash, html, dcc, dash_table
import dash_bootstrap_components as dbc 
from src.components import ids
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.data.loader import parse_date

def create_layout(app: Dash) -> html.Div:
    # Define the app layout
    # Upload buttons style
    upload_style = {'width': '100%', 'height': '60px', 'lineHeight': '60px',
                        'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                        'textAlign': 'center', 'margin': '10px'}
    
    return html.Div(
                className="app-div",
                children=[
                    # Header
                    html.H1(app.title, style={'textAlign': 'center'}),
                    html.P("Analyse your physiological data across different phases of your menstrual cycle",
                            style={'textAlign': 'center', 'fontSize': 20}), 
                    html.Hr(),

                    # Data upload section
                    html.Div([
                        html.H3("Upload Your Data Files", style={'textAlign': 'center'}),
                        html.Div([
                            html.Div([
                                html.H4("Physiological Cycles", style={'textAlign': 'center'}),
                                dcc.Upload(
                                    id=ids.UPLOAD_PHYSIOLOGICAL,
                                    children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
                                    style=upload_style,
                                    multiple=False
                                ),
                                html.Div(id=ids.UPLOAD_STATUS_PHYSIOLOGICAL, style={'textAlign': 'center', 'fontSize': 12})
                            ], className="upload-box"),
                            
                            html.Div([
                                html.H4("Journal Entries", style={'textAlign': 'center'}),
                                dcc.Upload(
                                    id=ids.UPLOAD_JOURNAL,
                                    children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
                                    style=upload_style,
                                    multiple=False
                                ),
                                html.Div(id=ids.UPLOAD_STATUS_JOURNAL, style={'textAlign': 'center', 'fontSize': 12})
                            ], className="upload-box"),
                            
                            html.Div([
                                html.H4("Sleep Data", style={'textAlign': 'center'}),
                                dcc.Upload(
                                    id=ids.UPLOAD_SLEEP,
                                    children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
                                    style=upload_style,
                                    multiple=False
                                ),
                                html.Div(id=ids.UPLOAD_STATUS_SLEEP, style={'textAlign': 'center', 'fontSize': 12})
                            ], className="upload-box"),
                            
                            html.Div([
                                html.H4("Workouts", style={'textAlign': 'center'}),
                                dcc.Upload(
                                    id=ids.UPLOAD_WORKOUTS,
                                    children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
                                    style=upload_style,
                                    multiple=False
                                ),
                                html.Div(id=ids.UPLOAD_STATUS_WORKOUTS, style={'textAlign': 'center', 'fontSize': 12})
                            ], className="upload-box"),
                        ], className="upload-grid"),
                    ], className="upload-section"),

                    html.Hr(),

                    # Main dashboard content
                    html.Div([
                        # Tabs
                        dcc.Tabs(id=ids.TABS, value="overview", 
                                 children=[
                                    dcc.Tab(label="Overview", value="overview"),
                                    dcc.Tab(label="Calendar View", value="calendar"),
                                    dcc.Tab(label="Sleep Analysis", value="sleep"),
                                    dcc.Tab(label="Recovery & Strain", value="recovery"),
                                    dcc.Tab(label="Trends", value="trends"),
                                    dcc.Tab(label="Statistical Analysis", value="stats")
                        ]),
                        # Tab content
                        html.Div(id=ids.TAB_CONTENT)
                    ], id=ids.MAIN_CONTENT, style={'display': 'none'}),

                    # Hidden divs to store data
                    html.Div(id=ids.STORED_DATA_PHYSIOLOGICAL, style={'display': 'none'}),
                    html.Div(id=ids.STORED_DATA_JOURNAL, style={'display': 'none'}),
                    html.Div(id=ids.STORED_DATA_SLEEP, style={'display': 'none'}),
                    html.Div(id=ids.STORED_DATA_WORKOUTS, style={'display': 'none'}),
                    html.Div(id=ids.PROCESSED_DATA, style={'display': 'none'}),

                    # bar_chart.render(app, data),
                    # pie_chart.render(app, data),
                ],
    )

def create_styled_table(ov_data: pd.DataFrame) -> html.Div:
    """Create a styled DBC table with phase-specific coloring"""
    
    # Create the basic table
    table = dbc.Table.from_dataframe(
        ov_data, 
        striped=True, 
        bordered=True, 
        hover=True,
        responsive=True,
        className="text-center uniform-columns"
    )
    return html.Div([table], className="custom-table-container")

def render_overview_tab(df: pd.DataFrame) -> dbc.Container:

    """Render the overview tab"""
    # Summary statistics
    total_days = len(df[ids.CYCLE_DATE].unique())
    no_cycles = df[ids.CYCLE_DAY_NUMBER].value_counts()[1]
    menstrual_days = len(df[df[ids.PHASE] == ids.MENSTRUAL])
    avg_cycle_len = df[df[ids.CYCLE_DAY_NUMBER]== 1][ids.CYCLE_LENGTH].mean()

    # Key metrics comparison
    metrics = [ids.RECOVERY_SCORE,ids.RESTING_HR, ids.HRV, 
               ids.SLEEP_PERFORMANCE, ids.SLEEP_EFFICIENCY, ids.DAY_STRAIN]
    
    # Option 1 DBC
    rows = []
    for metric in metrics:
        if metric in df.columns:
            follicular_avg = df[df[ids.PHASE] == ids.FOLLICULAR][metric].mean()
            ovulatory_avg = df[df[ids.PHASE] == ids.OVULATORY][metric].mean()
            luteal_avg = df[df[ids.PHASE] == ids.LUTEAL][metric].mean()
            menstrual_avg = df[df[ids.PHASE] == ids.MENSTRUAL][metric].mean()
            row = {
                    'Metric': metric,
                    ids.FOLLICULAR: round(follicular_avg, 2) if not pd.isna(follicular_avg) else 'N/A',
                    ids.OVULATORY: round(ovulatory_avg, 2) if not pd.isna(ovulatory_avg) else 'N/A',
                    ids.LUTEAL: round(luteal_avg, 2) if not pd.isna(luteal_avg) else 'N/A',
                    ids.MENSTRUAL: round(menstrual_avg, 2) if not pd.isna(menstrual_avg) else 'N/A',
                }
            rows.append(row)
    
        ov_data = pd.DataFrame(rows)
            
    return dbc.Container([
            # Summary cards
            # First row
            html.Div([
                html.Div([
                    html.H3(f"{total_days}"),
                    html.P("Total Days Analysed")
                ], className="summary-card"),
                html.Div([
                    html.H3(f"{no_cycles}"),
                    html.P("No Cycles in Analysis")
                ], className="summary-card"),
                html.Div([
                    html.H3(f"{menstrual_days}"),
                    html.P("Total Menstrual Days")
                ], className="summary-card"),
                html.Div([
                    html.H3(f"{avg_cycle_len:.1f}"),
                    html.P("Avg. Cycle Length [days]")
                ], className="summary-card")
            ], className="summary-grid"),

            # Comparison table
            html.H2(" Metrics Comparison"),
            create_styled_table(ov_data)

    ], fluid=True)
            
    # Option 2 Normal dash table
    ov_data = []
    for metric in metrics:
        if metric in df.columns:
            follicular_avg = df[df[ids.PHASE] == ids.FOLLICULAR][metric].mean()
            ovulatory_avg = df[df[ids.PHASE] == ids.OVULATORY][metric].mean()
            luteal_avg = df[df[ids.PHASE] == ids.LUTEAL][metric].mean()
            menstrual_avg = df[df[ids.PHASE] == ids.MENSTRUAL][metric].mean()
            ov_data.append({
                'Metric': metric,
                ids.FOLLICULAR: round(follicular_avg, 2) if not pd.isna(follicular_avg) else 'N/A',
                ids.OVULATORY: round(ovulatory_avg, 2) if not pd.isna(ovulatory_avg) else 'N/A',
                ids.LUTEAL: round(luteal_avg, 2) if not pd.isna(luteal_avg) else 'N/A',
                ids.MENSTRUAL: round(menstrual_avg, 2) if not pd.isna(menstrual_avg) else 'N/A',
            })

    return html.Div([
            # Summary cards
            # First row
            html.Div([
                html.Div([
                    html.H3(f"{total_days}"),
                    html.P("Total Days Analysed")
                ], className="summary-card"),
                html.Div([
                    html.H3(f"{no_cycles}"),
                    html.P("No Cycles in Analysis")
                ], className="summary-card"),
                html.Div([
                    html.H3(f"{menstrual_days}"),
                    html.P("Menstrual Days")
                ], className="summary-card"),
                html.Div([
                    html.H3(f"{avg_cycle_len:.1f}"),
                    html.P("Avg. Cycle Length [days]")
                ], className="summary-card")
            ], className="summary-grid"),

            # Comparison table
            html.H3(" Metrics Comparison"),
            dash_table.DataTable(
                data=ov_data,
                columns=[{"name": i, "id": i} for i in ['Metric', ids.FOLLICULAR, ids.OVULATORY, 
                                                                    ids.LUTEAL, ids.MENSTRUAL]],
                style_cell={'textAlign': 'center',},# 'font_family': 'cursive',},
                style_data_conditional=[
                    {
                        'if': {'column_id': ids.FOLLICULAR},
                        'backgroundColor': '#c7ee5394'
                    },
                    {
                        'if': {'column_id': ids.OVULATORY},
                        'backgroundColor': '#eee4538b'
                    },
                    {
                        'if': {'column_id': ids.LUTEAL},
                        'backgroundColor': '#74daf191'
                    },
                    {
                        'if': {'column_id': ids.MENSTRUAL},
                        'backgroundColor': '#ea5c5ca8'
                    },
                ],
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold', 'textAlign': 'center',
                },
            ),
            
            ])

def render_trends_tab(df: pd.DataFrame) -> dbc.Container:
    """Render the trends view tab with cycle overlays"""
    return html.Div([
                html.H4(),
                html.H3("Calendar View & Cycle Overlays"),
            
                # Metric selector
                html.Div([
                    html.Label("Select Metric for Visualization:"),
                    dcc.Dropdown(
                        id=ids.TREND_METRIC_DROPDOWN,
                        options=[
                            {'label': 'Recovery Score %', 'value': 'Recovery score %'},
                            {'label': 'Resting Heart Rate (bpm)', 'value': 'Resting heart rate (bpm)'},
                            {'label': 'Heart Rate Variability (ms)', 'value': 'Heart rate variability (ms)'},
                            {'label': 'Sleep Performance %', 'value': 'Sleep performance %'},
                            {'label': 'Day Strain', 'value': 'Day Strain'},
                            {'label': 'Sleep Efficiency %', 'value': 'Sleep efficiency %'}
                        ],
                        value='Recovery score %',
                        style={'margin-bottom': '20px'}
                    )
                ]),
                
                # Cycle overlay plot
                html.Div([
                    html.H4("Cycle Overlay Plot"),
                    html.P("Multiple cycles overlaid to show patterns. Each line represents a different cycle starting from menstruation."),
                    dcc.Graph(id=ids.CYCLE_OVERLAY_PLOT)
                ], style={'margin-top': '30px'}),
                # Cycle overlay average plot
                html.Div([
                    html.H4("Cycle Overlay Average Plot"),
                    html.P("Average of Multiple cycles to show patterns."),
                    dcc.Graph(id=ids.CYCLE_OVERLAY_AVERAGE)
                ], style={'margin-top': '30px'})
            ])


def create_cycle_overlay_plot(df: pd.DataFrame, metric: str, title: str) -> go.Figure:
    """Create an overlay plot showing multiple cycles aligned by cycle day"""
    #Hereee start by understanding how the data is processed and now used the 
    # already processed dataframe
    
    if ids.CYCLE_START_DATE not in df.columns or metric not in df.columns:
        return go.Figure()
    
    # Filter menstrual cycles only
    first_day_menstrual_cycle = df[(df[ids.CYCLE_DAY_NUMBER] == 1) & (df[ids.CYCLE_START] == True)].copy()
    first_day_menstrual_cycle[ids.CYCLE_START_DATE] = first_day_menstrual_cycle[ids.CYCLE_START_DATE].apply(parse_date)
    df[ids.CYCLE_START_DATE] = df[ids.CYCLE_START_DATE].apply(parse_date)

    if len(first_day_menstrual_cycle) == 0:
        return go.Figure()
    
    # Group by cycle 
    first_day_menstrual_cycle[ids.CYCLE_ID] = range(len(first_day_menstrual_cycle))
    get_rows = first_day_menstrual_cycle.index

    # Create a figure
    fig = go.Figure()
    fig2 = go.Figure()
    
    # For each cycle, try to find the following days
    colors = px.colors.qualitative.Set3
    
    # Add average line
    all_cycle_data = []

    for i, (no, cycle_start) in enumerate(first_day_menstrual_cycle.iterrows()):
        cycle_color = colors[i % len(colors)]
        start_date = cycle_start[ids.CYCLE_START_DATE]

        try: 
            # Find the end date for this cycle
            next_start_row = get_rows[i+1]
            # Find data points for this cycle
            cycle_data = df.iloc[no:next_start_row-1].copy()
        except: 
            # Find data points for this cycle
            cycle_data = df.iloc[no::].copy()

        if len(cycle_data) > 0 and len(cycle_data) < 35:
            # Add trace for this cycle
            fig.add_trace(go.Scatter(
                x=cycle_data[ids.CYCLE_DAY_NUMBER],
                y=cycle_data[metric],
                mode='lines+markers',
                name=f'Cycle {i+1} ({start_date.strftime("%Y-%m-%d")})',
                line=dict(color=cycle_color),
                marker=dict(color=cycle_color, size=6),
                opacity=0.7
            ))
            cycle_data[ids.CYCLE_ID] = i
            all_cycle_data.append(cycle_data[[ids.CYCLE_DAY_NUMBER, metric, ids.CYCLE_ID]])
    
    # Add average line
    if all_cycle_data:
        combined_data = pd.concat(all_cycle_data, ignore_index=True)
        avg_data = combined_data.groupby(ids.CYCLE_DAY_NUMBER)[metric].mean().reset_index()
        
        fig.add_trace(go.Scatter(
            x=avg_data[ids.CYCLE_DAY_NUMBER],
            y=avg_data[metric],
            mode='lines',
            name='Average',
            line=dict(color='black', width=3, dash='dash')
        ))
        fig2.add_trace(go.Scatter(
            x=avg_data[ids.CYCLE_DAY_NUMBER],
            y=avg_data[metric],
            mode='lines',
            name='Average',
            line=dict(color='black', width=3, dash='dash')
        ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Cycle Day",
        yaxis_title=metric,
        height=500,
        showlegend=True
    )
    fig2.update_layout(
        title=title,
        xaxis_title="Cycle Day",
        yaxis_title=metric,
        height=500,
        showlegend=True
    )
    
    return fig, fig2
