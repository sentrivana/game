import logging
import random

from game.assets import ASSETS, TEXTS
from game.consts import ENTITY_SIZE_PIXELS, TILE_SIZE_PIXELS
from game.events import CustomEvent
from game.level.types import EntityMode, ItemType
from game.utils import post_event


logger = logging.getLogger(__name__)


class Entity:
    MAX_HEALTH = 3

    def __init__(self, level, row, col, type_):
        self.level = level
        self.row = row
        self.col = col
        self.type = type_

        self.asset = ASSETS.load("entities", self.type)

        self.mode = EntityMode.IDLE

        self.text = None
        self.color = None

        self.can_bob = False

        logger.debug("Spawned %s at %d %d", self.type, row, col)

    @property
    def pos(self):
        return (self.row, self.col)

    def render(self, screen, top_left, bob=False):
        if self.mode == EntityMode.IDLE:
            left = (self.col - top_left[1]) * TILE_SIZE_PIXELS + (
                TILE_SIZE_PIXELS - ENTITY_SIZE_PIXELS
            ) // 2
            top = (self.row - top_left[0]) * TILE_SIZE_PIXELS + (
                TILE_SIZE_PIXELS - ENTITY_SIZE_PIXELS
            ) // 2
            if self.can_bob and bob:
                top -= 5
            screen.blit(self.asset, (left, top))

    def interact(self):
        logger.debug("Interacting with %s at %d %d", self.type, self.row, self.col)


class Player(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.inventory = []
        self.health = self.MAX_HEALTH


class Sign(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.text = TEXTS.get_text("signs")

    def interact(self):
        post_event(CustomEvent.SHOW_TEXT, text=self.text)


class Enemy(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.text = TEXTS.get_text("enemies")
        self.color = random.choice(["magenta", "green", "cyan", "violet"])
        self.minigame = None
        self.difficulty = None
        self.can_bob = True

        self.health = self.MAX_HEALTH

    @property
    def boss(self):
        return self.difficulty >= 9

    def set_properties(self, difficulty, minigame):
        self.difficulty = difficulty
        self.minigame = minigame(self)

    def interact(self):
        if self.mode == EntityMode.IDLE:
            self.mode = EntityMode.FIGHT

            small_text = None
            if self.minigame:
                small_text = self.minigame.description

            post_event(
                CustomEvent.SHOW_TEXT,
                text=self.text,
                small_text=small_text,
                color=self.color,
            )
            post_event(
                CustomEvent.INITIALIZE_MINIGAME,
                minigame=self.minigame,
                enemy=self,
            )

    def damage_received(self):
        self.health -= 1
        if self.health <= 0:
            post_event(CustomEvent.ENEMY_DEFEATED, enemy=self)

        self.minigame.flashes = 3
        self.minigame.set_blurp(TEXTS.get_text("enemy_hit", exhaust=False), good=True)
        self.minigame.reset()

    def player_hit(self):
        if self.minigame is not None:
            self.minigame.jitters = 3
            self.minigame.set_blurp(
                TEXTS.get_text("player_hit", exhaust=False), good=False
            )
            self.minigame.reset()


class Key(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_bob = True

    def interact(self):
        post_event(CustomEvent.KEY_PICKED_UP, entity=self)


class Door(Entity):
    def interact(self):
        if ItemType.KEY in self.level.player.inventory:
            post_event(CustomEvent.DOOR_OPENED, entity=self)


class Tree(Entity):
    pass


class Win(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_bob = True

    def interact(self):
        post_event(CustomEvent.LEVEL_CLEARED, text=TEXTS.get_text("level_cleared"))
