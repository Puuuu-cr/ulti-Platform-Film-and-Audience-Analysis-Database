CREATE INDEX idx_genres_name ON genres(genre_name);
CREATE INDEX idx_movies_release_date ON movies(release_date);
CREATE INDEX idx_movie_stats_avg_rating ON movie_stats(average_rating);

--- Here we test three kinds of index
