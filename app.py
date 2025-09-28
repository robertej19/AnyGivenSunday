import dash
from dash import dcc, html
import data_loader
import data_plotter

# Load data and create the plots
directory_path = 'mock_data_downloads'
standings_data = data_loader.load_standings_directory(directory_path)
fig_points, fig_win_prob = data_plotter.plot_standings(standings_data)

# Get latest time index data for summary
latest_time = standings_data['timeindex'].max()
latest_data = standings_data[standings_data['timeindex'] == latest_time].copy()

# Calculate win probabilities for latest data
from calculate_win_probability import dfs_win_probs
latest_data = dfs_win_probs(latest_data)

# Sort by projected final points (descending)
latest_data = latest_data.sort_values('ProjFinal', ascending=False)

# Initialize the Dash app
app = dash.Dash(__name__)

# Add custom CSS to remove white borders
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                margin: 0;
                padding: 0;
            }
            html, body {
                height: 100%;
                margin: 0;
                padding: 0;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Create summary table
summary_rows = []
for i, (_, row) in enumerate(latest_data.iterrows(), 1):
    summary_rows.append(
        html.Tr([
            html.Td(f"{i}", style={'padding': '8px', 'textAlign': 'center', 'border': '1px solid #444'}),
            html.Td(f"{row['Team Name']}", style={'padding': '8px', 'border': '1px solid #444'}),
            html.Td(f"{row['FPTS']:.1f}", style={'padding': '8px', 'textAlign': 'center', 'border': '1px solid #444'}),
            html.Td(f"{row['ProjFinal']:.1f}", style={'padding': '8px', 'textAlign': 'center', 'border': '1px solid #444'}),
            html.Td(f"{row['WinProb']:.1%}", style={'padding': '8px', 'textAlign': 'center', 'border': '1px solid #444'})
        ])
    )

# Define the app layout
app.layout = html.Div(children=[
    html.H1(children='Fantasy Football Standings', style={'color': 'white', 'textAlign': 'center'}),
    
    html.H2(children=f'Current Standings (Time Index: {int(latest_time)})', 
            style={'color': 'white', 'textAlign': 'center', 'marginTop': '30px'}),
    
    html.Table([
        html.Thead([
            html.Tr([
                html.Th('Rank', style={'padding': '8px', 'textAlign': 'center', 'border': '1px solid #444', 'backgroundColor': '#333'}),
                html.Th('Team', style={'padding': '8px', 'border': '1px solid #444', 'backgroundColor': '#333'}),
                html.Th('Current FPTS', style={'padding': '8px', 'textAlign': 'center', 'border': '1px solid #444', 'backgroundColor': '#333'}),
                html.Th('Projected Final', style={'padding': '8px', 'textAlign': 'center', 'border': '1px solid #444', 'backgroundColor': '#333'}),
                html.Th('Win Probability', style={'padding': '8px', 'textAlign': 'center', 'border': '1px solid #444', 'backgroundColor': '#333'})
            ])
        ]),
        html.Tbody(summary_rows)
    ], style={'margin': '20px auto', 'borderCollapse': 'collapse', 'width': '80%'}),

    dcc.Graph(
        id='points-graph',
        figure=fig_points
    ),
    
    dcc.Graph(
        id='win-prob-graph',
        figure=fig_win_prob
    )
], style={'backgroundColor': '#1a1a1a', 'color': 'white', 'minHeight': '100vh', 'padding': '20px'})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
