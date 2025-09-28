from bs4 import BeautifulSoup
import pandas as pd
import re


NUM_RE = re.compile(r"[-+]?\d*\.?\d+")

def _to_int(text):
    if text is None: 
        return None
    m = NUM_RE.search(text.replace(",", ""))
    return int(float(m.group())) if m else None

def _to_float(text):
    if text is None:
        return None
    m = NUM_RE.search(text.replace(",", ""))
    return float(m.group()) if m else None

def parse_dk_standings(html: str) -> pd.DataFrame:
    """
    Parse the DraftKings-style ReactVirtualized standings block
    and return a DataFrame with columns: Rank, Team Name, PMR, FPTS.
    """
    soup = BeautifulSoup(html, "lxml")

    # Target the standings table container
    table = soup.select_one("div.ReactVirtualized__Table.ContestStandings_contest-standings-table")
    if table is None:
        return pd.DataFrame(columns=["Rank", "Team Name", "PMR", "FPTS"])

    # Each row is a button with row classes
    rows = table.select("button.ReactVirtualized__Table__row.ContestStandings_row")
    data = []

    for row in rows:
        # Rank
        rank_el = row.select_one(".ContestStandings_rank-cell")
        rank = _to_int(rank_el.get_text(strip=True) if rank_el else None)

        # Team Name
        team_el = row.select_one(".UsernameWithEntryIndex_team-name")
        team = team_el.get_text(strip=True) if team_el else None

        # PMR (time remaining column)
        # Typically under `.column-timeRemaining [role="cell"] span`
        pmr_el = row.select_one('.column-timeRemaining [role="cell"] span') \
                 or row.select_one('.column-timeRemaining span')
        pmr = _to_int(pmr_el.get_text(strip=True) if pmr_el else None)

        # FPTS
        # Usually in `.ContestStandings_fantasy-points-cell` animated number span
        fpts_el = row.select_one(".ContestStandings_fantasy-points-cell .AnimatedNumber_animated-number span") \
                  or row.select_one(".ContestStandings_column-fantasyPoints .AnimatedNumber_animated-number span") \
                  or row.select_one(".ContestStandings_fantasy-points-cell") \
                  or row.select_one(".ContestStandings_column-fantasyPoints")
        fpts_text = fpts_el.get_text(strip=True) if fpts_el else None
        # remove any trailing labels like "FPTS"
        fpts_text = fpts_text.replace("FPTS", "").strip() if fpts_text else None
        fpts = _to_float(fpts_text)

        if any(v is not None for v in (rank, team, pmr, fpts)):
            data.append({"Rank": rank, "Team Name": team, "PMR": pmr, "FPTS": fpts})

    df = pd.DataFrame(data, columns=["Rank", "Team Name", "PMR", "FPTS"])
    # Sort by rank if present
    if not df.empty and df["Rank"].notna().any():
        df = df.sort_values("Rank", kind="stable").reset_index(drop=True)
    return df

if __name__ == "__main__":
    # Read the HTML file first
    with open("data_downloader/example_1.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    df = parse_dk_standings(html_content)
    print(df)