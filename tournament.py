import itertools
import random

def americano_matchmaking(players):
    num_players = len(players)
    if num_players % 2 != 0:
        players.append(None)
        num_players += 1
    group_a = players[:num_players // 2]
    group_b = players[num_players // 2:]
    num_rounds = num_players - 1
    matches = []
    for round_num in range(num_rounds):
        round_matches = []
        for i in range(num_players // 4):
            player_a = group_a[i]
            player_a1 = group_a[i+1]
            player_b = group_b[i]
            player_b1 = group_b[i+1]
            if player_a is not None and player_b is not None and player_a1 is not None and player_b1 is not None:
                round_matches.append([(player_a, player_a1), (player_b, player_b1)])
        matches.append(round_matches)
        last_player_a = group_a.pop()
        last_player_a1 = group_a.pop()
        last_player_b = group_b.pop(0)
        last_player_b1 = group_b.pop(0)
        group_a.insert(1, last_player_b)
        group_a.insert(1, last_player_a1)
        group_b.append(last_player_a)
        group_b.append(last_player_b1)
    return matches


def team_americano_matchmaking(players):
    num_players = len(players)
    if num_players % 2 != 0:
        players.append(None)
        num_players += 1
    group_a = players[:num_players // 2]
    group_b = players[num_players // 2:]
    num_rounds = num_players - 1
    matches = []
    for round_num in range(num_rounds):
        round_matches = []
        for i in range(num_players // 2):
            player_a = group_a[i]
            player_b = group_b[i]
            if player_a is not None and player_b is not None:
                round_matches.append([player_a, player_b])
        matches.append(round_matches)
        last_player_a = group_a.pop()
        last_player_b = group_b.pop(0)
        group_a.insert(1, last_player_b)
        group_b.append(last_player_a)
    return matches

def mexicano_matchmaking(players, team = False):
    groups = [players[i:i+4] for i in range(0, len(players), 4)]
    matches = []
    for group in groups:
            if team:
                matches.append([[(group[0][0]), 0], [(group[1][0]), 0]])
                matches.append([[(group[2][0]), 0], [(group[3][0]), 0]])
            else:
                matches.append([[(group[0][0], group[3][0]), 0], [(group[1][0], group[2][0]), 0]])
    return matches
    
def assign_scores(players, match, team = False):
    for item in players:
        for pair, score in match:
            if team and pair == item[0]:
                item[1] += score
            else:
                for player in pair:
                    if player == item[0]:
                        item[1] += score
    return players



### TESTING ###

all_players = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

print('\n ----- AMERICANO -----\n')
no_of_players = 8
single_players = list(all_players[:no_of_players])
matches = americano_matchmaking(single_players)
round_count = 1
for round in matches:
    print(f'ROUND: {round_count}')
    round_count += 1
    for match in round:
        print(match[0], 'vs', match[1])


print('\n ----- TEAM AMERICANO ----- \n')
no_of_teams = 8
team_players = list(all_players[:no_of_teams])
team_pairs = [(team_players[i] + '-1' , team_players[i] + '-2') for i in range(8)]
matches = team_americano_matchmaking(team_pairs)
round_count = 1
for round in matches:
    print(f'ROUND: {round_count}')
    round_count += 1
    for match in round:
        print(match[0], 'vs', match[1])


print('\n ----- Mexicano ----- \n')
point = 16
no_of_players = 8
single_players = list(all_players[:no_of_players])
player_score = []
for player in single_players:
    player_score.append([player, 0])
round = 0
while round != no_of_players - 1:
    
    print('ROUND - ', round + 1)
    matches = mexicano_matchmaking(player_score)
    round += 1
    for match in matches:
        print('\n')
        a = random.randint(0, point)
        b = point - a
        match[0][1] = a
        match[1][1] = b
        print(match[0][0], 'vs', match[1][0], '\nScore:', match[0][0], ' - ', a, 'vs', match[1][0], ' - ', b)
        player_score = assign_scores(player_score, match)
        player_score.sort(key=lambda x: x[1], reverse=True)
    print('\n\nScores: \n')
    for i in player_score:
        print(i[0], ' - ', i[1],  end=' | ')
    print('\n----------\n')


print('\n ----- TEAM Mexicano ----- \n')
point = 16
no_of_players = 8
team_players = list(all_players[:no_of_players])
team_pairs = [(team_players[i] + '-1' , team_players[i] + '-2') for i in range(8)]
player_score = []
for player in team_pairs:
    player_score.append([player, 0])
round = 0
while round != no_of_players - 1:
    
    print('ROUND - ', round + 1)
    matches = mexicano_matchmaking(player_score, True)
    round += 1
    for match in matches:
        print('\n')
        a = random.randint(0, point)
        b = point - a
        match[0][1] = a
        match[1][1] = b
        print(match[0][0], 'vs', match[1][0], '\nScore:', match[0][0], ' - ', a, 'vs', match[1][0], ' - ', b)
        player_score = assign_scores(player_score, match, True)
        player_score.sort(key=lambda x: x[1], reverse=True)
    print('\n\nScores: \n')
    for i in player_score:
        print(i[0], ' - ', i[1],  end=' | ')
    print('\n----------\n')


    
