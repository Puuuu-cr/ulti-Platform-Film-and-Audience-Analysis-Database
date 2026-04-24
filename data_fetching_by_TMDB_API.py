import requests
import psycopg2
import time

# ==========================================
# 1. Core Configuration Area
# ==========================================

# Fill in your config
TMDB_API_KEY = "YOUR TMDB API KEY"
DB_CONFIG = {
    "host": "localhost",
    "database": "YOUR DATABASE",
    "user": "",
    "password": "",
    "port": ""
}
BASE_IMG_URL = "https://image.tmdb.org/t/p/w500"

# ==========================================
# 2. Sync Movie Genres
# ==========================================
def sync_genres(cur):
    print("Syncing TMDB genre dictionary...")
    url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={TMDB_API_KEY}&language=en-US"
    response = requests.get(url)
    
    if response.status_code == 200:
        genres = response.json().get("genres", [])
        for g in genres:
            cur.execute("""
                INSERT INTO genres (genre_id, genre_name) 
                VALUES (%s, %s) 
                ON CONFLICT (genre_id) DO NOTHING;
            """, (g['id'], g['name']))
        print(f"Successfully synced {len(genres)} movie genres.\n")

# ==========================================
# 3. Fetch and Sync Movies
# ==========================================
def fetch_and_save_movies(cur, pages=10):
    print(f"Starting to fetch the top {pages} pages of popular movies...")
    
    for page in range(1, pages + 1):
        url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=en-US&page={page}"
        response = requests.get(url)
        
        if response.status_code == 200:
            movies = response.json().get("results", [])
            
            for m in movies:
                # 3.1 INSERT statement matching your table structure
                movie_sql = """
                    INSERT INTO movies (
                        movie_id, title, original_title, overview, release_date, 
                        vote_average, vote_count, popularity, original_language, 
                        poster_url, backdrop_url, is_adult
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (movie_id) DO UPDATE SET
                        vote_average = EXCLUDED.vote_average,
                        vote_count = EXCLUDED.vote_count,
                        popularity = EXCLUDED.popularity,
                        overview = EXCLUDED.overview,
                        poster_url = EXCLUDED.poster_url,
                        backdrop_url = EXCLUDED.backdrop_url;
                """
                movie_vals = (
                    m.get('id'), 
                    m.get('title'), 
                    m.get('original_title'), 
                    m.get('overview'),
                    m.get('release_date') if m.get('release_date') else None,
                    m.get('vote_average'), 
                    m.get('vote_count'), 
                    m.get('popularity'), 
                    m.get('original_language'),
                    f"{BASE_IMG_URL}{m.get('poster_path')}" if m.get('poster_path') else None,
                    f"{BASE_IMG_URL}{m.get('backdrop_path')}" if m.get('backdrop_path') else None,
                    m.get('adult', False),
                )
                cur.execute(movie_sql, movie_vals)

                # 3.2 Insert into movie-genre mapping table
                genre_ids = m.get('genre_ids', [])
                for g_id in genre_ids:
                    cur.execute("""
                        INSERT INTO movie_genres (movie_id, genre_id) 
                        VALUES (%s, %s) 
                        ON CONFLICT DO NOTHING;
                    """, (m['id'], g_id))
            
            print(f"✓ Page {page} (20 movies) fetched and saved successfully.")
        else:
            print(f"✗ Failed to fetch page {page}, status code: {response.status_code}")
            
        time.sleep(0.5)

# ==========================================
# 4. Main Program Execution
# ==========================================
if __name__ == "__main__":
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        sync_genres(cur)
        # You can adjust the number of pages to fetch here
        fetch_and_save_movies(cur, pages=500) 
        
        conn.commit()
        print("\n🎉 Data synchronization complete! Database is aligned with your design.")
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"\n❌ An error occurred: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
