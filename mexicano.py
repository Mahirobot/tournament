import itertools
import random

# Define the list of players
players = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']

# Divide players into groups of 4
groups = [players[i:i+4] for i in range(0, len(players), 4)]

# Round-robin within each group
for group in groups:
    print(f"Group: {group}")
    for pair in itertools.combinations(group, 2):
        print(f"{pair[0]} vs {pair[1]}")

# Determine the top 2 players from each group
top_players = []
for group in groups:
    scores = {player: 0 for player in group}
    for pair in itertools.combinations(group, 2):
        winner = random.choice(pair)
        scores[winner] += 1
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_players.extend([player for player, score in sorted_scores[:2]])

# Round-robin with the top 2 players from each group
groups = [top_players[i:i+3] for i in range(0, len(top_players), 3)]
for group in groups:
    print(f"Group: {group}")
    for pair in itertools.combinations(group, 2):
        print(f"{pair[0]} vs {pair[1]}")

# Determine the top 2 players from each group
top_pairs = []
for group in groups:
    scores = {pair: 0 for pair in itertools.combinations(group, 2)}
    for pair in itertools.combinations(group, 2):
        winner = random.choice(pair)
        scores[winner] += 1
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_pairs.extend([pair for pair, score in sorted_scores[:2]])

# Knockout stage with the top 2 pairs
for i, pair in enumerate(top_pairs):
    print(f"Match {i+1}: {pair[0]} and {pair[1]} vs {top_pairs[-(i+1)][0]} and {top_pairs[-(i+1)][1]}")
