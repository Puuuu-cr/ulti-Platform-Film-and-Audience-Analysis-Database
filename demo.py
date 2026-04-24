import streamlit as st
import psycopg2
from psycopg2 import sql
import hashlib

# ==========================================
# 1. Initialization and Database Connection
# ==========================================
st.set_page_config(page_title="My Movie Demo", page_icon="🎬", layout="wide")

@st.cache_resource
def init_connection():
    return psycopg2.connect(
        host="localhost", database="Movie_Project",
        user="oulin_yang", password="", port="5432"
    )

conn = init_connection()

# Initialize session states
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'viewing_movie' not in st.session_state:
    st.session_state.viewing_movie = None
if 'plaza_page' not in st.session_state:
    st.session_state.plaza_page = 1
if 'last_search' not in st.session_state:
    st.session_state.last_search = ""
if 'edit_review_mode' not in st.session_state:
    st.session_state.edit_review_mode = False

def clear_viewing_movie():
    st.session_state.viewing_movie = None
    st.session_state.edit_review_mode = False

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# 2. Database Operations
# ==========================================
def run_query(query, params=None, fetch=False):
    with conn.cursor() as cur:
        try:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            st.error(f"Database error: {e}")
            return False

# ==========================================
# 3. Page Components: Login System
# ==========================================
def login_section():
    st.sidebar.title("👤 User Center")
    if st.session_state.user_id is None:
        with st.sidebar.expander("Click to Login/Register", expanded=True):
            mode = st.radio("Mode", ["Login", "Register"])
            u_name = st.text_input("Username")
            u_pwd = st.text_input("Password", type="password") 
            
            if mode == "Register":
                u_email = st.text_input("Email")
                if st.button("Submit Registration"):
                    if u_name and u_pwd and u_email:
                        hashed_pwd = hash_password(u_pwd)
                        success = run_query("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", 
                                            (u_name, u_email, hashed_pwd))
                        if success:
                            st.success("Registration successful, please switch to Login")
                    else:
                        st.warning("Please fill in all fields.")
            else:
                if st.button("Login"):
                    if u_name and u_pwd:
                        hashed_pwd = hash_password(u_pwd)
                        res = run_query("SELECT user_id FROM users WHERE username = %s AND password_hash = %s", 
                                        (u_name, hashed_pwd), fetch=True)
                        if res:
                            st.session_state.user_id = res[0][0]
                            st.session_state.username = u_name
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.warning("Please enter both username and password.")
    else:
        st.sidebar.write(f"Welcome back, **{st.session_state.username}**!")
        if st.sidebar.button("Logout"):
            st.session_state.user_id = None
            st.session_state.username = None
            clear_viewing_movie()
            st.rerun()

