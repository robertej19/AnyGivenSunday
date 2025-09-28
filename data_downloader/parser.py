from bs4 import BeautifulSoup

def parse_standings(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    standings_data = []

    # Find all rows using the class from your HTML snippet
    rows = soup.find_all('div', class_='ContestStandings_row')

    if not rows:
        print("Could not find any standings rows with class 'ContestStandings_row'.")
        return standings_data
        
    print(f"Found {len(rows)} contestants.")

    for row in rows:
        contestant = {}
        
        # Extract Rank from the specific inner div
        rank_cell = row.find('div', class_='ContestStandings_rank-cell')
        if rank_cell:
            contestant['rank'] = rank_cell.get_text(strip=True)

        # Extract Username from its specific div
        username_cell = row.find('div', class_='UsernameWithEntryIndex_team-name')
        if username_cell:
            contestant['username'] = username_cell.get_text(strip=True)
            
        # Extract Points from the animated number span
        points_cell = row.find('span', class_='AnimatedNumber_animated-number')
        if points_cell:
            contestant['points'] = points_cell.get_text(strip=True)
        
        # Extract Winnings by finding the column with a 'column-winnings' class
        winnings_column = row.find('div', class_='column-winnings')
        if winnings_column:
            winnings_value = winnings_column.get_text(strip=True)
            if winnings_value:
                 contestant['winnings'] = winnings_value

        # Only add rows that have at least a username
        if 'username' in contestant:
            standings_data.append(contestant)

    return standings_data

if __name__ == "__main__":
    standings = parse_standings('example_1.html')
    for person in standings:
        print(person)
