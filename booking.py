############################
#       Join Request       #
############################
async def get_requests_list_db(activity_record_id: str, activity: str):
    """Get all join requests.

    Args:
        activity_record_id: str

    Returns:
        Union[str, List[str]]
    """
    try:
        players = list(
            mongodb_client[DBInfo.database][CollInfo.activity_joins].find(
                {
                    "activity_record_id": activity_record_id,
                    "activity": activity,
                    "payment_method": "PAY LATER",
                    "join_request": "PENDING",
                },
                {"team": 1, "player_ids": 1},
            )
        )
        if players:
            activity_joins = []
            for player in players:
                if player["team"]:
                    activity_joins.append(
                        {
                            "activity_joins_id": str(player["_id"]),
                            "player_infos": [
                                await internal.get_player_info(player["player_ids"][0]),
                                await internal.get_player_info(player["player_ids"][1]),
                            ],
                        }
                    )
                else:
                    activity_joins.append(
                        {
                            "activity_joins_id": str(player["_id"]),
                            "player_infos": [
                                await internal.get_player_info(player["player_ids"][0])
                            ],
                        }
                    )
            return activity_joins
        else:
            return []
    except Exception as e:
        utils.raise_exception(e=e)


async def update_join_request_db(activity_joins_id: str, req: str):
    """Update a request to "ACCEPTED" or "REJECTED".

    Args:
        activity_joins_id: str
        req: str
    """
    try:
        activity_joins_doc = mongodb_client[DBInfo.database][
            CollInfo.activity_joins
        ].find_one_and_update(
            {
                "_id": ObjectId(activity_joins_id),
            },
            {"$set": {"join_request": req}},
        )

        if activity_joins_doc is None:
            return []
        # Update activity_records
        mongodb_client[DBInfo.database][CollInfo.activity_records].update_one(
            {
                "_id": ObjectId(activity_joins_doc["activity_record_id"]),
            },
            {
                "$push": {
                    "players": activity_joins_doc["player_ids"]
                    if activity_joins_doc["team"]
                    else activity_joins_doc["player_ids"][0]
                }
            },
        )
        return activity_joins_doc["player_ids"]
    except Exception as e:
        utils.raise_exception(e=e)


###################
#   Player List   #
###################
async def get_player_list_db(activity_record_id: str):
    """Get players list from activity records.

    Args:
        activity_record_id: str
    """
    try:
        # Get players
        players = mongodb_client[DBInfo.database][CollInfo.activity_records].find_one(
            {"_id": ObjectId(activity_record_id)},
            {"players"},
        )
        assert players is not None, "Could not find players for this activity."
        player_infos = []
        for player in players["players"]:
            player_infos.append(await internal.get_player_info(player))
        return player_infos
    except Exception as e:
        utils.raise_exception(e=e)


#################
#   Lock Slot   #
#################
async def lock_slot_db(activity_records_id: str, names: Optional[List[str]] = None):
    """Locks a spot for a player or a team.

    Args:
        activity_records_id: str
        names: Optional[List[str]]
    """

    if names is None:
        names = [""]
    try:
        players = mongodb_client[DBInfo.database][CollInfo.activity_records].find_one(
            {"_id": ObjectId(activity_records_id)}, {"players": 1}
        )
        assert players is not None, "Could not fins players."

        curr_player = len(players["players"]) + 1
        ls = f"__lock_slot__{str(curr_player).rjust(3, '0')}__"

        participant = [ls + name for name in names] if len(names) > 1 else ls + names[0]

        mongodb_client[DBInfo.database][CollInfo.activity_records].update_one(
            {"_id": ObjectId(activity_records_id)}, {"$push": {"players": participant}}
        )
        return [participant] if type(participant) != list else participant
    except Exception as e:
        utils.raise_exception(e=e)


##############################
#    Available court list    #
##############################
async def get_all_available_courts_db(
    club_id: str, start_datetime: int, end_datetime: int
):
    """Get all available courts of a club from the database.

    Args:
        club_id (str): Club ID

    Returns:
        List: A list of available Court documents of a club from the database.
            List[schemas.Court]
    """

    try:
        court_infos = list(
            mongodb_client[DBInfo.database][CollInfo.courts].find({"club_id": club_id})
        )
        activity_record_infos = list(
            mongodb_client[DBInfo.database][CollInfo.activity_records].find(
                {
                    "club_id": club_id,
                    "start_datetime": {"$gte": start_datetime, "$lte": end_datetime},
                },
                {"court_ids": 1},
            )
        )
        court_ids = []
        if activity_record_infos:
            for item in activity_record_infos:
                court_ids.extend(item["court_ids"])

        return [court for court in court_infos if str(court["_id"]) not in court_ids]
    except Exception as e:
        utils.raise_exception(e=e)


async def get_player_info(player_id: str):
    """
    Get player name and photo_url

    Args:
        player_id: str

    Returns:
        {
            "player_id": "string",
            "name": "string",
            "photo_url": "string"
        }
    """
    if player_id.startswith("__lock_slot__"):
        return {"player_id": "", "name": player_id[18:], "photo_url": ""}
    out = mongodb_client[DBInfo.database][CollInfo.players].find_one(
        {"_id": player_id},
        {"name", "photo_url"},
    )
    assert out is not None, "Could not find player info."
    return {"player_id": player_id, "name": out["name"], "photo_url": out["photo_url"]}


async def get_court_info(court_id: str):
    """
    Get court name

    Args:
        court_id: str

    Returns:
        {
            "court_id": "string",
            "name": "string",
        }
    """
    out = mongodb_client[DBInfo.database][CollInfo.courts].find_one(
        {"_id": ObjectId(court_id)},
        {"name"},
    )
    assert out is not None, "Could not find court info."
    return {
        "court_id": court_id,
        "name": out["name"],
    }
