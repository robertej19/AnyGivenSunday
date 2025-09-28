import pandas as pd
from calculate_win_probability import dfs_win_probs
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import datetime, timedelta

def plot_standings(df):
    """
    Creates two separate Plotly figures: one for projected points and one for win probability.
    """
    # Ensure 'FPTS', 'PMR' and 'timeindex' are numeric
    df['FPTS'] = pd.to_numeric(df['FPTS'])
    df['PMR'] = pd.to_numeric(df['PMR'])
    df['timeindex'] = pd.to_numeric(df['timeindex'])

    # Calculate win probabilities for each time index
    processed_dfs = []
    for time, group in df.groupby('timeindex'):
        # Remove duplicates within each time group
        group = group.drop_duplicates(subset=['Team Name'], keep='first')
        processed_dfs.append(dfs_win_probs(group))
    
    plot_df = pd.concat(processed_dfs)
    
    # Final deduplication to ensure no duplicates for pivot operation
    plot_df = plot_df.drop_duplicates(subset=['Team Name', 'timeindex'], keep='first')
    
    # Convert timeindex to readable time format
    # timeindex is minutes since epoch, convert to datetime and adjust for EST (UTC-4)
    plot_df['time_dt'] = pd.to_datetime(plot_df['timeindex'] * 60, unit='s') - pd.Timedelta(hours=4)
    plot_df['time_str'] = plot_df['time_dt'].dt.strftime('%H:%M')
    
    # Create a time axis that preserves proportional spacing
    # Use the actual datetime values for plotting but format as HH:MM for display
    
    teams = plot_df['Team Name'].unique()
    colors = {team: f'hsl({i * 360 / len(teams)}, 70%, 50%)' for i, team in enumerate(teams)}

    # --- Projected Points Plot ---
    fig_points = go.Figure()
    
    for team in teams:
        team_df = plot_df[plot_df['Team Name'] == team].sort_values('timeindex')
        color = colors[team]
        
        # Uncertainty band
        fig_points.add_trace(go.Scatter(
            x=list(team_df['time_dt']) + list(team_df['time_dt'])[::-1],
            y=list(team_df['ProjFinal'] + team_df['StdDev']) + list(team_df['ProjFinal'] - team_df['StdDev'])[::-1],
            fill='toself',
            fillcolor=f'hsla({color[4:-1]}, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            showlegend=False
        ))

        # Projected Final Points line
        fig_points.add_trace(go.Scatter(
            x=team_df['time_dt'],
            y=team_df['ProjFinal'],
            mode='lines+markers',
            name=team,
            line=dict(color=color),
            hovertemplate=f'<b>{team}</b><br>' +
                         'Time: %{x|%H:%M}<br>' +
                         'Projected Final: %{y:.1f}<br>' +
                         '<extra></extra>'
        ))

    fig_points.update_layout(
        title_text='Projected Fantasy Points Over Time',
        xaxis_title_text='Time (HH:MM)',
        yaxis_title_text='Projected Final Points (FPTS)',
        legend_title_text='Team Name',
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#1a1a1a',
        font_color='white',
        font_size=16,
        xaxis=dict(
            showgrid=False,
            type='date',
            tickformat='%H:%M',
            tickmode='auto',
            nticks=10
        ),
        yaxis=dict(showgrid=False)
    )

    # --- Win Probability Plot ---
    fig_win_prob = go.Figure()
    
    # Create a mapping from timeindex to time_dt for the pivot
    time_mapping = plot_df[['timeindex', 'time_dt']].drop_duplicates().set_index('timeindex')['time_dt']
    win_prob_pivot = plot_df.pivot(index='timeindex', columns='Team Name', values='WinProb').fillna(0)
    
    # Convert the index to datetime values
    win_prob_pivot.index = win_prob_pivot.index.map(time_mapping)
    
    for team in teams:
        fig_win_prob.add_trace(go.Scatter(
            x=win_prob_pivot.index,
            y=win_prob_pivot[team],
            mode='lines',
            stackgroup='one',
            name=team,
            line=dict(color=colors[team]),
            hovertemplate=f'<b>{team}</b><br>' +
                         'Time: %{x|%H:%M}<br>' +
                         'Win Probability: %{y:.1%}<br>' +
                         '<extra></extra>'
        ))

    fig_win_prob.update_layout(
        title_text='Win Probability Over Time',
        xaxis_title_text='Time (HH:MM)',
        yaxis_title_text='Win Probability',
        legend_title_text='Team Name',
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#1a1a1a',
        font_color='white',
        font_size=16,
        xaxis=dict(
            showgrid=False,
            type='date',
            tickformat='%H:%M',
            tickmode='auto',
            nticks=10
        ),
        yaxis=dict(showgrid=False)
    )
    
    return fig_points, fig_win_prob

if __name__ == '__main__':
    import data_loader
    directory_path = 'mock_data_downloads'
    standings_data = data_loader.load_standings_directory(directory_path)
    
    if not standings_data.empty:
        fig = plot_standings(standings_data.copy())
        fig.write_html('standings_plot_with_win_prob.html')
        print("Plot saved to standings_plot_with_win_prob.html")
    else:
        print("No data to plot.")
