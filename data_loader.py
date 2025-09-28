import re
import pandas as pd
import os

def parse_line(line):
    """
    Parses a single line of the CSV file, handling bracketed arrays.
    """
    return re.findall(r'\[[^\]]*\]|[^,]+', line)

def parse_player_data(player_str):
    """
    Parses a player data string like '[Name,$Cost,Points]' into a tuple.
    """
    if not isinstance(player_str, str) or not player_str.startswith('[') or not player_str.endswith(']'):
        return None, None, None
    
    # Remove brackets and split by comma
    parts = player_str[1:-1].split(',')
    
    if len(parts) < 2:
        return (parts[0] if parts else None), None, None

    name = parts[0]
    points = parts[-1]
    cost = ",".join(parts[1:-1])
    
    return name, cost, points

def load_standings_file(file_path):
    """
    Loads standings data from a single CSV file with custom array fields,
    and parses the player data into separate columns.
    """
    with open(file_path, mode='r', encoding='utf-8') as infile:
        header_line = infile.readline().strip()
        if not header_line:
            return pd.DataFrame() # Return empty DataFrame for empty files
        header = parse_line(header_line)
        data = [parse_line(line.strip()) for line in infile if line.strip()]
    
    df = pd.DataFrame(data, columns=header)
    
    player_columns = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'WR3', 'TE', 'FLEX', 'DST']
    
    for col in player_columns:
        if col in df.columns:
            # Create new column names
            name_col = f'{col}_Name'
            cost_col = f'{col}_Cost'
            points_col = f'{col}_Points'

            # Apply the parsing function and expand into new columns
            parsed_data = df[col].apply(parse_player_data).apply(pd.Series)
            parsed_data.columns = [name_col, cost_col, points_col]
            
            # Add these new columns to the original DataFrame
            df = pd.concat([df, parsed_data], axis=1)
            
            # Drop the original column
            df.drop(col, axis=1, inplace=True)
            
    return df

def load_standings_directory(directory_path):
    """
    Loads standings data from all CSV files in a directory.
    """
    all_data = []
    for filename in os.listdir(directory_path):
        if filename.endswith('.csv') and filename.startswith('example_standings_'):
            file_path = os.path.join(directory_path, filename)
            
            # Extract timeindex from filename
            try:
                timeindex = int(filename.split('_')[-1].split('.')[0])
            except (IndexError, ValueError):
                continue
                
            df = load_standings_file(file_path)
            if not df.empty:
                df['timeindex'] = timeindex
                all_data.append(df)
    
    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)

if __name__ == '__main__':
    directory_path = 'mock_data_downloads'
    standings_data = load_standings_directory(directory_path)
    with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
        print(standings_data)
