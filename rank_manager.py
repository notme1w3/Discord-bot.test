RANKS = [
    {"name": "Miembro", "xp": 100},
    {"name": "Miembro Respetado", "xp": 250},
    {"name": "Halconcillo", "xp": 500},
    {"name": "Pistolero", "xp": 750},
    {"name": "Asesino", "xp": 850},
    {"name": "Soldado", "xp": 950},
    {"name": "Reclutador", "xp": 1000},
    {"name": "Sicario", "xp": 1300},
    {"name": "Chofer", "xp": 1750},
    {"name": "Teniente", "xp": 2500},
    {"name": "Jefe de Plaza", "xp": 3000},
    {"name": "Comandante", "xp": 3500},
    {"name": "Salamanca Familia", "xp": 4500},
    {"name": "Jefe de Operaciones", "xp": 5500},
    {"name": "Mano Derecha", "xp": None},
]

def get_rank(index):
    return RANKS[index]

def get_next(index):
    if index + 1 >= len(RANKS):
        return None
    return RANKS[index + 1]

def max_rank(index):
    return index >= len(RANKS) - 1
