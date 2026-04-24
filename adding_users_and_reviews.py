import random

# ==========================================
# 1. Your Real Movie IDs (176 in total)
# ==========================================
REAL_MOVIE_IDS = [
    83533, 1613798, 687163, 1470130, 1290821, 1327819, 1084577, 840464, 1290417, 1304313, 
    1171145, 1010755, 1641319, 1297842, 1311031, 502356, 1480387, 1159559, 1084242, 848116, 
    350, 1419406, 1368166, 1601797, 1193501, 680493, 1265609, 70435, 936075, 755898, 1511057, 
    1418657, 1659087, 1234731, 634649, 1159831, 662707, 1268127, 1367642, 329505, 7451, 
    1316092, 879945, 1115544, 157336, 24428, 1049471, 1242898, 1266127, 1272837, 1646787, 
    1168190, 418579, 299536, 1610418, 1108427, 875828, 440249, 1110034, 1658216, 1088434, 
    425274, 278, 226674, 1234821, 238, 1236153, 299534, 803796, 1325734, 1119449, 1539104, 
    1241470, 1572073, 1266992, 1010581, 28322, 1472951, 300496, 1107166, 967998, 1416391, 
    77338, 1246049, 1306368, 181808, 533535, 1424965, 252969, 383498, 744275, 1314481, 
    50619, 27205, 19995, 1339876, 120, 1582770, 597, 10867, 20222, 999136, 496243, 1038392, 
    680, 155, 283995, 1011985, 858024, 1387382, 615, 1579, 76600, 62029, 671, 1061474, 
    1233413, 122, 14836, 441168, 324857, 603, 129, 564, 1218925, 991494, 81774, 569094, 
    361743, 214756, 911430, 1408208, 1241982, 567609, 10138, 402431, 467905, 348, 1022789, 
    807, 872585, 950396, 969681, 1054867, 5236, 677638, 550, 1192548, 315635, 13, 798645, 
    346698, 980477, 1156594, 1167307, 38, 1213898, 1233506, 1315303, 808, 950387, 1228246, 
    1117857, 557, 1726, 519182, 508947, 269149, 372058, 1184918, 240, 497, 617126, 424
]

TOTAL_USERS = 40       
VETERAN_USER_ID = 1    

# Setup two specific movies for our scenarios
HIDDEN_GEM_ID = REAL_MOVIE_IDS[0]  # 83533 -> Hidden Gem
POLARIZING_ID = REAL_MOVIE_IDS[1]  # 1613798 -> Polarizing Movie

reviews_data = [] # Store generated reviews (user_id, movie_id, rating)

# ==========================================
# 2. Generate Rating Logic (0-10 scale, no review text)
# ==========================================

# --- Scenario A: Veteran Critic ---
# Randomly select 105 movies from the real IDs for the veteran to watch (satisfies COUNT >= 100)
veteran_watched = random.sample(REAL_MOVIE_IDS, 105)
if HIDDEN_GEM_ID not in veteran_watched:
    veteran_watched[0] = HIDDEN_GEM_ID

for m_id in veteran_watched:
    if m_id == HIDDEN_GEM_ID:
        rating = random.choice([9.5, 10.0]) # Veteran gives the hidden gem a perfect score
    else:
        rating = round(random.uniform(5.0, 8.5), 1) 
    reviews_data.append((VETERAN_USER_ID, m_id, rating))

# --- Scenarios B & C: Casual Users ---
for user_id in range(2, TOTAL_USERS + 1):
    # [Create extremely polarizing movie]: All casual users watched it, half gave 0, half gave 10
    polarizing_rating = 0.0 if user_id % 2 == 0 else 10.0 
    reviews_data.append((user_id, POLARIZING_ID, polarizing_rating))
    
    # [Maintain hidden gem]: Only users 2, 3, and 4 watched it
    if user_id in [2, 3, 4]:
        reviews_data.append((user_id, HIDDEN_GEM_ID, random.choice([8.5, 9.0, 9.5])))
        
    # Other random viewing behaviors as "background noise"
    available_movies = [m for m in REAL_MOVIE_IDS if m not in (HIDDEN_GEM_ID, POLARIZING_ID)]
    num_watched = random.randint(10, 20)
    normal_watched = random.sample(available_movies, num_watched)
    
    for m_id in normal_watched:
        rating = round(random.uniform(4.0, 7.5), 1)
        reviews_data.append((user_id, m_id, rating))

# ==========================================
# 3. Pre-calculate movie_stats (for incremental updates)
# ==========================================
movie_stats = {} 
for r in reviews_data:
    m_id, rating = r[1], r[2]
    if m_id not in movie_stats:
        movie_stats[m_id] = {'count': 0, 'sum': 0.0}
    movie_stats[m_id]['count'] += 1
    movie_stats[m_id]['sum'] += rating

# ==========================================
# 4. Generate SQL file for appending data (PostgreSQL)
# ==========================================
with open('/Users/oulin_yang/Desktop/append_demo_data.sql', 'w', encoding='utf-8') as f:
    
    f.write("-- ==========================================\n")
    f.write("-- Append mock users, rating records, and update local movie stats table\n")
    f.write("-- ==========================================\n\n")

    f.write("-- 1. Append Users\n")
    f.write("INSERT INTO users (user_id, username, email, password_hash) VALUES\n")
    user_values = []
    for u in range(1, TOTAL_USERS + 1):
        name = "veteran_critic" if u == VETERAN_USER_ID else f"casual_user_{u}"
        email = f"{name}@demo.com"
        pwd_hash = "$2y$10$Qz8mock_hash...aT" 
        user_values.append(f"({u}, '{name}', '{email}', '{pwd_hash}')")
    f.write(",\n".join(user_values) + "\nON CONFLICT (username) DO NOTHING;\n\n") 
    
    # Fix PostgreSQL auto-increment ID sequence (crucial to prevent errors when real users register later)
    f.write("SELECT setval('users_user_id_seq', (SELECT MAX(user_id) FROM users));\n\n")

    f.write("-- 2. Append User Reviews\n")
    f.write("INSERT INTO user_reviews (user_id, movie_id, rating) VALUES\n")
    review_values = [f"({r[0]}, {r[1]}, {r[2]})" for r in reviews_data]
    f.write(",\n".join(review_values) + "\nON CONFLICT (user_id, movie_id) DO UPDATE SET rating = EXCLUDED.rating;\n\n")

    f.write("-- 3. Update Movie Stats\n")
    f.write("INSERT INTO movie_stats (movie_id, total_reviews, average_rating) VALUES\n")
    stats_values = []
    for m_id, stats in movie_stats.items():
        avg_rating = round(stats['sum'] / stats['count'], 1)
        stats_values.append(f"({m_id}, {stats['count']}, {avg_rating})")
    
    # Use native PostgreSQL syntax for safe incremental updates
    f.write(",\n".join(stats_values) + """
ON CONFLICT (movie_id) DO UPDATE 
SET 
    total_reviews = movie_stats.total_reviews + EXCLUDED.total_reviews,
    average_rating = ROUND(
        (movie_stats.total_reviews * movie_stats.average_rating + EXCLUDED.total_reviews * EXCLUDED.average_rating) 
        / (movie_stats.total_reviews + EXCLUDED.total_reviews), 1
    );
""")

print(f"✅ Generation complete! Loaded a total of {len(REAL_MOVIE_IDS)} real movie IDs.")
print(f"✅ Generated {TOTAL_USERS} users and {len(reviews_data)} precise rating records.")
print(f"📁 Please check 'append_demo_data.sql' in your current directory and import it into your PostgreSQL database.")