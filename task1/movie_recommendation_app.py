import numpy as np
import pandas as pd
import streamlit as st
import sqlite3

# Load movie data
credits_df = pd.read_csv("tmdb_5000_credits.csv")
movies_df = pd.read_csv("tmdb_5000_movies.csv")

# Connect to the SQLite database
conn = sqlite3.connect('user_history.db')
cursor = conn.cursor()

# Create a table to store user history
cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_history (
        user_id TEXT,
        movie_title TEXT,
        rating REAL,
        genre TEXT,  -- Add this line to create the genre column
        PRIMARY KEY (user_id, movie_title)
    )
''')




conn.commit()

# Sample user data with user preferences
user_preferences = {
    'user1': ['Horror'],
    'user2': ['Action'],
    'user3': ['Drama', 'Comedy'],
}


def update_user_history(user_id, movie_title, rating, genre):
    # Update the user's history in the database
    cursor.execute("INSERT OR REPLACE INTO user_history (user_id, movie_title, rating, genre) VALUES (?, ?, ?, ?)", (user_id, movie_title, rating, genre))
    conn.commit()


def get_user_history(user_id):
    # Retrieve user history from the database
    cursor.execute("SELECT movie_title FROM user_history WHERE user_id = ?", (user_id,))
    return [row[0] for row in cursor.fetchall()]

def recommend_movies_for_user(user_id, movies_df, user_preferences, user_history):
    watched_movies = user_history
    unseen_movies = movies_df[~movies_df['title'].isin(watched_movies)]

    user_profile = user_preferences.get(user_id, [])
    preferred_genres = set(user_profile)

    # Calculate movie scores based on user profile and filter by preferred genres
    unseen_movies['score'] = unseen_movies.apply(
        lambda row: sum(1 for genre in preferred_genres if genre in row['genres']) if preferred_genres else 0,
        axis=1
    )

    # Sort by score in descending order
    recommended_movies = unseen_movies.sort_values(by='score', ascending=False)

    # Get the top 10 recommendations
    top_movies = recommended_movies.head(10)

    return top_movies[['title', 'genres', 'score']]

def get_movie_details(movie_title, movies_df):
    # Use case-insensitive comparison and strip extra spaces
    movie = movies_df[movies_df['title'].str.strip().str.lower() == movie_title.strip().lower()]
    if not movie.empty:
        return movie[['title', 'overview', 'release_date', 'vote_average']]
    else:
        return None

# Create a Streamlit web app
st.title("Movie Recommendation System")

# User input section
user_id = st.text_input("Enter your user ID (e.g., user1, user2, user3):")

if user_id in user_preferences:
    user_history = get_user_history(user_id)
    recommended_movies = recommend_movies_for_user(user_id, movies_df, user_preferences, user_history)
    st.subheader(f"Top 10 Movie Recommendations for {user_id} (Preferred Genres: {', '.join(user_preferences[user_id])}):")
    st.write(recommended_movies)

    # Ask for the selected movie from the top 10 recommendations
    selected_movie_title = st.text_input("Enter the title of the movie you want to know more about:")

    # Get and display details of the selected movie
    movie_details = get_movie_details(selected_movie_title, movies_df)
    if movie_details is not None:
        st.subheader("Movie Details:")
        st.write(movie_details)


        if selected_movie_title not in user_history:
            selected_movie_genre = movies_df[movies_df['title'] == selected_movie_title]['genres'].values[0]
            update_user_history(user_id, selected_movie_title, 1.0, selected_movie_genre)
            st.write(f"'{selected_movie_title}' has been added to your history.")
        else:
            st.warning(f"'{selected_movie_title}' is already in your history.")
    else:
        st.warning(f"Movie '{selected_movie_title}' not found in the recommendations.")



    
