from fastapi import FastAPI

# CORSMiddleware — allows our frontend (running on a different port)
# to make requests to our backend
# without CORS, browsers block requests between different origins
# e.g. frontend on port 5173 talking to backend on port 8000
from fastapi.middleware.cors import CORSMiddleware

from routers import pokemon, moves, items

app = FastAPI(
    title="Rotomdex API",
    description="The Pokedex API powering ROTOM"
)

# add CORS middleware to allow the frontend to talk to the backend
# allow_origins=["*"] means any origin is allowed — fine for development
# in production we would restrict this to our actual frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],     # allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"]     # allow all headers
)

# register our routers with the app
# prefix= adds a base path to all routes in that router
# e.g. prefix="/pokemon" means all routes in pokemon.py start with /pokemon
# tags= groups endpoints together in the /docs UI

app.include_router(pokemon.router, prefix="/pokemon", tags=["Pokemon"])
# app.include_router(moves.route, prefix="/moves", tags=["Moves"])
# app.include_router(items.router, prefix="/items", tags=["Items"])

# a simple root endpoint to confirm the API is running
# this is the first thing we'll test after starting the server

@app.get("/")
def root():
    return {"message": "Rotom dex API is running"}