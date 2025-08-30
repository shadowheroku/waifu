from Bot.database import db

async def get_team_by_user(user_id):
    return await db.Teams.find_one({"user_id": user_id})


async def get_team_by_captain(captain_id):
    return await db.Teams.find_one({"captain_id": captain_id})

async def create_or_update_team(user_id, team_name, captain_id=None, players_ids=None):
    update_payload = {
        "team_name": team_name,
        "captain_id": captain_id or user_id,
        "players_ids": players_ids or [],
    }

    await db.Teams.update_one(
        {"user_id": user_id},
        {"$set": update_payload},
        upsert=True
    )

async def add_player_to_team(user_id, player_id):
    result = await db.Teams.update_one(
        {"user_id": user_id},
        {"$addToSet": {"players_ids": player_id}}
    )
    
    if result.matched_count == 0:
        await create_or_update_team(user_id, f"{user_id}'s Team", None, [player_id])

async def remove_player_from_team(user_id, player_id):
    await db.Teams.update_one(
        {"user_id": user_id},
        {"$pull": {"players_ids": player_id}}
    )

async def delete_team(user_id):
    result = await db.Teams.delete_one({"user_id": user_id})
    return result.deleted_count > 0

async def get_all_teams():
    return await db.Teams.find().to_list(length=None)

async def get_team_players(user_id):
    team = await db.Teams.find_one(
        {"user_id": user_id}, 
        {"players_ids": 1, "_id": 0}
    )
    return team.get("players_ids", []) if team else []

async def get_teams_with_player(player_id):
    return await db.Teams.find({"players_ids": player_id}).to_list(length=None)

async def rename_team(user_id, new_team_name):
    result = await db.Teams.update_one(
        {"user_id": user_id},
        {"$set": {"team_name": new_team_name}}
    )
    return result.matched_count > 0

async def change_team_captain(user_id, new_captain_id):
    result = await db.Teams.update_one(
        {"user_id": user_id, "players_ids": new_captain_id},
        {"$set": {"captain_id": new_captain_id}}
    )
    
    return result.matched_count > 0
