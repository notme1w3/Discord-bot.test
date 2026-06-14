import os

XP_MANAGER_ROLE_ID = int(os.getenv("XP_MANAGER_ROLE_ID", 0))

def is_xp_manager(member):
    return any(role.id == XP_MANAGER_ROLE_ID for role in member.roles)
