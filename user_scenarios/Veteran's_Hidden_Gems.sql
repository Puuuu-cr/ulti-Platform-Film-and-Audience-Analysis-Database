-- =====================================================================
-- Scenario - Veteran's Hidden Gems
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
