# chromadb - our local vector database
# this is where we store and search pokemon descriptions as vectors
import chromadb

# OllamaEmbeddings - connects LangChain to our local Ollama embedding model
# this is what converts text into vectors using nomic-embed-text
from langchain_ollama import OllamaEmbeddings

# os and dotenv - loading env variables
import os
from dotenv import load_dotenv

load_dotenv()

# ---- Setup ----

# Persistent Client tells chromadb to save vectors to disk
# this means our vectors survive netween restarts -  we don't re-embed every time
# the path is where ChromaDB will create it's storage files
# we store it at the project root level, outsidde backend/
chroma_client = chromadb.PersistentClient(path="../../chroma_db")

# a collection in chromadb is like a table in postgreSQL
# it groups related vectors together
# get_or_create_collection - creates it if it doesn't exist, opens it if it does
# this makes the code safe to run multiple times without duplicating data
collection = chroma_client.get_or_create_collection(name="pokemon_lore")

# initialize the embedding model
# this connects to our locally running Ollama instance
# nomic-embed-text is the model we will use - it converts text to vectors
# base_url points to where Ollama is running on our machine
embeddings = OllamaEmbeddings(
    model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
    base_url=os.getenv("OLLAMA_BASE_MODEL", "http://localhost:11434")
)


# ----- Core Functions -----
def embed_text(text):
    # convert a single piece of text into a vector using nomic-embed-text
    # embed-query is used for single texts - returns a list of floats
    # e.g. "Pikachu is an electric mouse" becomes [0.023, -0.412, 0.891,...]
    # the numbers capture the semantic meaning of the text
    return embeddings.embed_query(text)

def add_pokemon_to_chromadb(pokemon_id, name, description):
    # add a single pokemon's lore to chromadb
    # we only add it if it doesn't already exist - makes seeding safe to rerun

    # collection.get() checks if a document with this id already exists
    # ids in chromadb are strings, so we convert pokemon_id to string
    existing = collection.get(ids=[str(pokemon_id)])

    # existing["ids"] is a list - if it's empty, the pokemon isn't in the chromadb yet
    if existing["ids"]:
        return
    
    # skip pokemon with no description - nothing useful to embed
    if not description or description.strip() == "":
        print(f"    Skipping {name} - no description")
        return
    
    # convert the description text into a vector
    vector = embed_text(description)

    # add the vector to ChromaDB with three pieces of information:
    # embeddings -  the actual vector (list of numbers representing meaning)
    # documents  -  the original text, stored alongside the vector
    #               ChromaDB returns this text when we search, so Rotom can read it
    # metadata   -  extra info stored with each entry, useful for filtering later 
    #               e.g. we could later search "only grass type pokemon"
    # ids        -  unique identifier for this entry, we use pokedex number
    collection.add(
        embeddings=[vector],
        documents=[description],
        metadatas=[{"pokemon_id": pokemon_id, "name": name}],
        ids=[str(pokemon_id)]
    )

