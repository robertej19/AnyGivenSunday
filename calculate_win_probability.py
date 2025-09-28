import numpy as np
import pandas as pd

def dfs_win_probs(df, sigma2=0.5, sims=20000, random_state=None):
    """
    Estimate final points distribution and win probabilities for DFS lineups.
    
    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns ['Team Name', 'FPTS', 'PMR'].
    sigma2 : float
        Variance per minute (tune this using historical data).
    sims : int
        Number of simulation draws.
    random_state : int or None
        For reproducibility.
        
    Returns
    -------
    result : pd.DataFrame
        Original df with added columns:
        - 'ProjFinal': expected final points (mean)
        - 'StdDev': std dev of final points
        - 'WinProb': probability of finishing 1st
    """
    rng = np.random.default_rng(random_state)
    
    mu = df["FPTS"].values + df["PMR"].values / 4.0
    var = sigma2 * df["PMR"].values
    std = np.sqrt(var)
    
    n_teams = len(df)
    
    # Simulate final scores for each team
    draws = rng.normal(loc=mu[:, None], scale=std[:, None], size=(n_teams, sims))
    
    # Find winner for each simulation
    winners = np.argmax(draws, axis=0)
    win_counts = np.bincount(winners, minlength=n_teams)
    win_probs = win_counts / sims
    
    out = df.copy()
    out["ProjFinal"] = mu
    out["StdDev"] = std
    out["WinProb"] = win_probs
    return out

if __name__ == "__main__":
    data = {
    "Team Name": ["Team A", "Team B", "Team C"],
    "FPTS": [80, 75, 36],
    "PMR": [60, 90, 360]   # player minutes remaining
    }
    df = pd.DataFrame(data)

    result = dfs_win_probs(df, sigma2=0.5, sims=50000, random_state=42)
    print(result)
