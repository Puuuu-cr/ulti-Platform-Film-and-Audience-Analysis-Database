-- =====================================================================
-- Scenario - Veteran's Hidden Gems
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
