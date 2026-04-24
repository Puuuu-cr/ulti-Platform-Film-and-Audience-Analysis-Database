-- =========================================================
-- 1. Independent Dimension Table: Movie Genres
-- =========================================================
CREATE TABLE IF NOT EXISTS genres (
    genre_id INTEGER PRIMARY KEY,
    genre_name VARCHAR(50) NOT NULL
);

-- =========================================================
-- 2. Core Entity Table: Movies
-- =========================================================
CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    original_title VARCHAR(255),
    overview TEXT,
    release_date DATE,
    vote_average DECIMAL(3, 1),
    vote_count INTEGER,
    popularity DECIMAL(12, 3),
    original_language VARCHAR(10),
    poster_url TEXT,
    backdrop_url TEXT,
    is_adult BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 3. Many-to-Many Relationship Table: Movie-Genres
-- =========================================================
CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id INTEGER REFERENCES movies(movie_id) ON DELETE CASCADE,
    genre_id INTEGER REFERENCES genres(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (movie_id, genre_id)
);

-- =========================================================
-- 4. Independent Entity Table: Users
-- =========================================================
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 5. Interaction Table: User Reviews
-- =========================================================
CREATE TABLE IF NOT EXISTS user_reviews (
    review_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    rating DECIMAL(3,1) CHECK (rating >= 0 AND rating <= 10),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, movie_id)
);

-- =========================================================
-- 6. Statistical Table (Vertical Partitioning): Local Movie Stats
-- =========================================================
CREATE TABLE IF NOT EXISTS movie_stats (
    movie_id INTEGER PRIMARY KEY REFERENCES movies(movie_id) ON DELETE CASCADE,
    total_reviews INTEGER DEFAULT 0,
    average_rating DECIMAL(3,1) DEFAULT 0.0
);

-- =========================================================
-- 7. User Watchlists
-- =========================================================
CREATE TABLE IF NOT EXISTS watchlists (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Composite Primary Key: Prevents a user from adding the same movie to their watchlist multiple times
    PRIMARY KEY (user_id, movie_id) 
);

-- =========================================================
-- 8. Comprehensive Movie Details View
-- =========================================================
CREATE OR REPLACE VIEW v_movie_full_details AS
WITH GenreAgg AS (
    -- First, aggregate the Genres by movie_id and concatenate them into a single comma-separated string
    SELECT 
        mg.movie_id,
        STRING_AGG(g.genre_name, ', ') AS all_genres
    FROM
        movie_genres mg
    JOIN 
        genres g ON mg.genre_id = g.genre_id
    GROUP BY 
        mg.movie_id
)
SELECT 
    -- 1. Select all original fields from the movies table (includes TMDB ratings, backdrop URLs, languages, etc.)
    m.*, 
    
    -- 2. Retrieve local system statistical data (default to 0.0 or 0 if no local reviews exist)
    COALESCE(ms.average_rating, 0.0) AS local_avg_rating,
    COALESCE(ms.total_reviews, 0) AS local_total_reviews,
    
    -- 3. Retrieve the previously aggregated genre string from the CTE
    ga.all_genres
FROM 
    movies m
LEFT JOIN 
    movie_stats ms ON m.movie_id = ms.movie_id
LEFT JOIN 
    GenreAgg ga ON m.movie_id = ga.movie_id;

-- =========================================================
-- 9. Masked User Info View
-- Displaying review author info while protecting passwords and emails
-- =========================================================
CREATE OR REPLACE VIEW v_public_user_info AS
SELECT 
    user_id, 
    username, 
    created_at 
FROM 
    users;
