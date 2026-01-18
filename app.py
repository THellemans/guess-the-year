import streamlit as st
import pandas as pd
import os
import json
import numpy as np
import base64

# -------------------------
# Helper functions
# -------------------------

def display_music_information(song_playing):
    artist, title, year_mp3 = song_playing.split('_')
    year = year_mp3.replace('.mp3', '')

    st.markdown(
        f"""
        <div style="background-color:#d5f3d7;padding:15px;border-radius:10px;text-align:center">
            <h2>🎵 {year} 🎵</h2>
            <p><strong>Artist:</strong> {artist}<br>
               <strong>Title:</strong> {title}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def give_points(team):
    st.session_state.scoreboard[team, 0] = int(
        st.session_state.song_playing.split('_')[-1][:4]
    )
    st.session_state.scoreboard[team, :] = np.sort(
        st.session_state.scoreboard[team, :]
    )
    if st.session_state.scoreboard[team, 0] != 0:
        st.title("WINNER!")

# -------------------------
# Session state init
# -------------------------

if "can_undo" not in st.session_state:
    st.session_state.can_undo = False

if "list_chosen" not in st.session_state:
    st.session_state.list_chosen = False

if "songs_played" not in st.session_state:
    st.session_state.songs_played = []

if "chose_players" not in st.session_state:
    st.session_state.chose_players = False

if "song_active" not in st.session_state:
    st.session_state.song_active = False

if "locs" not in st.session_state:
    with open("data/locs.json", "r") as file:
        st.session_state.locs = json.load(file)

# -------------------------
# Load data
# -------------------------

st.session_state.df_all = pd.read_csv(
    os.path.join(
        st.session_state.locs["centralized"],
        "unique_per_list.csv"
    )
)

# -------------------------
# App header
# -------------------------

st.markdown(
    "<h1 style='text-align: center;'>🎶 Guess the year 🎶</h1>",
    unsafe_allow_html=True
)

# -------------------------
# Rules
# -------------------------

with st.expander("📖 Explanation: How to Play 'Guess the Year'"):
    st.markdown("""
    ## 🕹️ Welcome to *Guess the Year*!

    Guess the release year of songs by placing them correctly
    relative to the timeline you’ve already built.

    **Minimum rules**
    1. Divide into teams
    2. Hear a song
    3. Guess the year
    4. Correct guess wins the song

    **Optional rules**
    - Guess artist & title for bonus points
    - Use tokens to contest other teams
    """)

# -------------------------
# Player setup
# -------------------------

if not st.session_state.chose_players:
    number_rounds = st.slider(
        "How many points to win?",
        min_value=2,
        max_value=30,
        value=10
    )

    number_of_players = st.slider(
        "How many players?",
        min_value=1,
        max_value=10,
        value=2
    )

    if st.button("Confirm!"):
        st.session_state.number_rounds = number_rounds
        st.session_state.number_of_players = number_of_players
        st.session_state.scoreboard = np.zeros(
            (number_of_players, number_rounds),
            dtype=int
        )
        st.session_state.scoreboard[:, -1] = np.random.randint(
            1960, 2020, number_of_players
        )
        st.session_state.chose_players = True
        st.rerun()

    st.stop()

# -------------------------
# Restart
# -------------------------

if st.button("Restart Game"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# -------------------------
# Choose music lists
# -------------------------

if not st.session_state.list_chosen:
    st.write("Choose one or more music lists you want to use")

    available_origins = list(
        st.session_state.df_all.origin.unique()
    )
    available_with_all = ["All"] + available_origins

    chosen_lists = st.multiselect(
        "Choose your list(s)",
        available_with_all
    )

    if "All" in chosen_lists:
        st.session_state.chosen_list = available_origins
    else:
        st.session_state.chosen_list = chosen_lists

    if st.session_state.chosen_list and st.button("Choose list(s)!"):
        df = st.session_state.df_all.query(
            "origin in @st.session_state.chosen_list"
        ).copy()

        df["artist"] = df["artist"].str.replace("_", "", regex=False)
        df["title"] = df["title"].str.replace("_", "", regex=False)

        df["qr_code"] = df["artist"] + "_" + df["title"] + ".png"

        spotify_links = os.listdir(
            st.session_state.locs["qrcode_spotify"]
        )
        df = df.query("qr_code in @spotify_links")

        st.session_state.df = df
        st.session_state.list_chosen = True

    st.stop()

# -------------------------
# Show random song
# -------------------------

if st.button("🔊 Show Random Song"):
    while True:
        random_row = st.session_state.df.sample().iloc[0]
        random_song = (
            f"{random_row.artist}_"
            f"{random_row.title}_"
            f"{random_row.year}"
        )
        if random_song not in st.session_state.songs_played:
            break

    st.session_state.song_playing = random_song
    st.session_state.songs_played.append(random_song)
    st.session_state.song_active = True

    qr_path = os.path.join(
        st.session_state.locs["qrcode_spotify"],
        random_row.qr_code
    )

    st.image(qr_path)

    if not pd.isna(random_row.youtube_link):
        st.markdown(
            f"[YouTube link]({random_row.youtube_link})"
        )

# -------------------------
# Show solution (only if song active)
# -------------------------

if st.session_state.song_active:
    if st.button("Show solution"):
        display_music_information(
            st.session_state.song_playing
        )

# -------------------------
# Team buttons (only if song active)
# -------------------------

if st.session_state.song_active:
    columns = st.columns(
        st.session_state.number_of_players
    )

    for i in range(st.session_state.number_of_players):
        with columns[i]:
            if st.button(f"Team {i + 1} answered correctly!"):
                give_points(i)
                st.session_state.winning_person = i
                st.session_state.can_undo = True
                st.session_state.song_active = False

# -------------------------
# Undo
# -------------------------

if st.session_state.can_undo:
    if st.button("Undo last addition"):
        year = int(
            st.session_state.song_playing
            .split("_")[-1][:4]
        )
        loc = (
            st.session_state.scoreboard[
                st.session_state.winning_person, :
            ] == year
        )
        st.session_state.scoreboard[
            st.session_state.winning_person, loc
        ] = 0
        st.session_state.scoreboard[
            st.session_state.winning_person, :
        ] = np.sort(
            st.session_state.scoreboard[
                st.session_state.winning_person, :
            ]
        )
        st.session_state.song_active = True
        st.session_state.can_undo = False

# -------------------------
# Scoreboard
# -------------------------

for p in range(st.session_state.number_of_players):
    st.title(
        "-".join(
            map(
                str,
                st.session_state.scoreboard[p, :]
            )
        )
    )
