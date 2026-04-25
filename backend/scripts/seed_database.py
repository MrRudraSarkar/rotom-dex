# requests - lets us make HTTP calls to the PokeAPI
import requests

# time - built into python, we use it to add small delays between API calls
# this prevents us from hammering the PokeAPI too fast and getting rate limited
import time

import sys
import os

# add backend/ to path so that we can import database.py and models.py
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database import SessionLocal, engine, Base
import models
from models import Pokemon, Type, Stats, Moves, Ability, Item, TypeEffectiveness

# ---- Helper  function ----

def fetch(url):
    # makes a GET request to  the given URL and returns the parsed JSON as a dict
    # if anything goes wrong (network error, bad status, etc), we catch it here
    # returning None instead of crashing means callers can check if "not" data
    try:
        response = requests.get(url)
        
        # raise_for_status() throws an exception if the was 4xx or 5xx(HTTP errors exclusivey)
        # without this, requests considers any response a "success", even error pages
        response.raise_for_status()

        return response.json()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None
    
def get_english(entries, text_field):
    # PokeAPI returns text content in multiple languages as a list of dicts
    # each dict looks like: {"language": {"name": "en", "url": "..."}, "flavor_text": "..."}
    # we loop through and find the first English one
    
    for entry in entries:
        # .get("language", {}) - if "language" key is missing, return empty dict
        # chaining .get("name") on that - if "name" is missing, return None
        # this way we never get a KeyError even if the structure is unexpected
        if entry.get("language", {}).get("name") == "en":
            # .replace() cleans up newlines and forms feeds that PokeAPI includes
            # in flavor text - these would look ugly when displayed
            return entry.get(text_field, "").replace("\n", " ").replace("\f", " ")
        
    return ""

# ---- Seeding functions ----
def seed_types(db):
    print("Seeding types...")

    data = fetch("https://pokeapi.co/api/v2/type?limit=18")
    if not data:
        return
    
    # .get("results", []) - if "results" key is missing. use empty list as fallback
    # this means the for loop simply doesnt run instead of crashing
    # we use this pattern everywhere we loop over the API response
    for entry in data.get("results", []):
        name = entry.get("name")

        # if name is None or an empty string, skip this entry - nothing useful to store
        if not name:
            continue

        if name in ("shadow", "unknown"):
            continue

        existing = db.query(Type).filter_by(name=name).first()
        if not existing:
            db.add(Type(name=name))

    db.commit()
    print("Types seeded.")

def seed_type_effectiveness(db):
    data = fetch("https://pokeapi.co/api/v2/type?limit=18")
    if not data:
        return
    
    for entry in data.get("results", []):
        type_name = entry.get("name")
        if type_name in ("shadow", "unknown"):
            continue

        type_data = fetch(entry.get("url"))
        if not type_data:
            continue

        attacking_type = db.query(Type).filter_by(name=type_name).first()
        if not attacking_type:
            continue

        damage_relations = type_data.get("damage_relations", {})

        # double_damage_to is a list of type dicts this type hits for 2x damage
        for t in damage_relations.get("double_damage_to", []):
            defending_type = db.query(Type).filter_by(name=t.get("name")).first()
            if defending_type:
                # db.merge() - inserts the row if it doesn't exist, updates it if it does
                # safer than db.add() for rows with composite primary keys
                db.merge(
                    TypeEffectiveness(
                        attacking_type_id=attacking_type.id,
                        defending_type_id=defending_type.id,
                        multiplier = 2.0
                    )
                )
        
        for t in damage_relations.get("half_damage_to", []):
            defending_type = db.query(Type).filter_by(name=t.get("name")).first()
            if defending_type:
                db.merge(
                    TypeEffectiveness(
                        attacking_type_id=attacking_type.id,
                        defending_type_id=defending_type.id,
                        multiplier=0.5 
                    )
                )
        
        for t in damage_relations.get("no_damage_to", []):
            defending_type=db.query(Type).filter_by(name=t.get("name")).first()
            if not defending_type:
                db.merge(
                    TypeEffectiveness(
                        attacking_type_id=attacking_type.id,
                        defending_type_id=defending_type.id,
                        multiplier=0.0
                    )
                )
        
        time.sleep(0.2)
    
    db.commit()
    print("Type effectiveness seeded")

def seed_move(db, move_url):
    data=fetch(move_url)
    if not data:
        return
    
    name = data.get("name")
    if not name:
        return
    
    if db.query(Moves).filter_by(name=name).first():
        return
    
    type_name=data.get("type", {}).get("name")
    type_obj=db.query(Type).filter_by(name=type_name).first() if type_name else None

    flavor_entries = data.get("flavor_text_entries", [])
    description = get_english(flavor_entries, "flavor_text")

    move = Moves(
        name=name,
        type_id=type_obj.id if type_obj else None,
        power=data.get("power"),
        accuracy=data.get("accuracy"),
        pp=data.get("pp"),
        damage_class=data.get("damage_class",{}).get("name"),
        description=description
    )
    db.add(move)

