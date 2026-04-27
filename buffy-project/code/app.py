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

# --- Row 1 ---
row1 = st.container()
with row1:
    st.subheader("Buffy Episode explorer")
    text_source = st.empty()   # create placeholder
    text_source.write('Data sourced from Wikipedia: [Buffy the Vampire Slayer episode guide](https://en.wikipedia.org/wiki/List_of_Buffy_the_Vampire_Slayer_episodes)')
    col1, col2 = st.columns([4, 1], gap="small")  # wider plot column

    # because streamlit re-runs the whole script on each interaction, we need to track the last selection action 
    # and value in session state, and use that to determine how to update the plot and the filter info text. 
    # We also need to track the number of times the page has been refreshed, to determine what to show in the 
    # filter info text when there has been no selection action yet (i.e. on first render).
    # So col2 gets defined before col1, because the selection actions and filter info text are defined in col2, 
    # but the plot is defined in col1 and needs to know about the selection actions to update the plot accordingly.
    with col2:

        st.subheader("Highlight episodes by writer or director")
        text_info = st.empty()   # create placeholder

        options = [default_writer] + list(list_writers.keys())
        selected_writer = st.selectbox(
            'Writers',
            options=options,
            key='writer',
            index=0,
            format_func=lambda w: w if w == default_writer else f"{w} ({list_writers[w]})"
        )
        # the selected writer has changed since the last selection action
        # so the writer filter has been updated, and we need to update state variables to 
        # track the last selection action and value, and update the filter info text and the plot accordingly
        if st.session_state.last_writer != selected_writer:
            st.session_state.last_writer = selected_writer
            st.session_state.last_selection_type = 'writer'
            st.session_state.last_selection_value = selected_writer

            # the default writer was selected, so no filter is used
            if selected_writer == default_writer:
                st.session_state.last_selection_type = None
                st.session_state.last_selection_value = None

        options = [default_director] + list(list_directors.keys())
        selected_director = st.selectbox(
            'Directors',
            options=options,
            key='director',
            index=0,
            format_func=lambda d: d if d == default_director else f"{d} ({list_directors[d]})"
        )
        # if the selected director has changed since the last selection action
        if st.session_state.last_director != selected_director:
            st.session_state.last_director = selected_director
            st.session_state.last_selection_type = 'director'
            st.session_state.last_selection_value = selected_director

            # the default director was selected, so no filter is used
            if selected_director == default_director:
                st.session_state.last_selection_type = None
                st.session_state.last_selection_value = None

        if st.session_state.refresh_count == 0:
            text_info.write('Nothing chosen currently')
        elif st.session_state.last_selection_type is None:
            text_info.write('Nothing chosen currently')
        else:
            text_filter = f'Highlighting : {st.session_state.last_selection_type} is {st.session_state.last_selection_value}' 
            text_info.write(text_filter)

        text_episode = st.empty()   # create placeholder for episode details

        # the plot needs to be re-rendered in col1 on each selection action, and the filter criteria passed to the 
        # filter_plot function to update the plot accordingly. The bf.filter_plot function will determine which 
        # episodes match the filter criteria and add a trace to the plot to highlight those episodes.
        # If the filter criteria is the default (i.e. no selection action yet), then the plot will be returned without 
        # any additional traces added.
        with col1:

            if st.session_state.last_selection_type is None:
                fig = fig_buffy
            else:
                fig = bf.filter_plot(fig_buffy, df, st.session_state.last_selection_type, st.session_state.last_selection_value)

            # when the user clicks on an episode it displays the full details
            event = st.plotly_chart(fig, use_container_width=True, height = 'content', on_select='rerun')
            if event and event.selection:
                points = event.selection["points"]
                if points:
                    clicked_point = points[0]
                    episode = clicked_point["x"]
                    episode_details = bf.get_episode_details(df, episode)
                    text_episode.markdown(episode_details, unsafe_allow_html=True)

# --- Row 3 (full width) ---
# st.divider()
st.session_state.refresh_count +=1

text_refresh = st.empty()   # create placeholder
text_refresh.write(f"Page refreshed {st.session_state.refresh_count} times")

