# rank_manager.py

RANKS = [
    {"name": "Miembro", "xp": 100, "role_id": 0},
    {"name": "Miembro Respetado", "xp": 250, "role_id": 0},
    {"name": "Halconcillo", "xp": 500, "role_id": 0},
    {"name": "Pistolero", "xp": 750, "role_id": 0},
    {"name": "Asesino", "xp": 850, "role_id": 0},
    {"name": "Soldado", "xp": 950, "role_id": 0},
    {"name": "Reclutador", "xp": 1000, "role_id": 0},
    {"name": "Sicario", "xp": 1300, "role_id": 0},
    {"name": "Chofer", "xp": 1750, "role_id": 0},
    {"name": "Teniente", "xp": 2500, "role_id": 0},
    {"name": "Jefe de Plaza", "xp": 3000, "role_id": 0},
    {"name": "Comandante", "xp": 3500, "role_id": 0},
    {"name": "Salamanca Familia", "xp": 4500, "role_id": 0},
    {"name": "Jefe de Operaciones", "xp": 5500, "role_id": 0},
    {"name": "Mano Derecha", "xp": None, "role_id": 0},  # MAX rank
]

def get_rank(index: int):
    return RANKS[index]

def get_next(index: int):
    if index + 1 >= len(RANKS):
        return None
    return RANKS[index + 1]

def is_max(index: int):
    return index >= len(RANKS) - 1
