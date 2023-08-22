from enum import Enum


class EntityType(Enum):
    EMPTY = 0
    PLAYER = 1
    ENEMY = 2
    SIGN = 3


class TileType(Enum):
    GROUND = 0
    WALL = 1
    HAZARD = 2


class EntityMode(Enum):
    IDLE = 0
    FIGHT = 1
