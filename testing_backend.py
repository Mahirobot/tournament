import itertools
import math
from bson.objectid import ObjectId
import utils
import internal
import schemas
from database import mongodb_client
from utils import CollInfo, DBInfo


async def americano(players):
    num_players = len(players)
    if num_players % 2 != 0:
        players.append(None)
        num_players += 1
    group_a = players[:num_players // 2]
    group_b = players[num_players // 2:]
    num_rounds = num_players - 1
    matches = []
    for _ in range(num_rounds):
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
        group_a.insert(1, last_player_b1)
        group_b.append(last_player_a)
        group_b.append(last_player_a1)
    return matches


async def team_americano(players):
    num_players = len(players)
    if num_players % 2 != 0:
        players.append(None)
        num_players += 1
    group_a = players[:num_players // 2]
    group_b = players[num_players // 2:]
    num_rounds = num_players - 1
    matches = []
    for _ in range(num_rounds):
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


async def mexicano(players, team = False):
    groups = [players[i:i+4] for i in range(0, len(players), 4)]
    matches = []
    for group in groups:
        if team:
            matches.extend(
                (
                    [[(group[0][0]), 0], [(group[1][0]), 0]],
                    [[(group[2][0]), 0], [(group[3][0]), 0]],
                )
            )
        else:
            matches.append([[(group[0][0], group[3][0]), 0], [(group[1][0], group[2][0]), 0]])
    return matches
    
async def assign_scores(players, match, team = False):
    for item in players:
        for pair, score in match:
            if team and pair == item[0]:
                item[1] += score
            else:
                for player in pair:
                    if player == item[0]:
                        item[1] += score
    return players


async def team_americano_rounds(matches, court_ids, no_courts):
    rounds = []
    court_assigned = 0
    # Get court ids
    
    for round_count, item in enumerate(matches, start=2):
        for match in item:
            rounds.append({
                "court_id": court_ids[court_assigned],
                "teams": [{
                        "player_1": match[0][0],
                        "player_2": match[0][1],
                        "team_score": 0
                    },{
                        "player_1": match[1][0],
                        "player_2": match[1][1],
                        "team_score": 0
                    },
                ],
            "winner": None,
            })
            court_assigned += 1
            if court_assigned == no_courts:
                court_assigned = 0
    return rounds

async def americano_rounds(matches, court_ids, no_courts):
    rounds = []
    court_assigned = 0
    # Get court ids
    
    for match in matches:
        print(match)
        rounds.append({
            "court_id": court_ids[court_assigned],
            "teams": [{
                    "player_1": match[0][0],
                    "player_2": match[0][1],
                    "team_score": 0
                },{
                    "player_1": match[1][0],
                    "player_2": match[1][1],
                    "team_score": 0
                },
            ],
        "winner": None,
        })
        court_assigned += 1
        if court_assigned == no_courts:
            court_assigned = 0
    return rounds

async def mexicano_rounds(matches, court_ids, no_courts, team):
    rounds = []
    court_assigned = 0
    # Get court ids

    for match in matches:
        rounds.append({
            "court_id": court_ids[court_assigned],
            "teams": [{
                    "player_1": match[0][0][0],
                    "player_2": match[0][0][1],
                    "team_score": 0
                },{
                    "player_1": match[1][0][0],
                    "player_2": match[1][0][1],
                    "team_score": 0
                }
        ],
        "winner": None 
        })
        court_assigned += 1
        if court_assigned == no_courts:
            court_assigned = 0
    return rounds

async def get_players(activity_record_id: str):
    players_info = mongodb_client[DBInfo.database][CollInfo.activity_records].find_one(
            {"_id": ObjectId(activity_record_id)},
            {"players": 1}
        )
    return players_info["players"]


async def create_activity_history(activity_record_id: str):

    # Get booking and activity information
    activity_record = mongodb_client[DBInfo.database][CollInfo.activity_records].find_one(
            {"_id": ObjectId(activity_record_id)}
        )
    activity_booking = mongodb_client[DBInfo.database][CollInfo.tournaments].find_one(
            {"_id": ObjectId(activity_record["activity_id"])}
        )

    players = await get_players(activity_record_id)
    no_participants = len(players)

    # Court assignment
    no_courts = len(activity_record["court_ids"])
    court_ids = activity_record["court_ids"]

    # Fix the no of match per round
    if activity_booking["tournament_type"] in ["Team Americano", "Team Mexicano"]:
        match_per_round = math.floor(no_participants / 2)
    else:
        match_per_round = no_participants / 4

    # Fix no of rounds
    if activity_booking["tournament_type"] in ["Team Americano", "Team Mexicano"]:
        no_rounds = max(0, no_participants - 1) if no_participants % 2 == 0 else max(0, no_participants)
    else:
        no_rounds = max(0, no_participants - 1)

    # Create rounds
    if no_participants != 0 and no_participants % 4 == 0:

        if activity_booking["tournament_type"] == "Americano":
            matches = await americano(players)
            rounds = await americano_rounds(matches, court_ids, no_courts)
        if activity_booking["tournament_type"] == "Team Americano":
            matches = await team_americano(players)
            rounds = await americano_rounds(matches, court_ids, no_courts)
        if activity_booking["tournament_type"] == "Mexicano":
            players_score = [[player, 0] for player in players]
            matches = await mexicano(players_score, False)
            rounds = await mexicano_rounds(matches, court_ids, no_courts, False)
        if activity_booking["tournament_type"] == "Team Mexicano":
            players_score = [[player, 0] for player in players]
            matches = await mexicano(players_score, True)
            rounds = await mexicano_rounds(matches, court_ids, no_courts, True)

        # Activity history
        activity_history = {
            "club_id": activity_record["club_id"],
            "activity_id": activity_record["activity_id"],
            "activity_record_id": activity_record_id,
            "activity_type": activity_record["activity_type"],
            "record": {
                "tournament_type": activity_booking["tournament_type"],
                "no_participants": no_participants,
                "no_rounds": no_rounds,
                "match_per_round": match_per_round,
                "no_courts": no_courts,
                "number_of_points": activity_booking["number_of_points"],
                "rounds": rounds
            }
        }

    else:
        # Activity history
        activity_history = {
            "club_id": activity_record["club_id"],
            "activity_id": activity_record["activity_id"],
            "activity_record_id": activity_record_id,
            "activity_type": activity_record["activity_type"],
            "record": {
                "tournament_type": activity_booking["tournament_type"],
                "no_participants": no_participants,
                "no_rounds": no_rounds,
                "match_per_round": match_per_round,
                "no_courts": no_courts,
                "number_of_points": activity_booking["number_of_points"],
                "rounds": []
            }
        }

    mongodb_client[DBInfo.database][CollInfo.tournament_matchmakings].insert_one(activity_history)
    return (schemas.ActivityHistory(**activity_history))


async def delete_activity_history(activity_record_id: str):

    mongodb_client[DBInfo.database][CollInfo.tournament_matchmakings].delete_one(
            {"activity_record_id": activity_record_id}
    )


async def tournament_matchmaking_helper(activity_record_id: str):


    activity_history = mongodb_client[DBInfo.database][CollInfo.tournament_matchmakings].find_one(
        {"activity_record_id": activity_record_id}
    )
    if activity_history is None:
        activity_history = await create_activity_history(activity_record_id)
    elif activity_history["record"]["no_participants"] != len(await get_players(activity_record_id)):
        await delete_activity_history(activity_record_id)
        activity_history = await create_activity_history(activity_record_id)
    return activity_history

out = create_activity_history("6450c56fddcc30988d8aa9f3")
print(out)
