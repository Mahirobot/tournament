import itertools
import math
import operator
from typing import Any, List, Tuple, Union

from bson.objectid import ObjectId

import internal
import schemas
import utils
from database import mongodb_client
from utils import CollInfo, DBInfo


async def americano(players):
    """
    Create single player matches according to the rules of americano matchmaking.
    Args:
        players: List of player ids taken from activity_records["players"]
    Returns:
        matches: List of matches
    """

    num_players = len(players)
    if num_players % 2 != 0:
        players.append(None)
        num_players += 1
    group_a = players[: num_players // 2]
    group_b = players[num_players // 2 :]
    num_rounds = num_players - 1
    matches = []
    for _ in range(num_rounds):
        round_matches = []
        for i in range(num_players // 4):
            player_a = group_a[i]
            player_a1 = group_a[i + 1]
            player_b = group_b[i]
            player_b1 = group_b[i + 1]
            if (
                player_a is not None
                and player_b is not None
                and player_a1 is not None
                and player_b1 is not None
            ):
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
    """
    Create team matches according to the rules of americano matchmaking.
    Args:
        players: List of player ids taken from activity_records["players"].
        This is list of lists that contains two player ids.
    Returns:
        matches: List of matches
    """

    num_players = len(players)
    if num_players % 2 != 0:
        players.append(None)
        num_players += 1
    group_a = players[: num_players // 2]
    group_b = players[num_players // 2 :]
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


async def mexicano(players, team=False, matches=None):
    """
    Create matches according to the rules of mexicano matchmaking.
    Args:
        players: List of player ids taken from activity_records["players"].
        This is list of lists that contains two player ids for team games or just list of player ids for single players.
        team: bool
        matches: always None
    Returns:
        matches: List of matches
    """

    groups = [players[i : i + 4] for i in range(0, len(players), 4)]
    matches = []
    for group in groups:
        if team:
            matches.extend(
                (
                    [group[0][0], group[1][0]],
                    [group[2][0], group[3][0]],
                )
            )
        else:
            matches.append([(group[0][0], group[3][0]), (group[1][0], group[2][0])])
    return matches


async def americano_rounds(matches, court_ids, no_courts):
    """
    Create rounds for americano.
    Args:
        matches: List of matches
        court_ids: List of court ids
        no_courts: Number of available courts
    Returns:
        rounds: List of rounds
    """

    rounds = []
    court_assigned = 0
    # Get court ids

    for item in matches:
        round_match = []
        for match in item:
            round_match.append(
                {
                    "court_info": court_ids[court_assigned],
                    "teams": [
                        {
                            "player_1": match[0][0],
                            "player_2": match[0][1],
                            "team_score": 0,
                        },
                        {
                            "player_1": match[1][0],
                            "player_2": match[1][1],
                            "team_score": 0,
                        },
                    ],
                    "winner": None,
                }
            )
            court_assigned += 1
            if court_assigned == no_courts:
                court_assigned = 0
        rounds.append(round_match)
    return rounds


async def team_americano_rounds(matches, court_ids, no_courts):
    """
    Create rounds for team americano.
    Args:
        matches: List of matches
        court_ids: List of court ids
        no_courts: Number of available courts
    Returns:
        rounds: List of rounds
    """

    rounds = []
    court_assigned = 0
    # Get court ids

    for round_count, item in enumerate(matches, start=2):
        for match in item:
            rounds.append(
                {
                    "court_info": court_ids[court_assigned],
                    "teams": [
                        {
                            "player_1": match[0][0],
                            "player_2": match[0][1],
                            "team_score": 0,
                        },
                        {
                            "player_1": match[1][0],
                            "player_2": match[1][1],
                            "team_score": 0,
                        },
                    ],
                    "winner": None,
                }
            )
            court_assigned += 1
            if court_assigned == no_courts:
                court_assigned = 0
    return rounds


async def mexicano_rounds(matches, court_ids, no_courts, team):
    """
    Create rounds for meaxicano and team mexicano.
    Args:
        matches: List of matches
        court_ids: List of court ids
        no_courts: Number of available courts
        team: bool, True means it's for team mexicano
    Returns:
        rounds: List of rounds
    """

    court_assigned = 0
    # Get court ids
    round_matches = []
    for match in matches:
        round_matches.append(
            {
                "court_info": court_ids[court_assigned],
                "teams": [
                    {"player_1": match[0][0], "player_2": match[0][1], "team_score": 0},
                    {"player_1": match[1][0], "player_2": match[1][1], "team_score": 0},
                ],
                "winner": None,
            }
        )
        court_assigned += 1
        if court_assigned == no_courts:
            court_assigned = 0
    return [round_matches]


async def get_players(activity_record_id: str):
    """
    Get a list of player for the given activity record id.
    Args:
        activity_record_id: str
    Returns:
        List of players/ List of lists of players
    """

    players_info = mongodb_client[DBInfo.database][CollInfo.activity_records].find_one(
        {"_id": ObjectId(activity_record_id)}, {"players": 1}
    )
    assert players_info is not None, "No player list found."
    return players_info["players"]


async def get_court_ids(activity_record_id: str):
    """
    Get a list of court_ids for the given activity record id.
    Args:
        activity_record_id: str
    Returns:
        List of court_ids
    """

    court_ids_info = mongodb_client[DBInfo.database][
        CollInfo.activity_records
    ].find_one({"_id": ObjectId(activity_record_id)}, {"court_ids": 1})
    assert court_ids_info is not None, "No court id found."
    return court_ids_info["court_ids"]


async def make_rounds(tournament_type, players, court_ids, no_courts):
    """
    Creates rounds according to tournament type.
    Args:
        tournament_type: any from -> ["Americano", "Team Americano", "Mexicano", "Team Mexicano"]
        players: List of players/ List of lists of players
        court_ids: List of court_ids
        no_courts: Number of available courts
    Returns:
        List of rounds
    """
    if tournament_type == "Americano":
        matches = await americano(players)
        rounds = await americano_rounds(matches, court_ids, no_courts)
    if tournament_type == "Team Americano":
        matches = await team_americano(players)
        rounds = await americano_rounds(matches, court_ids, no_courts)
    if tournament_type == "Mexicano":
        players_score = [[player, 0] for player in players]
        matches = await mexicano(players_score, False)
        rounds = await mexicano_rounds(matches, court_ids, no_courts, False)
    if tournament_type == "Team Mexicano":
        players_score = [[player, 0] for player in players]
        matches = await mexicano(players_score, True)
        rounds = await mexicano_rounds(matches, court_ids, no_courts, True)

    return rounds


async def get_match_per_round(tournament_type, no_participants):
    """
    Depending on the type of tournament returns the number of matches per round.
    Args:
        tournament_type: any from -> ["Americano", "Team Americano", "Mexicano", "Team Mexicano"]
        no_participants: int
    Returns:
        match_per_round
    """

    return (
        math.floor(no_participants / 2)
        if tournament_type in ["Team Americano", "Team Mexicano"]
        else no_participants / 4
    )


async def get_no_of_rounds(tournament_type, no_participants):
    """
    Depending on the type of tournament returns the number of rounds.
    Args:
        tournament_type: any from -> ["Americano", "Team Americano", "Mexicano", "Team Mexicano"]
        no_participants: int
    Returns:
        no_of_rounds
    """

    if tournament_type in ["Team Americano", "Team Mexicano"]:
        return (
            max(0, no_participants - 1)
            if no_participants % 2 == 0
            else max(0, no_participants)
        )
    else:
        return max(0, no_participants - 1)


async def base_activity_history(
    club_id, activity_id, activity_record_id, activity_type, number_of_points
):
    """
    Creates the basic activity history given the information.
    Args:
        club_id: str
        activity_id: str
        activity_record_id: str
        activity_type: str
        number_of_points: int
    Returns:
        schemas.ActivityHistory
    """

    return {
        "club_id": club_id,
        "activity_id": activity_id,
        "activity_record_id": activity_record_id,
        "activity_type": activity_type,
        "record": {
            "tournament_type": None,
            "max_players": 0,
            "no_participants": 0,
            "no_rounds": 0,
            "match_per_round": 0,
            "court_ids": None,
            "number_of_points": number_of_points,
            "summary": [],
            "rounds": [],
        },
    }


async def create_summary(players, summary=None):
    """
    Creates the basic summary of tournament given the information.
    Args:
        playters: List of players
        summary: Always None
    Returns:
        schemas.TournamentSummary
    """

    if summary is None:
        summary = []
    team = True if type(players[0]) == list else False

    for player in players:
        if team:
            player_info = [
                await internal.get_player_info(player[0]),
                await internal.get_player_info(player[1]),
            ]
        else:
            player_info = [
                await internal.get_player_info(player),
            ]

        summary.append(
            {
                "player_info": player_info,
                "matches": [],
                "points_won": 0,
                "points_lost": 0,
                "total_points_played": 0,
                "arrived": False,
            }
        )
    return summary


async def max_player_check(activity_id: str, current_max: int):
    """
    Check if the max player count has changed.

    Args:
       activity_id: str
       current_max: int

    Returns:
        bool
    """
    activity_booking = mongodb_client[DBInfo.database][CollInfo.tournaments].find_one(
        {"_id": ObjectId(activity_id)}
    )
    assert (
        activity_booking is not None
    ), f"Could not find the booking for activity id: {activity_id}"
    return activity_booking["no_of_players"] != current_max


async def create_activity_history(activity_record_id: str):
    """
    Creates activity history given activity_record_id.
    Args:
        activity_record_id: str
    Returns:
        schemas.ActivityHistory
    """

    # Get booking and activity information
    activity_record = mongodb_client[DBInfo.database][
        CollInfo.activity_records
    ].find_one({"_id": ObjectId(activity_record_id)})
    assert (
        activity_record is not None
    ), f"Could not find the activity record for activity id: {activity_record_id}"
    activity_booking = mongodb_client[DBInfo.database][CollInfo.tournaments].find_one(
        {"_id": ObjectId(activity_record["activity_id"])}
    )
    assert (
        activity_booking is not None
    ), f"Could not find the booking for activity id: {activity_record['activity_id']}"

    # Create an activity history
    activity_history = await base_activity_history(
        activity_record["club_id"],
        activity_record["activity_id"],
        activity_record_id,
        activity_record["activity_type"],
        activity_booking["number_of_points"],
    )

    # Set tournament type
    activity_history["record"]["tournament_type"] = activity_booking["tournament_type"]

    # Get max players
    activity_history["record"]["max_players"] = activity_booking["no_of_players"]

    # Get players or teams
    players = await get_players(activity_record_id)
    activity_history["record"]["no_participants"] = len(players)

    # Create summary
    activity_history["record"]["summary"] = await create_summary(players)

    # Court assignment
    no_courts = len(activity_record["court_ids"])
    activity_history["record"]["court_ids"] = activity_record["court_ids"]

    # Fix the no of match per round
    activity_history["record"]["match_per_round"] = await get_match_per_round(
        activity_booking["tournament_type"],
        activity_history["record"]["no_participants"],
    )

    # Fix no of rounds
    if "number_of_rounds" in activity_booking.keys():
        activity_history["record"]["no_rounds"] = activity_booking["number_of_rounds"]
    else:
        activity_history["record"]["no_rounds"] = await get_no_of_rounds(
            activity_booking["tournament_type"],
            activity_history["record"]["no_participants"],
        )

    # Create rounds
    # Schedule is empty if requirement for total number of players is not met
    if (
        activity_history["record"]["no_participants"] != 0
        and activity_history["record"]["no_participants"] > 3
        and activity_history["record"]["no_participants"]
        == activity_booking["no_of_players"]
    ):
        if activity_history["record"]["no_participants"] % 4 == 0:

            activity_history["record"]["rounds"] = await make_rounds(
                activity_booking["tournament_type"],
                players,
                activity_history["record"]["court_ids"],
                no_courts,
            )

        elif activity_booking["tournament_type"] == "Team Americano":
            activity_history["record"]["rounds"] = await make_rounds(
                activity_booking["tournament_type"],
                players,
                activity_history["record"]["court_ids"],
                no_courts,
            )

    mongodb_client[DBInfo.database][CollInfo.tournament_matchmakings].insert_one(
        activity_history
    )
    return activity_history


async def delete_activity_history(activity_record_id: str):
    """
    Deletes activity history given activity_record_id.
    Args:
        activity_record_id: str
    """

    mongodb_client[DBInfo.database][CollInfo.tournament_matchmakings].delete_one(
        {"activity_record_id": activity_record_id}
    )


async def replace_court_and_player_id_with_name(activity_history):
    """
    Replace activity history court player id with info

    Args:
        activity_history: schemas.ActivityHistory

    Returns:
        schemas.ActivityHistory
    """
    players = await get_players(activity_history["activity_record_id"])
    team = type(players[0]) == list
    for _round in activity_history["record"]["rounds"]:
        for _match in _round:
            _match["court_info"] = await internal.get_court_info(_match["court_info"])
            for _team in _match["teams"]:
                if team:
                    summary_idx = players.index([_team["player_1"], _team["player_2"]])
                    _team["player_1"] = activity_history["record"]["summary"][
                        summary_idx
                    ]["player_info"][0]
                    _team["player_2"] = activity_history["record"]["summary"][
                        summary_idx
                    ]["player_info"][1]
                else:
                    summary_idx_1 = players.index(_team["player_1"])
                    summary_idx_2 = players.index(_team["player_2"])
                    _team["player_1"] = activity_history["record"]["summary"][
                        summary_idx_1
                    ]["player_info"][0]
                    _team["player_2"] = activity_history["record"]["summary"][
                        summary_idx_2
                    ]["player_info"][0]

    return activity_history


async def tournament_matchmaking_helper(activity_record_id: str):
    """
    Creates activity history if there's none, updates it if there's a change in participant
    number or court id, fetches the activity history otherwise

    Args:
        activity_record_id: str
    Returns:
        schemas.ActivityHistory
    """
    try:
        activity_history = mongodb_client[DBInfo.database][
            CollInfo.tournament_matchmakings
        ].find_one({"activity_record_id": activity_record_id})
        # Create new schedule if one does not exist
        if activity_history is None:
            activity_history = await create_activity_history(activity_record_id)

        # If participant number, court id or max participant count changes recreate schedule
        elif (
            activity_history["record"]["no_participants"]
            != len(await get_players(activity_record_id))
            or activity_history["record"]["court_ids"]
            != await get_court_ids(activity_record_id)
            or (
                await max_player_check(
                    activity_history["activity_id"],
                    activity_history["record"]["max_players"],
                )
            )
        ):

            await delete_activity_history(activity_record_id)
            activity_history = await create_activity_history(activity_record_id)

        activity_history = await replace_court_and_player_id_with_name(activity_history)
        # Just fetch schedule otherwise
        return schemas.ActivityHistory(**activity_history)
    except Exception as e:
        utils.raise_exception(e=e)


async def update_tournament_summary(
    activity_record_id,
    players,
    tournament_info,
    player_id,
    points_won,
    points_lost,
    points_played,
    edit,
    current_winner_team,
    winner_team,
):
    """
    Update tournament summary.
    Args:
        activity_record_id: str
        players: List
        tournament_info: scemas.TournamentRecord
        player_id: str
        points_won: int
        points_lost: int
        points_played: int
        edit: bool
        current_winner_team: int
        winner_team: int
    Returns:
        tournament_info: scemas.TournamentRecord
    """

    summary_idx = players.index(player_id)
    if edit:
        if current_winner_team == 0:
            tournament_info["summary"][summary_idx]["matches"].remove(1)
        else:
            tournament_info["summary"][summary_idx]["matches"].remove(0)
    if winner_team == 0:
        tournament_info["summary"][summary_idx]["matches"].append(1)
    else:
        tournament_info["summary"][summary_idx]["matches"].append(0)

    tournament_info["summary"][summary_idx]["points_won"] += points_won
    tournament_info["summary"][summary_idx]["points_lost"] += points_lost
    tournament_info["summary"][summary_idx]["total_points_played"] += points_played

    return tournament_info


async def update_flag(edit, tournament_info, round_idx):
    """
    Check if updating score is allowed.
    Args:
        edit: bool
        tournament_info: schemas.TournamentRecord
        round_idx: int
    Returns:
        bool
    """

    return bool(
        (
            edit
            and tournament_info["tournament_type"] in ["Mexicano", "Team Meaxicano"]
            and round_idx < len(tournament_info["rounds"])
        )
    )


async def get_winner(team_1_score: int, team_2_score: int):
    """
    Get the winner given team score.
    Args:
        team_1_score: int
        team_2_score: int
    Returns:
        winner: str -> Team 1, Team 2, Draw
        team_1_winner: int -> 1 if winner is team 1
        team_2_winner: int -> 0 if winner is team 1
    """

    winner = None
    team_1_winner = 0
    team_2_winner = 0
    if team_1_score > team_2_score:
        winner = "Team 1"
        team_1_winner = 1
    elif team_1_score < team_2_score:
        winner = "Team 2"
        team_2_winner = 1
    else:
        winner = "Draw"
    return winner, team_1_winner, team_2_winner


async def get_tournament_info(activity_record_id: str):
    """
    Get tournament record.
    Args:
        activity_record_id: str
    Returns:
        schemas.TournamentRecord
    """

    tournament_info = mongodb_client[DBInfo.database][
        CollInfo.tournament_matchmakings
    ].find_one(
        {"activity_record_id": activity_record_id},
        {"record"},
    )
    assert tournament_info is not None, "No record found for tournament."
    return tournament_info["record"]


async def create_next_mexicano_round(
    activity_record_id: str, round_idx: int, query: bool = False
):
    """
    Create next round of mexicano if there are rounds left.
    Args:
        activity_record_id: str
        round_idx: int
        query: bool (To add a new round when specifically instructed)
    """

    # Get tournament info
    tournament_info = await get_tournament_info(activity_record_id)
    # Create new round for Mexicano and Team Mexicano
    create_round = True
    if tournament_info["tournament_type"] in ["Mexicano", "Team Mexicano"]:
        if tournament_info["no_rounds"] == len(tournament_info["rounds"]) and not query:
            create_round = False
        for match in tournament_info["rounds"][round_idx]:
            if match["winner"] is None or not create_round:
                create_round = False
                break

        if create_round:
            players = await get_players(activity_record_id)
            player_score = [
                [player, info["points_won"]]
                for player, info in zip(players, tournament_info["summary"])
            ]

            player_score.sort(key=operator.itemgetter(1), reverse=True)
            if tournament_info["tournament_type"] == "Mexicano":
                matches = await mexicano(player_score, team=False)
                rounds = await mexicano_rounds(
                    matches,
                    tournament_info["court_ids"],
                    len(tournament_info["court_ids"]),
                    False,
                )
            else:
                matches = await mexicano(player_score, team=True)
                rounds = await mexicano_rounds(
                    matches,
                    tournament_info["court_ids"],
                    len(tournament_info["court_ids"]),
                    True,
                )
            mongodb_client[DBInfo.database][
                CollInfo.tournament_matchmakings
            ].update_one(
                {"activity_record_id": activity_record_id},
                {"$push": {"record.rounds": rounds[0]}},
            )

            # TODO If no score has been updated in new round of mexicano, user can update previous round score


async def update_score_db(
    activity_record_id: str,
    round_idx: int,
    match_idx: int,
    team_1_score: int,
    team_2_score: int,
):
    """
    Updates score of a match. Returns string declaring winner or states if the score can't be updated.
    Args:
        activity_record_id: str
        round_idx: int -> from 0 to len(rounds)
        match_idx: int -> from 0 to len(matches)
        team_1_score: int
        team_2_score: int
    Returns:
        string -> [Team 1, Team 2, Draw, "Cannot Update"]
    """
    try:
        winner, team_1_winner, team_2_winner = await get_winner(
            team_1_score, team_2_score
        )

        # Get tournament info
        tournament_info = await get_tournament_info(activity_record_id)

        if (
            round_idx + 1 > tournament_info["no_rounds"]
            or match_idx + 1 > tournament_info["match_per_round"]
        ):
            return "Cannot Update"

        # Edit or update score flag
        current_score_1 = tournament_info["rounds"][round_idx][match_idx]["teams"][0][
            "team_score"
        ]
        current_score_2 = tournament_info["rounds"][round_idx][match_idx]["teams"][1][
            "team_score"
        ]
        edit = True
        if current_score_1 == 0 and current_score_2 == 0:
            edit = False
            curr_1_win = 0
            curr_2_win = 0
        else:
            current_winner, curr_1_win, curr_2_win = await get_winner(
                current_score_1, current_score_2
            )

        # If it is a previous round of mexicano score cannot be updated
        if (
            edit
            and tournament_info["tournament_type"] in ["Mexicano", "Team Mexicano"]
            and round_idx + 1 != len(tournament_info["rounds"])
        ):
            # TODO Created new round but no score has been updated yet
            return "Cannot Update"

        # Update score
        mongodb_client[DBInfo.database][CollInfo.tournament_matchmakings].update_one(
            {"activity_record_id": activity_record_id},
            {
                "$set": {
                    f"record.rounds.{round_idx}.{match_idx}.winner": winner,
                    f"record.rounds.{round_idx}.{match_idx}.teams.0.team_score": team_1_score,
                    f"record.rounds.{round_idx}.{match_idx}.teams.1.team_score": team_2_score,
                }
            },
        )
        players = await get_players(activity_record_id)

        # Calculate points
        points_won_t1 = (current_score_1 - team_1_score) * -1
        points_lost_t1 = (current_score_2 - team_2_score) * -1
        points_played = (
            (current_score_1 + current_score_2) - (team_1_score + team_2_score)
        ) * -1

        # If it's a team game
        if tournament_info["tournament_type"] in ["Team Americano", "Team Mexicano"]:

            for team in range(2):
                if team == 0:
                    points_won = points_won_t1
                    points_lost = points_lost_t1
                    current_winner_team = curr_1_win
                    winner_team = team_1_winner
                    player_id = [
                        tournament_info["rounds"][round_idx][match_idx]["teams"][0][
                            "player_1"
                        ],
                        tournament_info["rounds"][round_idx][match_idx]["teams"][0][
                            "player_2"
                        ],
                    ]
                else:
                    points_won = points_lost_t1
                    points_lost = points_won_t1
                    current_winner_team = curr_2_win
                    winner_team = team_2_winner
                    player_id = [
                        tournament_info["rounds"][round_idx][match_idx]["teams"][1][
                            "player_1"
                        ],
                        tournament_info["rounds"][round_idx][match_idx]["teams"][1][
                            "player_2"
                        ],
                    ]

                # Updating team 1 score

                tournament_info = await update_tournament_summary(
                    activity_record_id,
                    players,
                    tournament_info,
                    player_id,
                    points_won,
                    points_lost,
                    points_played,
                    edit,
                    current_winner_team,
                    winner_team,
                )

        # If it is not a team game
        else:
            for team in range(2):
                if team == 0:
                    points_won = points_won_t1
                    points_lost = points_lost_t1
                    current_winner_team = curr_1_win
                    winner_team = team_1_winner
                else:
                    points_won = points_lost_t1
                    points_lost = points_won_t1
                    current_winner_team = curr_2_win
                    winner_team = team_2_winner
                for player_idx in ["player_1", "player_2"]:
                    # Updating player 1 of team 1 score
                    player_id = tournament_info["rounds"][round_idx][match_idx][
                        "teams"
                    ][team][player_idx]
                    tournament_info = await update_tournament_summary(
                        activity_record_id,
                        players,
                        tournament_info,
                        player_id,
                        points_won,
                        points_lost,
                        points_played,
                        edit,
                        current_winner_team,
                        winner_team,
                    )

        # Update score
        mongodb_client[DBInfo.database][CollInfo.tournament_matchmakings].update_one(
            {"activity_record_id": activity_record_id},
            {"$set": {"record.summary": tournament_info["summary"]}},
        )
        await create_next_mexicano_round(activity_record_id, round_idx)
        return winner
    except Exception as e:
        utils.raise_exception(e=e)


async def update_court_db(
    activity_record_id: str, round_idx: int, match_idx: int, court_id: str
):
    """
    Updates the court of a match.
    Args:
        activity_record_id: str
        round_idx: int
        match_idx: int
        court_id: str
    Returns:
        string message
    """

    try:
        # Get record
        tournament_info = mongodb_client[DBInfo.database][
            CollInfo.tournament_matchmakings
        ].find_one(
            {"activity_record_id": activity_record_id},
            {"record.court_ids"},
        )
        assert tournament_info is not None, "No record found for tournament."

        if court_id in tournament_info["record"]["court_ids"]:
            # Update court
            mongodb_client[DBInfo.database][
                CollInfo.tournament_matchmakings
            ].update_one(
                {"activity_record_id": activity_record_id},
                {
                    "$set": {
                        f"record.rounds.{round_idx}.{match_idx}.court_info": court_id
                    }
                },
            )
            return "Court updated."
        else:
            return "Court not selected for tournament."
    except Exception as e:
        utils.raise_exception(e=e)


async def get_tournament_brackets_db(activity_record_id: str):
    """
    Get tournament bracket from summary
    Args:
        activity_records_id: str
    Returns:
        schemas.TournamentBracket
    """

    # Get record
    try:
        tournament_summary = mongodb_client[DBInfo.database][
            CollInfo.tournament_matchmakings
        ].find_one(
            {"activity_record_id": activity_record_id},
            {"record.summary"},
        )
        assert tournament_summary is not None, "No summary found for tournament."

        brackets = [
            {
                "player_info": item["player_info"],
                "total_matches": len(item["matches"]),
                "matches_won": sum(item["matches"]),
                "point_difference": item["points_won"] - item["points_lost"],
                "total_points": item["points_won"],
            }
            for item in tournament_summary["record"]["summary"]
        ]

        return sorted(
            brackets,
            key=lambda e: (e["total_points"], e["point_difference"], e["matches_won"]),
            reverse=True,
        )
    except Exception as e:
        utils.raise_exception(e=e)


async def create_new_round_db(activity_record_id: str):
    """
    Create a new round for Mexicano/ Team mexicano

    Args:
        activity_record_id: str
    """
    try:
        # Get record
        tournament_summary = mongodb_client[DBInfo.database][
            CollInfo.tournament_matchmakings
        ].find_one(
            {"activity_record_id": activity_record_id},
            {"record"},
        )
        assert tournament_summary is not None, "No summary found for tournament."
        assert (
            len(tournament_summary["record"]["rounds"])
            == tournament_summary["record"]["no_rounds"]
        ), "Current rounds not played."

        if tournament_summary["record"]["tournament_type"] in [
            "Mexicano",
            "Team Mexicano",
        ]:
            await create_next_mexicano_round(
                activity_record_id, tournament_summary["record"]["no_rounds"] - 1, True
            )

            # Update record
            tournament_summary = mongodb_client[DBInfo.database][
                CollInfo.tournament_matchmakings
            ].update_one(
                {"activity_record_id": activity_record_id},
                {"$inc": {"record.no_rounds": 1}},
            )
            return "Created"
        return "Can only create round for Mexicano and Team Mexicano."
    except Exception as e:
        utils.raise_exception(e=e)


async def get_player_list_tournament_db(activity_record_id: str):
    """Get player id and arrival flag.

    Args:
        activity_record_id: str

    Returns:
        List[schemas.TournamentParticipants]
    """
    try:
        # Get record
        tournament = mongodb_client[DBInfo.database][
            CollInfo.tournament_matchmakings
        ].find_one(
            {"activity_record_id": activity_record_id},
            {"record.summary"},
        )
        assert tournament is not None, "No summary found for tournament."

        return [
            {
                "player_info": item["player_info"],
                "arrived": item["arrived"],
            }
            for item in tournament["record"]["summary"]
        ]
    except Exception as e:
        utils.raise_exception(e=e)


async def update_participants_flag_db(
    activity_record_id: str, here: bool, player_id: Union[str, List[str]]
):
    """Update arrival flag.

    Args:
        activity_record_id: str
        player_id: Union[str, List[str]]
    """
    try:
        player = player_id[0] if type(player_id) == list else player_id
        # Get record
        mongodb_client[DBInfo.database][CollInfo.tournament_matchmakings].update_one(
            {
                "activity_record_id": activity_record_id,
                "record.summary.player_info.player_id": player,
            },
            {"$set": {"record.summary.$.arrived": here}},
        )
    except Exception as e:
        utils.raise_exception(e=e)
