from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from search import search_movies

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class Movie(BaseModel):
    id: int
    title: str
    genres: str
    overview: str
    release_year: int
    cast: str
    directors: str
    poster: str
    similarity: float

@app.get("/search", response_model=List[Movie])
async def search(query: str, limit: int = 5):
    """
    Search for similar movies based on query text.
    
    Args:
        query: Search text
        limit: Maximum number of results to return (default: 5)
    
    Returns:
        List of similar movies
    """
    results = search_movies(query, limit)
    return results
