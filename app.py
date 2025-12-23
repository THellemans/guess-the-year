import streamlit as st
import pandas as pd
import os
import json
import numpy as np

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
        """, unsafe_allow_html=True
    )

# Load in all data we only load in once
if 'can_undo' not in st.session_state:
    st.session_state.can_undo = False

if 'list_chosen' not in st.session_state:
    st.session_state.list_chosen = False

if 'locs' not in st.session_state:
    with open("data/locs.json", 'r') as file:
        st.session_state.locs = json.load(file)

st.session_state.df_all = pd.read_csv(os.path.join(st.session_state.locs['centralized'], 'unique_per_list.csv'))

if 'songs_played' not in st.session_state:
    st.session_state.songs_played = list()

if "chose_players" not in st.session_state:
    st.session_state.chose_players = False

# Streamlit app starts here
st.markdown(
    "<h1 style='text-align: center;'>🎶 Guess the year 🎶</h1>",
    unsafe_allow_html=True
)

if not st.session_state.chose_players:
    number_rounds = st.slider(min_value=2, max_value = 30, value = 10, label = "How many points to win?")
    number_of_players = st.slider(min_value=1, max_value = 10, value = 2, label = "How many players?")
    if st.button("Confirm!"):
        st.session_state.number_rounds = number_rounds
        st.session_state.number_of_players = number_of_players
        st.session_state.scoreboard = np.zeros((st.session_state.number_of_players, st.session_state.number_rounds), dtype = int)
        st.session_state.scoreboard[:, -1] = np.random.randint(1960, 2020, (st.session_state.scoreboard.shape[0]))
        st.session_state.chose_players = True
        st.rerun()
    st.stop()
        
if st.button("Restart Game"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

if not st.session_state.get("list_chosen", False):
    st.write("Choose one or more music lists you want to use")
    
    available_origins = list(st.session_state.df_all.origin.unique())
    available_with_all = ["All"] + available_origins
    
    chosen_lists = st.multiselect(
        "Choose your list(s) :-)", 
        available_with_all
    )

    if "All" in chosen_lists:
        st.session_state.chosen_list = available_origins
    else:
        st.session_state.chosen_list = chosen_lists

    if st.session_state.chosen_list and st.button("Choose list(s)!"):
        st.session_state.df = st.session_state.df_all.query("origin in @st.session_state.chosen_list")
        
        # Clean up artist and title text
        st.session_state.df['artist'] = (
            st.session_state.df['artist']
            .str.replace('_', '', regex=False)
            .str.replace('/', '', regex=False)
            .str.replace('\\', '', regex=False)
        )
        st.session_state.df['title'] = (
            st.session_state.df['title']
            .str.replace('_', '', regex=False)
            .str.replace('/', '', regex=False)
            .str.replace('\\', '', regex=False)
        )
        
        st.session_state.df['qr_code'] = (
            st.session_state.df['artist'] + '_' + st.session_state.df['title'] + '.png'
        )
        
        spotify_links = os.listdir(st.session_state.locs['qrcode_spotify'])
        st.session_state.df = st.session_state.df.query("qr_code in @spotify_links")
        
        st.session_state.list_chosen = True

# Stop execution if no list chosen yet
if not st.session_state.get("list_chosen", False):
    st.stop()

# Provide random file selection and validation
if st.button("🔊 Show Random Song"):
    while True:
        random_row = st.session_state.df.sample().iloc[0]
        random_song = f"{random_row.artist}_{random_row.title}_{random_row.year}"
        st.session_state.song_playing = random_song
        if random_song not in st.session_state.songs_played:
            break
    st.session_state.songs_played.append(random_song)
    # Play the selected MP3 file
    qr_path = os.path.join(st.session_state.locs['qrcode_spotify'], random_row.qr_code)

    
    st.image(qr_path)
    if not pd.isna(random_row.youtube_link):
        st.markdown(f"[YouTube link]({random_row.youtube_link})", unsafe_allow_html=True)


if st.button("Show solution"):
    display_music_information(st.session_state.song_playing)

def give_points(team):
    st.session_state.scoreboard[team, 0] = int(st.session_state.song_playing.split('_')[-1][:4])
    st.session_state.scoreboard[team, :] = np.sort(st.session_state.scoreboard[team, :])
    if st.session_state.scoreboard[team, 0] != 0:
        st.title("WINNER!")

# Create columns based on the number of teams
columns = st.columns(st.session_state.number_of_players)

# Place buttons in separate columns
for i in range(st.session_state.number_of_players):
    with columns[i]:  # Use each column to place a button
        if st.button(f"Team {i + 1} answered correctly!"):
            give_points(i)
            st.session_state.winning_person = i
            st.session_state.can_undo = True

if st.session_state.can_undo:
    if st.button("Undo last addition"):
        loc_last = st.session_state.scoreboard[st.session_state.winning_person, :] == int(st.session_state.song_playing.split('_')[-1][:4])
        st.session_state.scoreboard[st.session_state.winning_person, loc_last] = 0
        st.session_state.scoreboard[st.session_state.winning_person, :] = np.sort(st.session_state.scoreboard[st.session_state.winning_person, :])
        st.session_state.can_undo = False

for num_player in range(st.session_state.number_of_players):
    st.title('-'.join([str(year) for year in st.session_state.scoreboard[num_player, :]]))
