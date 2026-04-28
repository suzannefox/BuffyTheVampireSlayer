import buffy_functions as bf
import streamlit as st
from pathlib import Path
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# --- get data ---
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR.parent / "data" / "Episode Information.txt"

df = bf.get_buffydata_from_wikipedia(DATA_FILE)
fig_buffy = bf.plot_buffy_viewers(df)
list_writers, list_directors = bf.get_filmakers(df)

default_writer = "Select a writer..."
default_director = "Select a director..."

# --- state variables ---
if 'refresh_count' not in st.session_state:
    st.session_state.refresh_count = 0
# track when a different writer is selected
if 'last_writer' not in st.session_state:
    st.session_state.last_writer = None
# track when a different director is selected
if 'last_director' not in st.session_state:
    st.session_state.last_director = None
# track which is the last dropdown selected
if 'last_selection_type' not in st.session_state:
    st.session_state.last_selection_type = None
# track the last selected value (writer or director, depending on the last selection type)
if 'last_selection_value' not in st.session_state:
    st.session_state.last_selection_value = None


# --- Header ---
st.markdown("### Buffy Episode explorer")

# --- Chart (FULL WIDTH, TOP PRIORITY) ---
text_episode = st.empty()

if st.session_state.last_selection_type is None:
    fig = fig_buffy
else:
    fig = bf.filter_plot(
        fig_buffy,
        df,
        st.session_state.last_selection_type,
        st.session_state.last_selection_value
    )

# 👇 make chart behave properly everywhere
fig.update_layout(
    height=600,                 # key for mobile
    margin=dict(t=40, b=20)
)

fig.update_traces(
    marker=dict(size=8),        # easier to tap on mobile
    selected=dict(marker=dict(opacity=0.8)),
    unselected=dict(marker=dict(opacity=0.8))
)

event = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select='rerun'
)

if event and event.selection:
    points = event.selection["points"]
    if points:
        clicked_point = points[0]
        episode = clicked_point["x"]
        episode_details = bf.get_episode_details(df, episode)
        text_episode.markdown(episode_details, unsafe_allow_html=True)

text_source = st.empty()
text_source.markdown(
    "Data sourced from Wikipedia: "
    "[Buffy the Vampire Slayer episode guide]"
    "(https://en.wikipedia.org/wiki/List_of_Buffy_the_Vampire_Slayer_episodes)"
)

# --- Controls (NOW BELOW CHART) ---
# st.markdown("#### Highlight episodes by writer or director")

# text_info = st.empty()

# col1, col2 = st.columns(2)  # ← equal width, works better on mobile

# with col1:
#     options = [default_writer] + list(list_writers.keys())
#     selected_writer = st.selectbox(
#         'Writers',
#         options=options,
#         key='writer',
#         index=0,
#         format_func=lambda w: w if w == default_writer else f"{w} ({list_writers[w]})"
#     )

# with col2:
#     options = [default_director] + list(list_directors.keys())
#     selected_director = st.selectbox(
#         'Directors',
#         options=options,
#         key='director',
#         index=0,
#         format_func=lambda d: d if d == default_director else f"{d} ({list_directors[d]})"
#     )