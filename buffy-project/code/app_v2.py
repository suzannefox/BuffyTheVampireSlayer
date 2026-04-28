import buffy_functions as bf
import streamlit as st
from pathlib import Path
import plotly.express as px

st.set_page_config(layout="wide")

# --- styling (tighten vertical space) ---
st.markdown("""
<style>
.block-container {
    padding-top: 0.5rem;
    padding-bottom: 0rem;
}
h3, h4 {
    margin-bottom: 0.3rem;
}
</style>
""", unsafe_allow_html=True)

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

# --- controls FIRST (logic happens here) ---
st.markdown("#### Highlight episodes by writer or director")

col1, col2 = st.columns(2)

with col1:
    options_w = [default_writer] + list(list_writers.keys())
    selected_writer = st.selectbox(
        'Writers',
        options=options_w,
        key='writer',
        index=0,
        format_func=lambda w: w if w == default_writer else f"{w} ({list_writers[w]})"
    )

with col2:
    options_d = [default_director] + list(list_directors.keys())
    selected_director = st.selectbox(
        'Directors',
        options=options_d,
        key='director',
        index=0,
        format_func=lambda d: d if d == default_director else f"{d} ({list_directors[d]})"
    )

# --- determine selection (simple + robust) ---
selection_type = None
selection_value = None

if selected_writer != default_writer:
    selection_type = "writer"
    selection_value = selected_writer
elif selected_director != default_director:
    selection_type = "director"
    selection_value = selected_director

# --- info text ---
if selection_type is None:
    st.write("Nothing chosen currently")
else:
    st.write(f"Highlighting: {selection_type} = {selection_value}")

# --- build figure AFTER selection is known ---
if selection_type is None:
    fig = fig_buffy
else:
    fig = bf.filter_plot(fig_buffy, df, selection_type, selection_value)

# --- improve chart for mobile + layout ---
fig.update_layout(
    height=600,
    margin=dict(t=40, b=20),
    title=dict(
        x=0,
        xanchor="left",
        y=0.95
    )
)

fig.update_traces(
    marker=dict(size=8),
    selected=dict(marker=dict(opacity=0.8)),
    unselected=dict(marker=dict(opacity=0.8))
)

# --- header ---
st.markdown("### Buffy Episode explorer")

# --- chart ---
text_episode = st.empty()

event = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun"
)

# --- click handling ---
if event and event.selection:
    points = event.selection["points"]
    if points:
        clicked_point = points[0]
        episode = clicked_point["x"]
        episode_details = bf.get_episode_details(df, episode)
        text_episode.markdown(episode_details, unsafe_allow_html=True)

# --- source (kept tight under chart) ---
st.markdown(
    "Data sourced from Wikipedia: "
    "[Buffy the Vampire Slayer episode guide]"
    "(https://en.wikipedia.org/wiki/List_of_Buffy_the_Vampire_Slayer_episodes)"
)