# ==========================================
# 4. Page: Details Logic (Optimized with View)
# ==========================================
def show_movie_details(movie_id):
    st.button("⬅️ Back to List", on_click=clear_viewing_movie)
    
    # 🌟 OPTIMIZATION: Using v_movie_full_details to get everything (including genres and local stats) in one go
    query = """
        SELECT title, original_title, release_date, original_language, overview, 
               vote_average, vote_count, poster_url, all_genres, local_avg_rating, local_total_reviews 
        FROM v_movie_full_details 
        WHERE movie_id = %s
    """
    movie_res = run_query(query, (movie_id,), fetch=True)
    if not movie_res:
        st.error("Movie not found.")
        return
    
    title, orig_title, rel_date, lang, overview, tmdb_avg, tmdb_votes, poster, genres, loc_avg, loc_votes = movie_res[0]
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(poster if poster else "https://via.placeholder.com/300x450", use_container_width=True)
        
        # 📌 NEW: Watchlist Toggle Button
        if st.session_state.user_id:
            is_in_wl = run_query("SELECT 1 FROM watchlists WHERE user_id=%s AND movie_id=%s", (st.session_state.user_id, movie_id), fetch=True)
            if is_in_wl:
                if st.button("➖ Remove from Watchlist", use_container_width=True):
                    run_query("DELETE FROM watchlists WHERE user_id=%s AND movie_id=%s", (st.session_state.user_id, movie_id))
                    st.toast("Removed from your watchlist!")
                    st.rerun()
            else:
                if st.button("➕ Add to Watchlist", use_container_width=True, type="primary"):
                    run_query("INSERT INTO watchlists (user_id, movie_id) VALUES (%s, %s)", (st.session_state.user_id, movie_id))
                    st.toast("Added to your watchlist!")
                    st.rerun()
                    
    with col2:
        st.header(title)
        st.caption(f"Original: {orig_title} | Released: {rel_date} | Lang: {lang} | Genres: {genres or 'N/A'}")
        st.write(f"**Overview:** {overview}")
        
        m1, m2 = st.columns(2)
        m1.metric("TMDB Rating", f"⭐ {tmdb_avg}", f"{tmdb_votes} votes", delta_color="off")
        m2.metric("Local Rating", f"⭐ {loc_avg}", f"{loc_votes} reviews", delta_color="off")

    st.divider()
    
    if st.session_state.user_id:
        st.subheader("My Review")
        my_review = run_query("SELECT rating, review_text FROM user_reviews WHERE movie_id = %s AND user_id = %s", 
                             (movie_id, st.session_state.user_id), fetch=True)
        
        if my_review and not st.session_state.edit_review_mode:
            with st.container(border=True):
                st.write(f"**My Rating:** ⭐ {my_review[0][0]}")
                st.write(f"**My Review:** {my_review[0][1]}")
                
            if st.button("Edit Rating and Review"):
                st.session_state.edit_review_mode = True
                st.rerun()
        else:
            with st.form("my_review_form"):
                current_score = float(my_review[0][0]) if my_review else 8.0
                current_text = my_review[0][1] if my_review else ""
                score = st.slider("Rating", 0.0, 10.0, current_score, step=0.5)
                text = st.text_area("Review Comments", current_text)
                
                btn_label = "Update Review" if my_review else "Submit Review"
                if st.form_submit_button(btn_label):
                    run_query("""
                        INSERT INTO user_reviews (user_id, movie_id, rating, review_text) 
                        VALUES (%s, %s, %s, %s) 
                        ON CONFLICT (user_id, movie_id) DO UPDATE SET rating=EXCLUDED.rating, review_text=EXCLUDED.review_text
                    """, (st.session_state.user_id, movie_id, score, text))
                    st.success("Review saved successfully!")
                    st.session_state.edit_review_mode = False
                    st.rerun()
            
            if my_review and st.session_state.edit_review_mode:
                if st.button("Cancel Edit"):
                    st.session_state.edit_review_mode = False
                    st.rerun()
    else:
        st.info("💡 Please login on the left to rate, review, or add to your watchlist.")

# ==========================================
# 5. Page: Main Plaza
# ==========================================
def main_plaza():
    st.header("🔍 Explore Movies")
    search_q = st.text_input("Enter movie title or keywords to search...", "")
    
    if search_q != st.session_state.last_search:
        st.session_state.plaza_page = 1
        st.session_state.last_search = search_q

    items_per_page = 20
    offset = (st.session_state.plaza_page - 1) * items_per_page

    base_query = "FROM movies"
    params = []
    if search_q:
        base_query += " WHERE title ILIKE %s OR overview ILIKE %s"
        params.extend([f'%{search_q}%', f'%{search_q}%'])

    count_query = f"SELECT COUNT(*) {base_query}"
    total_items = run_query(count_query, tuple(params), fetch=True)[0][0]
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)

    query = f"SELECT movie_id, title, vote_average, poster_url {base_query} ORDER BY popularity DESC LIMIT %s OFFSET %s"
    params.extend([items_per_page, offset])
    
    movies = run_query(query, tuple(params), fetch=True)
    
    cols = st.columns(5)
    for i, m in enumerate(movies):
        with cols[i % 5]:
            st.image(m[3] if m[3] else "https://via.placeholder.com/300x450?text=No+Image", use_container_width=True)
            st.markdown(f"**{m[1]}**")
            st.caption(f"⭐ {m[2]}")
            if st.button("View Details", key=f"btn_{m[0]}"):
                st.session_state.viewing_movie = m[0]
                st.session_state.edit_review_mode = False
                st.rerun()
    
    if total_pages > 1:
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.session_state.plaza_page > 1:
                if st.button("⬅️ Previous Page"):
                    st.session_state.plaza_page -= 1
                    st.rerun()
        with col2:
            st.markdown(f"<div style='text-align: center'>Page {st.session_state.plaza_page} of {total_pages}</div>", unsafe_allow_html=True)
        with col3:
            if st.session_state.plaza_page < total_pages:
                if st.button("Next Page ➡️"):
                    st.session_state.plaza_page += 1
                    st.rerun()

