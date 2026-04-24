-- =========================================================
-- Trigger to update local rating
-- =========================================================
CREATE OR REPLACE FUNCTION update_local_movie_stats()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO movie_stats (movie_id, total_reviews, average_rating)
    VALUES (NEW.movie_id, 1, NEW.rating)
    ON CONFLICT (movie_id) DO UPDATE SET
        total_reviews = movie_stats.total_reviews + 1,
        average_rating = (
            SELECT ROUND(AVG(rating), 1) 
            FROM user_reviews 
            WHERE movie_id = NEW.movie_id
        );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_stats ON user_reviews;
CREATE TRIGGER trigger_update_stats
AFTER INSERT ON user_reviews
FOR EACH ROW
EXECUTE FUNCTION update_local_movie_stats();
