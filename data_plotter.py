import pandas as pd
from calculate_win_probability import dfs_win_probs
from plotly.subplots import make_subplots
import plotly.graph_objects as go

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
        processed_dfs.append(dfs_win_probs(group))
    
    plot_df = pd.concat(processed_dfs)
    
    teams = plot_df['Team Name'].unique()
    colors = {team: f'hsl({i * 360 / len(teams)}, 70%, 50%)' for i, team in enumerate(teams)}

    # --- Projected Points Plot ---
    fig_points = go.Figure()
    
    for team in teams:
        team_df = plot_df[plot_df['Team Name'] == team].sort_values('timeindex')
        color = colors[team]
        
        # Uncertainty band
        fig_points.add_trace(go.Scatter(
            x=list(team_df['timeindex']) + list(team_df['timeindex'])[::-1],
            y=list(team_df['ProjFinal'] + team_df['StdDev']) + list(team_df['ProjFinal'] - team_df['StdDev'])[::-1],
            fill='toself',
            fillcolor=f'hsla({color[4:-1]}, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            showlegend=False
        ))

        # Projected Final Points line
        fig_points.add_trace(go.Scatter(
            x=team_df['timeindex'],
            y=team_df['ProjFinal'],
            mode='lines+markers',
            name=team,
            line=dict(color=color)
        ))

    fig_points.update_layout(
        title_text='Projected Fantasy Points Over Time',
        xaxis_title_text='Time Index',
        yaxis_title_text='Projected Final Points (FPTS)',
        legend_title_text='Team Name',
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#1a1a1a',
        font_color='white',
        font_size=16,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )

    # --- Win Probability Plot ---
    fig_win_prob = go.Figure()
    
    win_prob_pivot = plot_df.pivot(index='timeindex', columns='Team Name', values='WinProb').fillna(0)
    
    for team in teams:
        fig_win_prob.add_trace(go.Scatter(
            x=win_prob_pivot.index,
            y=win_prob_pivot[team],
            mode='lines',
            stackgroup='one',
            name=team,
            line=dict(color=colors[team])
        ))

    fig_win_prob.update_layout(
        title_text='Win Probability Over Time',
        xaxis_title_text='Time Index',
        yaxis_title_text='Win Probability',
        legend_title_text='Team Name',
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#1a1a1a',
        font_color='white',
        font_size=16,
        xaxis=dict(showgrid=False),
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