# ==========================================
# 6. Page: My Watchlist (NEW 📌)
# ==========================================
def my_watchlist():
    st.header("🕒 My Watchlist")
    if not st.session_state.user_id:
        st.warning("Please login first to view your watchlist.")
        return
    
    # 🌟 OPTIMIZATION: Leveraging v_movie_full_details for easy data retrieval
    query = """
    SELECT v.movie_id, v.title, v.poster_url, v.vote_average, w.added_at 
    FROM watchlists w
    JOIN v_movie_full_details v ON w.movie_id = v.movie_id
    WHERE w.user_id = %s
    ORDER BY w.added_at DESC
    """
    movies = run_query(query, (st.session_state.user_id,), fetch=True)
    
    if not movies:
        st.info("Your watchlist is empty. Go to Movie Plaza to find something to watch!")
    else:
        cols = st.columns(5)
        for i, m in enumerate(movies):
            with cols[i % 5]:
                st.image(m[2] if m[2] else "https://via.placeholder.com/300x450", use_container_width=True)
                st.markdown(f"**{m[1]}**")
                st.caption(f"⭐ {m[3]}")
                if st.button("View Details", key=f"wl_btn_{m[0]}"):
                    st.session_state.viewing_movie = m[0]
                    st.rerun()

# ==========================================
# 7. Page: Personal Footprint
# ==========================================
def my_ratings():
    st.header("🍿 My Rating History")
    if not st.session_state.user_id:
        st.warning("Please login first to view your personal rating history.")
        return
    
    rated_movies = run_query("""
        SELECT m.title, r.rating, r.review_text, r.created_at, m.poster_url 
        FROM user_reviews r
        JOIN movies m ON r.movie_id = m.movie_id
        WHERE r.user_id = %s
        ORDER BY r.created_at DESC
    """, (st.session_state.user_id,), fetch=True)
    
    if not rated_movies:
        st.write("You haven't reviewed any movies yet.")
    else:
        for rm in rated_movies:
            with st.container(border=True):
                c1, c2 = st.columns([1, 8])
                c1.image(rm[4] if rm[4] else "https://via.placeholder.com/80x120?text=No+Image", width=80)
                c2.markdown(f"**{rm[0]}**")
                c2.caption(f"My Rating: ⭐{rm[1]} | Review Date: {rm[3]}")
                c2.write(f"My Review: {rm[2]}")

# ==========================================
# 8. Page: Decade Genre Champions
# ==========================================
def decade_genre_champions():
    st.header("🏆 Decade Genre Champions")
    genres = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery", "Romance", "Science Fiction", "TV Movie", "Thriller", "War", "Western"]
    selected_genre = st.selectbox("Choose a genre:", genres)
    
    if selected_genre:
        query = """
        WITH MovieDecades AS (
            SELECT m.movie_id, m.title, m.poster_url, g.genre_name, FLOOR(EXTRACT(YEAR FROM m.release_date) / 10) * 10 AS decade, m.vote_average AS tmdb_rating, m.vote_count AS tmdb_votes
            FROM movies m
            JOIN movie_genres mg ON m.movie_id = mg.movie_id
            JOIN genres g ON mg.genre_id = g.genre_id
            WHERE m.vote_count >= 1000 AND m.release_date IS NOT NULL AND g.genre_name = %s
        ),
        RankedChampions AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY decade ORDER BY tmdb_rating DESC, tmdb_votes DESC) as rank_in_category FROM MovieDecades
        )
        SELECT movie_id, decade, title, tmdb_rating, tmdb_votes, poster_url FROM RankedChampions WHERE rank_in_category = 1 ORDER BY decade DESC
        """
        champions = run_query(query, (selected_genre,), fetch=True)
        if champions:
            for champ in champions:
                with st.container(border=True):
                    col_year, col_poster, col_info = st.columns([1.5, 1.5, 5])
                    col_year.subheader(f"🕰️ {int(champ[1])}s")
                    col_poster.image(champ[5] if champ[5] else "https://via.placeholder.com/150", use_container_width=True)
                    col_info.markdown(f"### {champ[2]}")
                    col_info.caption(f"⭐ Rating: {champ[3]} | 🗳️ Votes: {champ[4]}")
                    if col_info.button("View Details", key=f"champ_{champ[0]}_{champ[1]}"):
                        st.session_state.viewing_movie = champ[0]
                        st.rerun()

