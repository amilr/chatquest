from typing import Dict, List
from collections import namedtuple
from enum import Enum
from pydantic import BaseModel

Point = namedtuple('Point', ['x', 'y'])

class Town(BaseModel):
    name: str
    description: str
    image_prompt: str

class Place(BaseModel):
    description: str

class NPC(BaseModel):
    description: str
    appearance: str

class TownList(BaseModel):
    items: List[Town]

class PlaceList(BaseModel):
    items: List[Place]

class NPCList(BaseModel):
    items: List[NPC]

class WorldStatus(Enum):
    NotStarted = 1
    Creating = 2
    Started = 3

class GenImage(BaseModel):
    data: bytes
    dirty: bool

class World:
    def __init__(self):
        self.description = None
        self.towns: List[Town] = None
        self.towns_images: List[bytes] = []
        self.map = None
        self.location = None
        self.places_dict: Dict[str, Place] = {}
        self.places_images_dict: Dict[str, GenImage] = {}
        self.npcs_dict: Dict[str, List[NPC]] = {}

        self.status = WorldStatus.NotStarted
        self.current_town = None

    def init_map(self):
        board = [['' for x in range(9)] for y in range(9)]
        
        regions = [
            {'row_start': 4, 'row_end': 7, 'col_start': 4, 'col_end': 7, 'region_id': 1},
            {'row_start': 1, 'row_end': 4, 'col_start': 4, 'col_end': 7, 'region_id': 2},
            {'row_start': 4, 'row_end': 7, 'col_start': 1, 'col_end': 4, 'region_id': 3},
            {'row_start': 4, 'row_end': 7, 'col_start': 7, 'col_end': 10, 'region_id': 4},
            {'row_start': 7, 'row_end': 10, 'col_start': 4, 'col_end': 7, 'region_id': 5}
        ]
        
        for region in regions:
            counter = 1
            for row in range(region['row_start'], region['row_end']):
                for col in range(region['col_start'], region['col_end']):
                    board[row - 1][col - 1] = f"{region['region_id']}:{counter}"
                    counter += 1
        
        center = Point(x=len(board[0]) // 2, y=len(board) // 2)
        
        self.map = board
        self.location = center
        return self.map, self.location
    
    def init_npc_dict(self):
        for key in self.places_dict.keys():
            self.npcs_dict[key] = []

    def get_place_key(self) -> str:
        return self.map[self.location.x][self.location.y]

    def get_current_place(self) -> tuple[int, Town, str, Place]:
        place_key = self.get_place_key()
        place = self.places_dict[place_key]
        town_index = int(place_key.split(':')[0]) - 1
        town = self.towns[town_index]
        return town_index, town, place_key, place
    
    def get_npcs(self) -> List[NPC]:
        return self.npcs_dict[self.get_place_key()]
        
    def get_npc(self, idx: int) -> NPC:
        place_key = self.get_place_key()
        if idx <= len(self.npcs_dict[place_key]):
            return self.npcs_dict[place_key][idx - 1]
        else:
            return None

    def get_place_image(self) -> GenImage:
        return self.places_images_dict[self.get_place_key()]

    def set_place_image(self, image: bytes):
        self.places_images_dict[self.get_place_key()].data = image

    def can_move(self, location: Point) -> bool:
        if location.x < 0 or location.y < 0:
            return False
        if location.x >= len(self.map) or location.y >= len(self.map):
            return False
        return self.map[location.x][location.y] != ''
    
    def set_creating(self):
        self.status = WorldStatus.Creating

    def set_started(self):
        self.status = WorldStatus.Started

    def not_started(self) -> bool:
        return self.status == WorldStatus.NotStarted

    def creating(self) -> bool:
        return self.status == WorldStatus.Creating

    def started(self) -> bool:
        return self.status == WorldStatus.Started


__all__ = ['World', 'Town', 'Place', 'Point', 'Move']
