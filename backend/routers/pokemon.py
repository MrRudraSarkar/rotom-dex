# APIRouter — creates a mini FastAPI app that we register in main.py
# think of it as a group of related endpoints that can be plugged in
# Depends — FastAPI's dependency injection system
# we use it to inject the database session into each route function
# FastAPI calls get_db() for us and passes the result as the db parameter
from fastapi import APIRouter, HTTPException, Depends, status

from sqlalchemy.orm import Session

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database import get_db
from models import Pokemon
from schemas import PokemonSummarySchema, PokemonDetailSchema

from typing import List

router = APIRouter()

@router.get("/", response_model=List[PokemonSummarySchema])
def get_allPokemon(db:Session = Depends(get_db))->List[PokemonSummarySchema]:
    # Depends(get_db) calls our get_db() function and injects the session
    # db: Session is the database session we use to query PostgreSQL
    pokemon_list = db.query(Pokemon).all()
    return pokemon_list

@router.get("{identifier}", response_model=PokemonDetailSchema)
def get_pokemon(id: str, db: Session = Depends(get_db))->PokemonDetailSchema:
    if id.isdigit():
        pokemon = db.query(Pokemon).filter(
            Pokemon.pokedex_number == int(id)
        ).first()
    else:
        pokemon = db.query(Pokemon).filter(
            Pokemon.name == id.lower()
        ).first()

    if not pokemon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pokemon not found")

    return pokemon