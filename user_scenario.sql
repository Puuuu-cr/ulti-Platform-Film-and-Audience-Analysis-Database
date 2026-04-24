-- =====================================================================
-- Scenario 2: Decade Genre Champions (Based on TMDB Global Ratings)
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


-- =====================================================================
-- Scenario 3: Hidden Gems from Veteran Reviewers
-- =====================================================================

WITH VeteranUsers AS (
    -- Step 1: Identify "Veterans" (users who have reviewed > 100 movies)
    SELECT user_id
    FROM user_reviews
    GROUP BY user_id
    HAVING COUNT(movie_id) >= 100
),
VeteranRatings AS (
    -- Step 2: Calculate the average rating given ONLY by these Veteran users
    SELECT 
        r.movie_id, 
        AVG(r.rating) AS veteran_avg_rating
    FROM user_reviews r
    JOIN VeteranUsers vu ON r.user_id = vu.user_id
    GROUP BY r.movie_id
)
-- Step 3: Combine Veteran ratings with overall public stats to find the "Hidden Gems"
SELECT 
    m.title, 
    vr.veteran_avg_rating, 
    ms.total_reviews AS public_total_reviews
FROM VeteranRatings vr
JOIN movies m ON vr.movie_id = m.movie_id
JOIN movie_stats ms ON vr.movie_id = ms.movie_id
WHERE ms.total_reviews < 50      -- Condition 1: "Hidden" (Low public attention)
  AND vr.veteran_avg_rating >= 9 -- Condition 2: "Gem" (Highly praised by veterans)
ORDER BY vr.veteran_avg_rating DESC;


-- =====================================================================
-- Scenario 4: Most Polarizing/Controversial Movies
-- =====================================================================
-- Note: STDDEV is supported in PostgreSQL, MySQL, and Oracle. 
-- It calculates how spread out the numbers are. A high Standard Deviation 
-- means lots of 1-star and 10-star ratings (polarizing).

SELECT 
    m.title,
    ms.average_rating,
    ms.total_reviews,
    -- Calculate the Standard Deviation of ratings for this movie
    ROUND(STDDEV(r.rating), 3) AS rating_spread
FROM user_reviews r
JOIN movies m ON r.movie_id = m.movie_id
JOIN movie_stats ms ON m.movie_id = ms.movie_id
GROUP BY 
    m.movie_id, m.title, ms.average_rating, ms.total_reviews
-- Ensure statistical significance (e.g., standard deviation on 2 reviews is meaningless)
HAVING COUNT(r.rating) >= 30 
ORDER BY rating_spread DESC
LIMIT 10;
