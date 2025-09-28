import dash
from dash import dcc, html, Input, Output, callback
import data_loader
import data_plotter
import asyncio
import threading
import time
from datetime import datetime
from scraper import DraftKingsScraper
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for data management
standings_data = None
scraper = None
scraper_thread = None
last_update_time = None
scraper_running = False
scraper_initialized = False

def load_data():
    """Load standings data from the data_downloads directory."""
    global standings_data, last_update_time
    directory_path = 'data_downloads'
    standings_data = data_loader.load_standings_directory(directory_path)
    
    # Remove duplicates to prevent plotting issues
    if not standings_data.empty:
        # Remove duplicates based on Team Name and timeindex
        initial_count = len(standings_data)
        standings_data = standings_data.drop_duplicates(subset=['Team Name', 'timeindex'], keep='first')
        final_count = len(standings_data)
        if initial_count != final_count:
            logger.info(f"Removed {initial_count - final_count} duplicate records")
    
    last_update_time = datetime.now()
    logger.info(f"Loaded {len(standings_data)} records from {directory_path}")
    return standings_data

def get_latest_data():
    """Get the latest standings data and calculate win probabilities."""
    if standings_data is None or standings_data.empty:
        return None
    
    latest_time = standings_data['timeindex'].max()
    latest_data = standings_data[standings_data['timeindex'] == latest_time].copy()
    
    if latest_data.empty:
        return None
    
    # Remove duplicates (keep first occurrence)
    latest_data = latest_data.drop_duplicates(subset=['Team Name'], keep='first')
    
    # Debug: Check data types before processing
    logger.info(f"Data types before win prob calculation:")
    logger.info(f"FPTS type: {latest_data['FPTS'].dtype}, sample: {latest_data['FPTS'].iloc[0] if len(latest_data) > 0 else 'N/A'}")
    logger.info(f"PMR type: {latest_data['PMR'].dtype}, sample: {latest_data['PMR'].iloc[0] if len(latest_data) > 0 else 'N/A'}")
    
    # Calculate win probabilities for latest data
    try:
        from calculate_win_probability import dfs_win_probs
        latest_data = dfs_win_probs(latest_data)
    except Exception as e:
        logger.error(f"Error calculating win probabilities: {e}")
        # Add default values if calculation fails
        latest_data['ProjFinal'] = latest_data['FPTS']
        latest_data['WinProb'] = 0.0
    
    # Sort by projected final points (descending)
    latest_data = latest_data.sort_values('ProjFinal', ascending=False)
    
    return latest_data, latest_time

def create_plots():
    """Create the plots from current standings data."""
    if standings_data is None or standings_data.empty:
        return None, None
    
    try:
        return data_plotter.plot_standings(standings_data)
    except Exception as e:
        logger.error(f"Error creating plots: {e}")
        return None, None

# Initialize data
load_data()

# Initialize the Dash app
app = dash.Dash(__name__)

# Scraper management functions
def start_scraper():
    """Start the background scraper in a separate thread."""
    global scraper, scraper_thread, scraper_running, scraper_initialized
    
    if scraper_initialized:
        logger.info("Scraper already initialized, skipping start")
        return
        
    if scraper_running or (scraper_thread is not None and scraper_thread.is_alive()):
        logger.info("Scraper already running, skipping start")
        return
    
    scraper_running = True
    scraper_initialized = True
    logger.info("Starting scraper thread...")
    
    def run_scraper_loop():
        """Run the scraper in a loop."""
        global scraper, scraper_running
        try:
            scraper = DraftKingsScraper()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Initialize scraper
            if loop.run_until_complete(scraper.initialize()):
                logger.info("Scraper initialized successfully")
                
                while scraper_running:
                    try:
                        # Scrape data
                        loop.run_until_complete(scraper.refresh_and_scrape())
                        
                        # Reload data in main thread
                        load_data()
                        logger.info("Data refreshed from scraper")
                        
                        # Wait 45 seconds
                        for _ in range(45):
                            if not scraper_running:
                                break
                            time.sleep(1)
                        
                        if not scraper_running:
                            break
                        
                        # Refresh page 15 seconds before next scrape
                        loop.run_until_complete(scraper.page.reload(wait_until="domcontentloaded"))
                        for _ in range(15):
                            if not scraper_running:
                                break
                            time.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error in scraper loop: {e}")
                        for _ in range(60):  # Wait a minute before retrying
                            if not scraper_running:
                                break
                            time.sleep(1)
            else:
                logger.error("Failed to initialize scraper")
                
        except Exception as e:
            logger.error(f"Fatal error in scraper thread: {e}")
        finally:
            if scraper:
                try:
                    loop.run_until_complete(scraper.close())
                except:
                    pass
            scraper_running = False
            logger.info("Scraper thread ended")
    
    scraper_thread = threading.Thread(target=run_scraper_loop, daemon=True)
    scraper_thread.start()
    logger.info("Scraper thread started")