def seed_ability(db, ability_url):
    data = fetch(ability_url)
    if not data:
        return
    
    name = data.get("name")
    if not name:
        return

    if db.query(Ability).filter_by(name=name).first():
        return
    
    # effect_entries is a list of dicts with languages and effect description
    # we prefer short_effective here -  it is concise and fits well with the UI
    effect_entries = data.get("effect_entries", [])
    description = ""
    for entry in effect_entries:
        if entry.get("language", {}).get("name") == "en":
            description = entry.get("short_effect", "")
            break

    db.add(Ability(name=name, description=description))

def seed_pokemon(db, pokedex_number):
    data = fetch(f"https://pokeapi.co/api/v2/pokemon/{pokedex_number}")
    if not data:
        return
    
    name = data.get("name")
    if not name:
        return
    
    if db.query(Pokemon).filter_by(name=name).first():
        return

    # the main pokemon endpoint does not have flavor text
    # we need to fetch species endpoint separately for the description
    species_url = data.get("species", {}).get("url")
    description = ""
    if species_url:
        species_data = fetch(species_url)
        if species_data:
            flavor_entries = species_data.get("flavor_text_entries", [])
            description = get_english(flavor_entries, "flavor_text")

    # sprites is a dict of different image urls for this Pokemon
    # we want front_default - the standard front facing sprite
    sprite_url = data.get("sprites", {}).get("front_default", "")

    pokemon = Pokemon(
        name=name,
        pokedex_number=pokedex_number,
        height=data.get("height"),
        weight=data.get("weight"),
        base_experience=data.get("base_experience"),
        sprite_url=sprite_url,
        description=description
    )
    db.add(pokemon)

    # db.flush() sends the INSERT to the db without committing the transaction
    # this is necessary because we need pokemon.id to exist before we can
    # create the Stats row and append relationship below
    # without db.flush() pokemon.id would still be None at this point
    db.flush()


    # ---- Types ----
    for type_entry in data.get("types", []):
        type_name = type_entry.get("type", {}).get("name")
        type_obj = db.query(Type).filter_by(name=type_name).first()
        if type_obj:
            # .apppend() on a relationship list creates the junction table entry
            # SQLAlchemy handles the pokemon_types insert automaticcally
            pokemon.types.append(type_obj)

    # ---- Stats ----
    # PokeAPI returns stats as a list of dicts like:
    # [{"base_stat": 45, "stat":{"name": "hp"}},...]
    # we convert this into a flat dict for easy lookup: {"hp": 45,...}
    stats_list = data.get("stats", [])
    stats_dict = {}
    for s in stats_list:
        stat_name = s.get("stat", {}).get("name")
        base_stat = s.get("base_stat")
        if stat_name:
            stats_dict[stat_name] = base_stat

    db.add(
        Stats(
            pokemon_id=pokemon.id,
            hp=stats_dict.get("hp"),
            attack=stats_dict.get("attack"),
            defense=stats_dict.get("defense"),
            # PokeAPI uses hyphens in these names not underscores
            special_attack=stats_dict.get("special-attack"),
            special_defense=stats_dict.get("special-defense"),
            speed=stats_dict.get("speed")
        )
    )

    # ---- Moves ----
    for move_entry in data.get("moves", []):
        move_url = move_entry.get("move", {}).get("url")
        if move_url:
            seed_move(db, move_url)
            move_name = move_entry.get("move", {}).get("name")
            move_obj = db.query(Moves).filter_by(name=move_name).first()
            if move_obj:
                pokemon.moves.append(move_obj)

    # ---- Abilities ----
    for ability_entry in data.get("abilities", []):
        ability_url = ability_entry.get("ability", {}).get("url")
        if ability_url:
            seed_ability(db, ability_url)
            ability_name = ability_entry.get("ability", {}).get("name")
            ability_obj = db.query(Ability).filter_by(name=ability_name).first()
            if ability_obj:
                pokemon.abilities.append(ability_obj)
    
    db.commit()
    print(f"    Seeded{name} (#{pokedex_number})")

def seed_items(db):
    print("Seeding items....")

    data = fetch("https://pokeapi.co/api/v2/item?limit=100")
    if not data:
        return
    
    for entry in data.get("results", []):
        item_url = entry.get("url")
        if not item_url:
            continue

        item_data = fetch(item_url)
        if not item_data:
            continue

        name = item_data.get("name")
        if not name:
            continue

        if db.query(Item).filter_by(name=name).first():
            continue

        category = item_data.get("category", {}).get("name", "")

        # items use "text" as the field name, not "flavor_text" like pokemon
        flavor_entries = item_data.get("flavor_text_entries", [])
        description = get_english(flavor_entries, "text")

        db.add(
            Item(
                name=name,
                category=category,
                cost=item_data.get("cost"),
                description=description
            )
        )

        time.sleep(0.1)
    db.commit()
    print("Items seeded")

# ---- Main ----
def main():
    # create all tables if they don't already exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        print("Starting database seed.....")

        seed_types(db)
        seed_type_effectiveness(db)

        print("Seeding Pokemon.....")
        for i in range(1,152):
            seed_pokemon(db, i)
            # small pause between each pokemon to avoid getting rate limited
            time.sleep(0.3)

        seed_items(db)

        print("Database seeded successfully...")
    
    except Exception as e:
        # rollback undoes all uncommitted changes if something goes wrong:
        # without this, a partial failure could leave the database in a broken state
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    main()