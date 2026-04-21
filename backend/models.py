# Column - defines a column in  a table
# Integer - whole number column type
# String - short text column type (varchar)
# Float - decimal number column type
# ForeignKey - links the table to a primary key in another table
# Text - long text column type, no length limit (for descriptions, lore)
# Table - used to create plain junction table no class needed
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Table

# relationship - defines how two models relate to each other in python
# let's us do things like pokemon.types instead of having to write a join query
from sqlalchemy.orm import relationship

# our Base class from database.py - all models must inherit from this
from database import Base

# ----- Junction Tables (many-to-many relationships) -----
# A pokemon can have multiple types, and a type can belong to many pokemon
# we can't store that in a single column - we need a middle table
# Table() created a simple table without a full Python class 
# Base.metadata tells SQLAlchemy to include this table when creating the schema

pokemon_types = Table(
    "pokemon_types", Base.metadata,
    Column("pokemon_id", Integer, ForeignKey("pokemon.id")),
    Column("type_id", Integer, ForeignKey("types.id"))
)

# same pattern - a pokemon can learn many moves, a move can be learned by multiple pokemon
pokemon_moves = Table(
    "pokemon_moves", Base.metadata,
    Column("pokemon_id", Integer, ForeignKey("pokemon.id")),
    Column("move_id", Integer, ForeignKey("moves.id"))
)

# same pattern - a Pokemon can have many abilities, an ability can belong to many pokemon
pokemon_abilities = Table(
    "pokemon_abilities", Base.metadata,
    Column("pokemon_id", Integer, ForeignKey("pokemon.id")),
    Column("ability_id", Integer, ForeignKey("abilities.id"))
)

# ---- Main tables ----

class Pokemon(Base):
    # __tablename__ tells SQLAlchemy what to name this table in PostgreSQL
    __tablename__ = "pokemon"

    # primary_key=True - unique identifier for each row, auto increments 
    id = Column(Integer, primary_key=True)

    # unique=True - no two pokemon can share a name
    # nullable=False - this field is required, cannot be empty
    name = Column(String, unique=True, nullable=False)

    pokedex_number = Column(Integer, unique=True)
    height = Column(Float) # stored in decimeters as returned by pokeAPI
    weight = Column(Float) # stored in hectograms as returned by pokeAPI
    base_experience = Column(Integer)
    sprite_url = Column(String)

    # Text instead of string because descriptions can be long
    # this field also gets embedded into ChromaDB for RAG queries
    description = Column(String)

    # relationship() lets us access related data as python attributes
    # secondary=... points to the junction table that connects the two models
    # back_populates=... creates the reverse link on the other model
    types = relationship("Type", secondary=pokemon_types, back_populates="pokemon")
    moves = relationship("Move", secondary=pokemon_types, back_populates="pokemon")
    abilities = relationship("Ability", secondary=pokemon_abilities, back_populates="pokemon")

    # uselist=False - tells SQLAlchemy this is one=to-one, not many-to-many
    # a pokemon has exactly one stat row, not a list of stats
    stats = relationship("Stats", back_populates="pokemon", uselist=False)

class Type(Base):
    __tablename__ = "types"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    
    # reverse side of the pokemon_types relationship
    pokemon = relationship("Pokemon", secondary=pokemon_types, back_populates="types")

class Stats(Base):
    __tablename__="stats"

    id = Column(Integer, primary_key=True)

    # ForeignKey links this row to a specific Pokemon
    # "pokemon.id" refers to the id column in the pokemon table
    pokemon_id = Column(Integer, ForeignKey("pokemon.id"))

    hp =  Column(Integer)
    attack = Column(Integer)
    defense = Column(Integer)
    special_attack = Column(Integer)
    special_defense = Column(Integer)
    speed = Column(Integer)
    
    # reverse side of the stats relationship on pokemon
    pokemon = relationship("Pokemon", back_populates="stats")

class Moves(Base):
    __tablename__="moves"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    type_id = Column(Integer, ForeignKey("types.id"))
    
    # nullable=True - some moves have no power (e.g. status moves like Thunder Wave)
    power = Column(Integer, nullable=True)
    accuracy = Column(Integer, nullable=True)
    pp = Column(Integer)

    # physical -> uses attack/defense stats to calculate damage
    # special -> uses special attack/special defense stats to calculate damage
    # status -> deals no damage, applies status effects
    damange_class = Column(String)

    description = Column(Text)

    pokemon = relationship("Pokemon", back_populates="moves")

class Ability(Base):
    __tablename__="abilities"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(Text)

    pokemon = relationship("Pokemon", back_populates="abilities")

class Item(Base):
    __tablename__="items"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    category = Column(String) # pokeball, medicine, held items, berries etc...
    description = Column(Text)

class TypeEffectiveness(Base):
    __tablename__ = "type_effectiveness"

    # composite primary key - the combination of both columns is unique
    # e.g. fire attacking grass is one unique row
    attacking_type_id = Column(Integer, ForeignKey("types.id"), primary_key=True)
    defending_type_id = Column(Integer, ForeignKey("types.id"), primary_key=True)

    # 0    = immune(normal vs ghost)
    # 0.5  = not very effective
    # 1    = normal damage
    # 2    = super effective
    multiplier = Column(Float)