def stop_scraper():
    """Stop the background scraper."""
    global scraper, scraper_running
    scraper_running = False
    if scraper:
        # The scraper will be closed when the thread exits
        logger.info("Scraper stop requested")

# Don't start scraper here - will start when app runs

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

# Define the app layout
app.layout = html.Div(children=[
    html.H1(children='Fantasy Football Standings', style={'color': 'white', 'textAlign': 'center'}),
    
    # Auto-refresh interval
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # Update every 30 seconds
        n_intervals=0
    ),
    
    # Status indicator
    html.Div(id='status-indicator', style={'color': 'white', 'textAlign': 'center', 'marginBottom': '20px'}),
    
    # Main content
    html.Div(id='main-content', children=[
        html.H2(children='Loading...', style={'color': 'white', 'textAlign': 'center', 'marginTop': '30px'}),
        html.Div(children='Please wait while data loads...', style={'color': 'white', 'textAlign': 'center'})
    ])
], style={'backgroundColor': '#1a1a1a', 'color': 'white', 'minHeight': '100vh', 'padding': '20px'})

# Callback to update the main content
@callback(
    [Output('main-content', 'children'),
     Output('status-indicator', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_content(n_intervals):
    """Update the main content with latest data."""
    try:
        # Reload data (scraper runs independently)
        load_data()
        
        # Get latest data
        latest_result = get_latest_data()
        if latest_result is None:
            return (
                html.Div([
                    html.H2(children='No Data Available', style={'color': 'white', 'textAlign': 'center', 'marginTop': '30px'}),
                    html.Div(children='Waiting for data from scraper...', style={'color': 'white', 'textAlign': 'center'})
                ]),
                f"Last update: {last_update_time.strftime('%H:%M:%S') if last_update_time else 'Never'} | Status: Waiting for data"
            )
        
        latest_data, latest_time = latest_result
        
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
        
        # Create plots
        fig_points, fig_win_prob = create_plots()
        
        if fig_points is None or fig_win_prob is None:
            return (
                html.Div([
                    html.H2(children='Error Creating Plots', style={'color': 'white', 'textAlign': 'center', 'marginTop': '30px'}),
                    html.Div(children='Unable to create plots from data', style={'color': 'white', 'textAlign': 'center'})
                ]),
                f"Last update: {last_update_time.strftime('%H:%M:%S') if last_update_time else 'Never'} | Status: Error"
            )
        
        # Create the main content
        content = html.Div([
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
        ])
        
        status = f"Last update: {last_update_time.strftime('%H:%M:%S') if last_update_time else 'Never'} | Status: Live | Records: {len(standings_data)}"
        
        return content, status
        
    except Exception as e:
        logger.error(f"Error updating content: {e}")
        return (
            html.Div([
                html.H2(children='Error Loading Data', style={'color': 'white', 'textAlign': 'center', 'marginTop': '30px'}),
                html.Div(children=f'Error: {str(e)}', style={'color': 'white', 'textAlign': 'center'})
            ]),
            f"Last update: {last_update_time.strftime('%H:%M:%S') if last_update_time else 'Never'} | Status: Error"
        )

# Run the app
if __name__ == '__main__':
    # Start the scraper only once
    start_scraper()
    
    try:
        # Use debug=False to prevent frequent reloads that cause scraper restarts
        app.run(debug=False, host='0.0.0.0', port=8050)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        stop_scraper()
    except Exception as e:
        logger.error(f"App error: {e}")
        stop_scraper()
