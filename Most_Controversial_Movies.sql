-- =====================================================================
-- Scenario - Decade Genre Champions (Based on TMDB Global Ratings)
-- =====================================================================

WITH MovieDecades AS (
    -- Step 1: Extract the decade from release_date and gather TMDB base stats
    SELECT 
        m.movie_id,
        m.title,
        g.genre_name,
        -- PostgreSQL syntax: Extract Year, divide by 10, multiply by 10 (e.g., 1994 -> 1990)
        FLOOR(EXTRACT(YEAR FROM m.release_date) / 10) * 10 AS decade,
        m.vote_average AS tmdb_rating,
        m.vote_count AS tmdb_votes
    FROM movies m
    JOIN movie_genres mg ON m.movie_id = mg.movie_id
    JOIN genres g ON mg.genre_id = g.genre_id
    -- Ensure statistical significance: only consider globally well-known movies
    WHERE m.vote_count >= 1000 
      AND m.release_date IS NOT NULL
),
RankedChampions AS (
    -- Step 2: Apply Window Function to rank movies within each genre AND decade
    SELECT 
        title,
        genre_name,
        decade,
        tmdb_rating,
        tmdb_votes,
        ROW_NUMBER() OVER (
            PARTITION BY genre_name, decade 
            ORDER BY tmdb_rating DESC, tmdb_votes DESC
        ) as rank_in_category
    FROM MovieDecades
)
-- Step 3: Filter only the #1 movie (the Champion) for each category
SELECT 
    genre_name, 
    decade, 
    title AS champion_movie, 
    tmdb_rating,
    tmdb_votes
FROM RankedChampions
WHERE rank_in_category = 1
ORDER BY genre_name ASC, decade DESC
