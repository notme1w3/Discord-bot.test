import json
import discord

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

RANKS = sorted(CONFIG["ranks"], key=lambda x: x["xp"])


def get_rank_from_xp(xp: int):
    current_rank = RANKS[0]

    for rank in RANKS:
        if xp >= rank["xp"]:
            current_rank = rank
        else:
            break

    return current_rank


async def sync_member_rank(member: discord.Member, xp: int):

    guild = member.guild

    target_rank = get_rank_from_xp(xp)

    target_role = guild.get_role(target_rank["role_id"])

    if target_role is None:
        return None

    rank_role_ids = [rank["role_id"] for rank in RANKS]

    roles_to_remove = [
        role
        for role in member.roles
        if role.id in rank_role_ids
        and role.id != target_role.id
    ]

    if roles_to_remove:
        await member.remove_roles(
            *roles_to_remove,
            reason="Rank synchronization"
        )

    if target_role not in member.roles:
        await member.add_roles(
            target_role,
            reason="XP Promotion/Demotion"
        )

        return target_rank

    return None


def get_next_rank(xp: int):

    for rank in RANKS:
        if rank["xp"] > xp:
            return rank

    return None
