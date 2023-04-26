def padel_matchmaking(players):
    num_players = len(players)
    if num_players % 2 != 0:
        players.append(None)
        num_players += 1
    group_a = players[:num_players // 2]
    group_b = players[num_players // 2:]
    num_rounds = num_players - 1
    for round_num in range(num_rounds):
        print(f"Round {round_num + 1}:")
        round_matches = []
        for i in range(num_players // 2):
            player_a = group_a[i]
            player_b = group_b[i]
            if player_a is not None and player_b is not None:
                round_matches.append((player_a, player_b))
            print(f"{player_a} vs. {player_b}")
        last_player_a = group_a.pop()
        last_player_b = group_b.pop(0)
        group_a.insert(1, last_player_b)
        group_b.append(last_player_a)
