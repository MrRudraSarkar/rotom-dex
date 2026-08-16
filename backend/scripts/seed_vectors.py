# this script reads all pokemon descriptions from PostgreSQL
# converts them to vectors using nomic-embed-text
# and stores those vectors in ChromaDB
# think of it as building the "search index" for Rotom's lore knowledge

import sys
import os

# add backend/ to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database import SessionLocal
from models import Pokemon

# import our ChromaDB functions from rag.py
from agent.rag import add_pokemon_to_chromadb

def main():
    print("Starting ChromaDB vector seeding...")

    # open a database session to read from PostgreSQL
    db = SessionLocal()

    try:
        # fetch all 151 pokemon from PostgreSQL
        # we only need their id, name and description for embedding
        all_pokemon = db.query(Pokemon).all()

        print(f"Found {len(all_pokemon)} pokemon to embed...")

        for pokemon in all_pokemon:
            # add_pokemon_to_chromadb handles the embedding and storage
            # it also skips duplicates so this script is safe to rerun
            add_pokemon_to_chromadb(
                pokemon_id=pokemon.pokedex_number,
                name=pokemon.name,
                description=pokemon.description
            )
            print(f" Embedded {pokemon.name}")

        print(f"\nChromaDB seeding completed")
        print(f"Total vectors in collections: {len(all_pokemon)}")

    except Exception as e:
        print(f"Seeding failed: {e}")
        raise

    finally:
        # always close the database session when done
        db.close()

if __name__ =="__main__":
    main()