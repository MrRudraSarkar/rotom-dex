from pydantic import BaseModel, Field
from typing import Optional, List

# ----- What are schemas? -----
# schemas are like contracts — they define exactly what data looks like
# when it comes INTO our API (request) or goes OUT of our API (response)
# SQLAlchemy models define how data is stored in the database
# Pydantic schemas define how data is shown to the outside world
# they are separate on purpose — you might store more than you want to expose

class TypeSchema(BaseModel):
    id: int
    name: str

    # model_config tells Pydantic how to handle the data source
    # from_attributes=True means Pydantic can read data directly from
    # SQLAlchemy model instances (which use attributes, not dicts)
    # without this, Pydantic wouldn't know how to read our database rows
    model_config = {"from_attributes": True}

class StatsSchema(BaseModel):
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int

    model_config = {"from_attributes": True}

class AbilitySchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}

class MoveSchema(BaseModel):
    id: int
    name: str
    # Optional[str] means this field can be a string or None
    # we use None as the default so missing values don't cause errors
    damage_class: Optional[str] = None
    power: Optional[int] = None
    accuracy: Optional[int] = None
    pp: Optional[int] = None
    description: Optional[str] = None

    model_config = {"from_attributes": True}

class PokemonSummarySchema(BaseModel):
    # summary schema — used when listing all pokemon
    # we don't want to return ALL data for 151 pokemon at once
    # just enough to display a list — name, number, sprite, types
    id: int
    name: str
    pokedex_number: int
    sprite_url: Optional[str] = None
    types: List[TypeSchema] = []

    model_config = {"from_attributes": True}

class PokemonDetailSchema(BaseModel):
    # detail schema — used when fetching a single pokemon
    # returns everything including stats, moves, abilities
    id:  int
    name: str
    pokedex_number: int
    height: Optional[int] = None
    weight: Optional[int] = None
    base_experience: Optional[int] = None
    sprite_url: Optional[str] = None
    description: Optional[str] = None
    types: List[TypeSchema] = []
    stats: Optional[StatsSchema] = None
    moves: List[MoveSchema] = []
    abilities: List[AbilitySchema] = []

    model_config = {"from_attributes": True}

class ItemSchema(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    cost: Optional[int] = None
    description: Optional[str] = None

    model_config = {"from_attribute": True}

# ------ Chat schemas ------
# these define what goes into and comes out of the Rotom chat endpoint

class ChatRequest(BaseModel):
    # the message the user sends to Rotom
    message: str

class ChatResponse(BaseModel):
    response: str