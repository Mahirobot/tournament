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
        for i in range(num_players // 4):
            player_a = group_a[i]
            player_a1 = group_a[i+1]
            player_b = group_b[i]
            player_b1 = group_b[i+1]
            if player_a is not None and player_b is not None and player_a1 is not None and player_b1 is not None:
                round_matches.append(((player_a, player_a1), (player_b, player_b1)))
            print((player_a, player_a1), 'vs',(player_b, player_b1))
        last_player_a = group_a.pop()
        last_player_a1 = group_a.pop()
        last_player_b = group_b.pop(0)
        last_player_b1 = group_b.pop(0)
        group_a.insert(1, last_player_b)
        group_a.insert(1, last_player_b1)
        group_b.append(last_player_a)
        group_b.append(last_player_a1)
