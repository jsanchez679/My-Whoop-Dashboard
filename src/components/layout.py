from dash import Dash, html, dcc, dash_table
import dash_bootstrap_components as dbc 
from src.components import ids
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from src.data import loader as ld 
from src.components import year_dropdown, month_dropdown

def create_layout(app: Dash) -> html.Div:
    # Define the app layout
    # Upload buttons style
    upload_style = {'width': '98%', 'height': '40px', 'lineHeight': '40px',
                        'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                        'textAlign': 'center', 'margin': '5px'}
    
    return html.Div(
                className="app-div",
                children=[
                    # Header
                    html.H1(app.title, style={'textAlign': 'center'}),
                    html.P("Analyse your physiological data across different phases of your menstrual cycle",
                            style={'textAlign': 'center', 'fontSize': 20}), 
                    html.Hr(),

                    # Toggle button for upload section
                    html.Div([
                        html.H4(
                            ["Upload Your Data Files ", html.Span("▼", id=ids.UPLOAD_ARROW)],
                            id=ids.TOGGLE_UPLOAD_BUTTON,
                            style={
                                'textAlign': 'center', 
                                'cursor': 'pointer',
                                'userSelect': 'none',
                                'padding': '5px'
                            }
                        ),
                    ], style={'textAlign': 'center'}),

                    # Data upload section
                    # Collapsible Data upload section
                    dbc.Collapse(
                        id=ids.UPLOAD_SECTION_COLLAPSE,
                        is_open=True,
                        children=[
                                html.Div([
                                    html.Div([
                                        html.Div([
                                            html.H5("Physiological Cycles", style={'textAlign': 'center'}),
                                            dcc.Upload(
                                                id=ids.UPLOAD_PHYSIOLOGICAL,
                                                children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
                                                style=upload_style,
                                                multiple=False
                                            ),
                                            html.Div(id=ids.UPLOAD_STATUS_PHYSIOLOGICAL, style={'textAlign': 'center', 'fontSize': 12})
                                        ], className="upload-box"),
                                        
                                        html.Div([
                                            html.H5("Journal Entries", style={'textAlign': 'center'}),
                                            dcc.Upload(
                                                id=ids.UPLOAD_JOURNAL,
                                                children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
                                                style=upload_style,
                                                multiple=False
                                            ),
                                            html.Div(id=ids.UPLOAD_STATUS_JOURNAL, style={'textAlign': 'center', 'fontSize': 12})
                                        ], className="upload-box"),
                                        
                                        html.Div([
                                            html.H5("Sleep Data", style={'textAlign': 'center'}),
                                            dcc.Upload(
                                                id=ids.UPLOAD_SLEEP,
                                                children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
                                                style=upload_style,
                                                multiple=False
                                            ),
                                            html.Div(id=ids.UPLOAD_STATUS_SLEEP, style={'textAlign': 'center', 'fontSize': 12})
                                        ], className="upload-box"),
                                        
                                        html.Div([
                                            html.H5("Workouts", style={'textAlign': 'center'}),
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
                        ]),
                    html.Hr(),

                    # Year and Month Dropdown
                    html.Div(
                        className="dropdown-container",
                        children=[
                            html.H5("Filter your data  ▶ ", style={'textAlign': 'center', 'width': '200px'}),
                            year_dropdown.render(app),
                            month_dropdown.render(app),
                            html.Hr(),
                        ],
                    style={'margin-bottom': '20px',"display": "flex",
                            "flexDirection": "row",
                            "alignItems": "center",   # vertically centers label/button with dropdown
                            "width": "96%",
                            "margin-right": "2%",
                            "margin-left": "2%"}
                    ),
                    # Main dashboard content
                    html.Div([
                        # Tabs
                        dcc.Tabs(id=ids.TABS, value="overview", 
                                 children=[
                                    dcc.Tab(label="Overview", value="overview"),
                                    # dcc.Tab(label="Calendar View", value="calendar"),
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
                ],
    )

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
            create_styled_table(ov_data, "custom-table-container")

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

def create_styled_table(data: pd.DataFrame, className: str) -> html.Div:
    """Create a styled DBC table with phase-specific coloring"""
    
    # Create the basic table
    table = dbc.Table.from_dataframe(
        data, 
        striped=True, 
        bordered=True, 
        hover=True,
        responsive=True,
        className="text-center uniform-columns"
    )
    return html.Div([table], className=className)

def render_sleep_tab(df: pd.DataFrame) -> dbc.Container:
    """Render the sleep analysis tab"""
    sleep_metrics = [ids.SLEEP_PERFORMANCE, ids.SLEEP_EFFICIENCY, ids.REM_DURATION, 
                    ids.DEEP_SLEEP_DURATION, ids.LIGHT_SLEEP_DURATION]
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(ids.SLEEP_PERFORMANCE, ids.SLEEP_EFFICIENCY, 
                        ids.REM_DURATION, ids.DEEP_SLEEP_DURATION),
        specs=[[{'secondary_y': False}, {'secondary_y': False}],
               [{'secondary_y': False}, {'secondary_y': False}]]
    )
    
    phase_colors = ['#EA5C5C', '#C7EE53', '#EEE453', '#74DAF1']
    phase_names = ['Menstrual', 'Follicular', 'Ovulatory', 'Luteal']
    
    for i, metric in enumerate(sleep_metrics[:4]):
        if metric in df.columns:
            row = (i // 2) + 1
            col = (i % 2) + 1
            
            for j, phase in enumerate(phase_names):
                data = df[df[ids.PHASE] == phase][metric].dropna()
                
                fig.add_trace(
                    go.Box(y=data, name=f'{phase}', 
                          marker_color=phase_colors[j], showlegend=(i==0)),
                    row=row, col=col
                )
    
    fig.update_layout(height=600, title_text="Sleep Metrics by Cycle Phase")
    
    return html.Div([
        dcc.Graph(figure=fig)
    ])

def render_recovery_tab(df: pd.DataFrame) -> dbc.Container:
    """Render the recovery & strain analysis tab
        TURN THIS INTO A SIMILAR STRAIN AND RECOVERY GRAPH FROM WHOOP
    """
    # Recovery and strain over time
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Recovery Score Over Time', 'Day Strain Over Time'),
        shared_xaxes=True
    )
    
    # Recovery score
    colors = df[ids.PHASE].map({'Menstrual':'#EA5C5C', 'Follicular':'#C7EE53', 
                                'Ovulatory':'#EEE453', 'Luteal': '#74DAF1'})
    fig.add_trace(
        go.Scatter(x=df[ids.CYCLE_START_DATE], y=df[ids.RECOVERY_SCORE],
                  mode='markers+lines', name=ids.RECOVERY_SCORE,
                  marker=dict(color=colors, size=8),
                  line=dict(color='gray', width=1)),
        row=1, col=1
    )
    
    # Day strain
    if 'Day Strain' in df.columns:
        fig.add_trace(
            go.Scatter(x=df[ids.CYCLE_START_DATE], y=df[ids.DAY_STRAIN],
                      mode='markers+lines', name=ids.DAY_STRAIN,
                      marker=dict(color=colors, size=8),
                      line=dict(color='gray', width=1)),
            row=2, col=1
        )
    
    fig.update_layout(height=600, title_text="Recovery and Strain Analysis")
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text=ids.RECOVERY_SCORE, row=1, col=1)
    fig.update_yaxes(title_text=ids.DAY_STRAIN, row=2, col=1)
    
    return html.Div([
        dcc.Graph(figure=fig)
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
                            {'label': ids.RECOVERY_SCORE, 'value': ids.RECOVERY_SCORE},
                            {'label': ids.RESTING_HR, 'value': ids.RESTING_HR},
                            {'label': ids.HRV, 'value': ids.HRV},
                            {'label': ids.SLEEP_PERFORMANCE, 'value': ids.SLEEP_PERFORMANCE},
                            {'label': ids.DAY_STRAIN, 'value': ids.DAY_STRAIN},
                            {'label': ids.SLEEP_EFFICIENCY, 'value': ids.SLEEP_EFFICIENCY}
                        ],
                        value=ids.RECOVERY_SCORE,
                        style={'margin-bottom': '20px'}
                    )
                ]),
                
                # Cycle overlay plot
                html.Div([
                    html.H4("Cycle Overlay Plot"),
                    html.P("Multiple cycles overlaid to show patterns. Each line represents a different cycle starting from the first day of menstruation."),
                    dcc.Graph(id=ids.CYCLE_OVERLAY_PLOT, 
                              style={'margin-bottom': '0px',
                                     'padding-bottom': '0px'})
                ], style={'margin-top': '20px', 
                          'margin-bottom': '20px',
                          'padding-bottom': '0px'}),
                html.Div([
                     dcc.Graph(id=ids.CYCLE_OVERLAY_LEGEND, 
                               config={'displayModeBar': False},
                               style={'margin-top': '0px',
                                      'margin-bottom': '20px'})
                ], style={'margin-top': '0px', 
                          'margin-bottom': '0px',
                          'padding-top': '0px'}),
            ])

def create_cycle_overlay_plot(df: pd.DataFrame, metric: str, title: str) -> go.Figure:
    """Create an overlay plot showing multiple cycles aligned by cycle day"""
    
    if ids.CYCLE_START_DATE not in df.columns or metric not in df.columns:
        return go.Figure()
    
    # Filter menstrual cycles only
    first_day_menstrual_cycle = df[(df[ids.CYCLE_DAY_NUMBER] == 1) & (df[ids.CYCLE_START] == True)].copy()
    first_day_menstrual_cycle[ids.CYCLE_START_DATE] = first_day_menstrual_cycle[ids.CYCLE_START_DATE].apply(ld.parse_date)
    df[ids.CYCLE_START_DATE] = df[ids.CYCLE_START_DATE].apply(ld.parse_date)

    if len(first_day_menstrual_cycle) == 0:
        return go.Figure()
    
    # Group by cycle 
    first_day_menstrual_cycle[ids.CYCLE_ID] = range(len(first_day_menstrual_cycle))
    get_rows = first_day_menstrual_cycle.index

    # Create a figure
    fig = make_subplots(rows=3, cols=1, 
                        # subplot_titles=['Cycle Overlay Plot','Cycle Average Plot', 'Phase'],
                        shared_xaxes = True, shared_yaxes=False, 
                        x_title = 'Cycle Day', y_title=metric,
                        row_heights=[0.475, 0.475, 0.05],
                        ) 
    
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
            cycle_data = df.iloc[no:next_start_row].copy()
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
            ), row=1, col=1)
            cycle_data[ids.CYCLE_ID] = i
            all_cycle_data.append(cycle_data[[ids.CYCLE_DAY_NUMBER, metric, ids.CYCLE_ID, ids.PHASE]])
    
    # Add average line
    if all_cycle_data:
        combined_data = pd.concat(all_cycle_data, ignore_index=True)
        avg_data = combined_data.groupby(ids.CYCLE_DAY_NUMBER)[metric].mean().reset_index()
        cc = combined_data[[ids.CYCLE_ID, ids.PHASE]].value_counts().to_frame()
        cc = cc.sort_values(by=[ids.CYCLE_ID, ids.PHASE])
        avg_phase_length = cc.groupby(ids.PHASE)['count'].mean().reset_index()
        avg_phase_length['count_round'] = avg_phase_length['count'].round(0)
        avg_phase_length = avg_phase_length.set_index(ids.PHASE)
        try: 
            avg_phase_length = avg_phase_length.drop(index=['Unknown'])
        except: 
            pass
        cycle_length_sum = avg_phase_length['count_round'].sum()
        avg_data = avg_data[:int(cycle_length_sum)]

        #Create a heatmap with the corresponding colors 
        follicular_start = avg_phase_length.loc['Menstrual','count_round'] + 1
        ovulatory_start = cycle_length_sum - avg_phase_length.loc['Luteal','count_round'] - avg_phase_length.loc['Ovulatory','count_round'] + 1
        ovulatory_end = cycle_length_sum - avg_phase_length.loc['Luteal','count_round']
        # luteal_start = ovulatory_end + 1
        dict_phases = {}
        for day in range(1,int(cycle_length_sum)+1):
            if day <= avg_phase_length.loc['Menstrual','count_round']:
                dict_phases[str(day)] = 1
            elif day >= follicular_start and day < ovulatory_start:
                dict_phases[str(day)] = 2
            elif day >= ovulatory_start and day <= ovulatory_end:
                dict_phases[str(day)] = 3
            else: #elif cycle_day >= luteal_start:
                dict_phases[str(day)] = 4
        df_phase = pd.DataFrame.from_dict(dict_phases, orient='index', columns=['phase'])
        phase_names = {1: 'Menstrual', 2: 'Follicular', 3: 'Ovulatory', 4: 'Luteal'}
        df_phase['phase_name'] = df_phase['phase'].map(phase_names)

        # fig.add_trace(go.Scatter(
        #     x=avg_data[ids.CYCLE_DAY_NUMBER],
        #     y=avg_data[metric],
        #     mode='lines',
        #     name='Average',
        #     line=dict(color='black', width=3, dash='dash')),
        #     row=1, col=1)
        fig.add_trace(go.Scatter(
            x=avg_data[ids.CYCLE_DAY_NUMBER],
            y=avg_data[metric],
            mode='lines',
            name='Average',
            line=dict(color='black', width=3, dash='dash')),
            row=2, col=1)
        
        # Create hover text array
        hover_text = []   
        for day in df_phase.index:
            phase_name = df_phase.loc[day, 'phase_name']
            hover_text.append(f'Day: {day}<br>Phase: {phase_name}')

        fig.add_trace(go.Heatmap(
            z=df_phase['phase'].values.reshape(1, -1),  # Reshape to single row
            x=df_phase.index.astype(int),  # Cycle days as x-axis
            colorscale=[[0, "#EA5C5C"], [0.33, "#C7EE53"], [0.66, "#EEE453"], [1, "#74DAF1"]],  # Custom colors
            showscale=False,
            colorbar=dict(
                tickvals=[1, 2, 3, 4],
                ticktext=['Menstrual', 'Follicular', 'Ovulatory', 'Luteal']
            ),
            text=np.array(hover_text).reshape(1, -1),
            hovertemplate='%{text}<extra></extra>'),
            row=3, col=1)
            
    # Update layout
    fig.update_layout(
        height=600,
        # width=800,
        showlegend=True,
        margin=dict(l=100, r=150, t=50, b=60),
    )

    # Remove all background elements from the heatmap
    fig.update_xaxes(showgrid=False, zeroline=False, row=3, col=1)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False, row=3, col=1)
    
    return fig

def create_phase_legend() -> go.Figure:
    phase_colors = ['#EA5C5C', '#C7EE53', '#EEE453', '#74DAF1']
    phase_names = ['Menstrual', 'Follicular', 'Ovulatory', 'Luteal']
    
    legend_fig = go.Figure()
    
    # Add invisible traces just for the legend
    for phase_name, color in zip(phase_names, phase_colors):
        legend_fig.add_trace(go.Scatter(
            x=[0], y=[0],
            mode='markers',
            marker=dict(color=color, size=20, symbol='square'),
            name=phase_name,
            showlegend=True,
            hoverinfo='none'
        ))
    
    # Configure the legend-only figure
    legend_fig.update_layout(
        height=60,  # Very short height
        width=800,  # Match your main figure width
        showlegend=True,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
        xaxis=dict(visible=False),  # Hide axes
        yaxis=dict(visible=False),  # Hide axes
        hovermode=False, 
        legend=dict(
            orientation="h",
            yanchor="middle",
            y=0.5,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="Black",
            borderwidth=1,
            font=dict(size=14)
        )
    )
    
    return legend_fig

def render_stats_tab(df: pd.DataFrame) -> html.Div:
    """Render the statistical analysis tab"""
    # Statistical tests and detailed analysis
    descriptive_table_data, overall_test_data, pairwise_table_data = ld.get_stats(df)

    return dbc.Container([
        html.H3("Statistical Analysis - Menstrual Cycle Phases"),
        # Descriptive Statistics Table
        html.Div([
            html.H4("1. Descriptive Statistics by Phase"),
            html.P("Summary statistics for each metric across all menstrual cycle phases:"),
            create_styled_table(descriptive_table_data, "stats_table")
        ]),
        
        # Overall Test Results Table
        html.Div([
            html.H4("2. Overall Statistical Tests"),
            html.P("Tests to determine if there are any significant differences between phases for each metric:"),
            create_styled_table(overall_test_data, "test_table")
        ]),

        # Pairwise Comparisons Table
        html.Div([
            html.H4("3. Pairwise Comparisons (Bonferroni Corrected)"),
            html.P("Detailed comparisons between each pair of menstrual cycle phases:"),
            create_styled_table(pairwise_table_data, "pairwise_table")
        ]),

        # Interpretation Guide
        html.Div([
            html.H4("Interpretation Guide:"),
            html.Ul([
                html.Li("P-value < 0.05 indicates statistical significance"),
                html.Li("Overall tests: ANOVA used if data is normal with equal variances, otherwise Kruskal-Wallis"),
                html.Li("Pairwise tests: t-tests used for normal data, Mann-Whitney U for non-normal data"),
                html.Li("Bonferroni correction: Adjusts p-values for multiple comparisons to reduce false positives"),
                html.Li("Mean/Median difference: Positive values indicate first phase > second phase"),
                html.Li("Effect sizes: Cohen's d or median differences help interpret practical significance"),
                html.Li("Green highlighting indicates statistically significant results (p < 0.05)")
            ])
        ], style={'margin-top': '20px', 'backgroundColor': '#f8f9fa', 'padding': '15px', 'border-radius': '5px'})
        
        ], fluid=True)
    

    return html.Div([
        html.H3("Statistical Analysis - Menstrual Cycle Phases"),
        
        # Descriptive Statistics Table
        html.Div([
            html.H4("1. Descriptive Statistics by Phase"),
            html.P("Summary statistics for each metric across all menstrual cycle phases:"),
            dash_table.DataTable(
                data=descriptive_table_data,
                columns=[{"name": col, "id": col} for col in descriptive_table_data[0].keys()] if descriptive_table_data else [],
                style_cell={'textAlign': 'left', 'fontSize': '12px'},
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold',
                    'fontSize': '13px'
                },
                style_cell_conditional=[
                    {'if': {'column_id': 'Metric'}, 'width': '20%'},
                    {'if': {'column_id': 'Phase'}, 'width': '12%'},
                ]
            )
        ], style={'margin-bottom': '30px'}),
        
        # Overall Test Results Table
        html.Div([
            html.H4("2. Overall Statistical Tests"),
            html.P("Tests to determine if there are any significant differences between phases for each metric:"),
            dash_table.DataTable(
                data=overall_test_data,
                columns=[{"name": col, "id": col} for col in overall_test_data[0].keys()] if overall_test_data else [],
                style_cell={'textAlign': 'left', 'fontSize': '12px'},
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    },
                    {
                        'if': {
                            'filter_query': '{Significant} = Yes',
                            'column_id': 'Significant'
                        },
                        'backgroundColor': '#90EE90',
                        'color': 'black',
                    }
                ],
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold',
                    'fontSize': '13px'
                },
                style_cell_conditional=[
                    {'if': {'column_id': 'Metric'}, 'width': '18%'},
                    {'if': {'column_id': 'Test Used'}, 'width': '15%'},
                    {'if': {'column_id': 'Interpretation'}, 'width': '25%'},
                ]
            )
        ], style={'margin-bottom': '30px'}),
        
        # Pairwise Comparisons Table
        html.Div([
            html.H4("3. Pairwise Comparisons (Bonferroni Corrected)"),
            html.P("Detailed comparisons between each pair of menstrual cycle phases:"),
            dash_table.DataTable(
                data=pairwise_table_data,
                columns=[{"name": col, "id": col} for col in pairwise_table_data[0].keys()] if pairwise_table_data else [],
                style_cell={'textAlign': 'left', 'fontSize': '12px'},
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    },
                    {
                        'if': {
                            'filter_query': '{Significant} = Yes',
                            'column_id': 'Significant'
                        },
                        'backgroundColor': '#90EE90',
                        'color': 'black',
                    }
                ],
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold',
                    'fontSize': '13px'
                },
                style_cell_conditional=[
                    {'if': {'column_id': 'Metric'}, 'width': '18%'},
                    {'if': {'column_id': 'Comparison'}, 'width': '20%'},
                    {'if': {'column_id': 'Test Used'}, 'width': '15%'},
                ]
            )
        ], style={'margin-bottom': '30px'}),
        
        # Interpretation Guide
        html.Div([
            html.H4("Interpretation Guide:"),
            html.Ul([
                html.Li("P-value < 0.05 indicates statistical significance"),
                html.Li("Overall tests: ANOVA used if data is normal with equal variances, otherwise Kruskal-Wallis"),
                html.Li("Pairwise tests: t-tests used for normal data, Mann-Whitney U for non-normal data"),
                html.Li("Bonferroni correction: Adjusts p-values for multiple comparisons to reduce false positives"),
                html.Li("Mean/Median difference: Positive values indicate first phase > second phase"),
                html.Li("Effect sizes: Cohen's d or median differences help interpret practical significance"),
                html.Li("Green highlighting indicates statistically significant results (p < 0.05)")
            ])
        ], style={'margin-top': '20px', 'backgroundColor': '#f8f9fa', 'padding': '15px', 'border-radius': '5px'})
    ])
    
