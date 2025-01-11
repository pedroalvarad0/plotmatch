import os
from openai import OpenAI
from dotenv import load_dotenv
from db import get_db_connection

load_dotenv()

def get_query_embedding(query_text):
    """Create embedding for the search query"""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=query_text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error creating query embedding: {str(e)}")
        return None

def find_similar_movies(query_embedding, limit=5):
    """Find movies with similar embeddings using cosine similarity"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Query to get the most similar movie IDs using pgvector
        query = """
        SELECT 
            movie_id,
            embedding,
            embedding <=> vector(%s) as distance
        FROM movie_embeddings
        ORDER BY distance ASC
        LIMIT %s;
        """
        
        # Convert Python list to PostgreSQL array string
        vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
        cur.execute(query, (vector_str, limit))
        results = cur.fetchall()
        
        # Get details for the found movies
        movie_ids = [int(result[0]) for result in results]  # Convert to integers
        similarities = [1 - result[2] for result in results]
        
        if movie_ids:
            movies_query = """
            SELECT id, title, genres, overview, release_year, movie_cast, directors, poster
            FROM movies
            WHERE id = ANY(%s::int[])  -- Specify that it's an array of integers
            """
            
            cur.execute(movies_query, (movie_ids,))
            movies = cur.fetchall()
            
            # Combine results with similarities
            movie_results = []
            for movie, similarity in zip(movies, similarities):
                movie_dict = {
                    'id': movie[0],
                    'title': movie[1],
                    'genres': movie[2],
                    'overview': movie[3],
                    'release_year': movie[4],
                    'cast': movie[5],
                    'directors': movie[6],
                    'poster': "https://image.tmdb.org/t/p/original" + movie[7],
                    'similarity': similarity,
                }
                movie_results.append(movie_dict)
                
            return movie_results
            
        return []
        
    finally:
        cur.close()
        conn.close()

def search_movies(query_text, limit=5):
    """Main function to search movies"""
    # Get query embedding
    query_embedding = get_query_embedding(query_text)
    if not query_embedding:
        return []
    
    # Find similar movies
    similar_movies = find_similar_movies(query_embedding, limit)
    
    return similar_movies

if __name__ == "__main__":
    # Example usage
    query = "Movies about a guy that discover some kind of drug that unlock full brain potential"
    results = search_movies(query, limit=5)

    #print(get_query_embedding(query))
    
    print(f"\nSearch results for: '{query}'\n")
    for movie in results:
        print(f"ID: {movie['id']}")
        print(f"Title: {movie['title']} ({movie['release_year']})")
        print(f"Similarity: {movie['similarity']:.4f}")
        print(f"Genres: {movie['genres']}")
        print(f"Directors: {movie['directors']}")
        print(f"Cast: {movie['cast']}")
        print(f"Overview: {movie['overview']}\n")