# ==========================================
# 9. Page: Veteran's Choice (Optimized with View)
# ==========================================
def veteran_hidden_gems():
    st.header("💎 Veteran's Choice")
    st.write("Discover low-profile movies highly rated by our most active reviewers.")

    # 🌟 OPTIMIZATION: Using v_movie_full_details removes the need to manually join `movies` AND `movie_stats`
    query = """
    WITH VeteranUsers AS (
        SELECT user_id FROM user_reviews GROUP BY user_id HAVING COUNT(movie_id) >= 100
    ),
    VeteranRatings AS (
        SELECT r.movie_id, AVG(r.rating) AS veteran_avg_rating
        FROM user_reviews r
        JOIN VeteranUsers vu ON r.user_id = vu.user_id
        GROUP BY r.movie_id
    )
    SELECT v.movie_id, v.title, vr.veteran_avg_rating, v.local_total_reviews, v.poster_url, v.vote_average
    FROM VeteranRatings vr
    JOIN v_movie_full_details v ON vr.movie_id = v.movie_id
    WHERE v.local_total_reviews < 50 AND vr.veteran_avg_rating >= 4.5
    ORDER BY vr.veteran_avg_rating DESC;
    """
    gems = run_query(query, fetch=True)
    if gems:
        for g in gems:
            with st.container(border=True):
                c1, c2 = st.columns([1, 5])
                c1.image(g[4] if g[4] else "https://via.placeholder.com/150", use_container_width=True)
                with c2:
                    st.subheader(g[1])
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Veteran Rating", f"⭐ {g[2]:.1f}")
                    m2.metric("Public Reviews", f"👥 {g[3]}")
                    m3.metric("TMDB Avg", f"🌍 {g[5]}")
                    if st.button("View Details", key=f"gem_{g[0]}"):
                        st.session_state.viewing_movie = g[0]
                        st.rerun()
    else:
        st.info("No hidden gems found yet. Try lowering the 'Veteran' threshold in code for testing!")

# ==========================================
# 10. Page: Controversial Hits (Optimized with View)
# ==========================================
def controversial_hits():
    st.header("🔥 Controversial Hits")
    st.write("Movies that divide our community: High standard deviation in ratings means people either love them or hate them.")

    # 🌟 OPTIMIZATION: Again, replacing dual JOINs of `movies` and `movie_stats` with the view
    query = """
    SELECT 
        v.movie_id,
        v.title,
        v.local_avg_rating,
        v.local_total_reviews,
        ROUND(STDDEV(r.rating), 3) AS rating_spread,
        v.poster_url
    FROM user_reviews r
    JOIN v_movie_full_details v ON r.movie_id = v.movie_id
    GROUP BY 
        v.movie_id, v.title, v.local_avg_rating, v.local_total_reviews, v.poster_url
    HAVING COUNT(r.rating) >= 30 
    ORDER BY rating_spread DESC
    LIMIT 10;
    """
    
    controversial = run_query(query, fetch=True)
    
    if controversial:
        for movie in controversial:
            m_id, title, avg_rating, total_rev, spread, poster = movie
            with st.container(border=True):
                c1, c2 = st.columns([1, 5])
                with c1:
                    st.image(poster if poster else "https://via.placeholder.com/150", use_container_width=True)
                with c2:
                    st.subheader(title)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Controversy Index", f"📈 {spread}")
                    m2.metric("Local Avg Rating", f"⭐ {avg_rating}")
                    m3.metric("Total Reviews", f"💬 {total_rev}")
                    
                    st.caption("A higher Index means more mixed 1-star and 10-star reviews.")
                    
                    if st.button("View Details", key=f"con_btn_{m_id}"):
                        st.session_state.viewing_movie = m_id
                        st.rerun()
    else:
        st.info("Not enough data to calculate controversy yet (Requires movies with at least 30 reviews).")

# ==========================================
# 11. Main App Routing
# ==========================================
login_section()

nav = st.sidebar.radio(
    "Navigation", 
    ["Movie Plaza", "My Watchlist", "My Rating History", "Decade Genre Champions", "Veteran's Choice", "Controversial Hits"],
    on_change=clear_viewing_movie
)

if st.session_state.viewing_movie:
    show_movie_details(st.session_state.viewing_movie)
elif nav == "My Watchlist":
    my_watchlist()
elif nav == "My Rating History":
    my_ratings()
elif nav == "Decade Genre Champions":
    decade_genre_champions()
elif nav == "Veteran's Choice":
    veteran_hidden_gems()
elif nav == "Controversial Hits":
    controversial_hits()
else:
    main_plaza()