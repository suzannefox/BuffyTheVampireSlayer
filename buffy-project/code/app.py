import buffy_functions as bf
import streamlit as st

import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# --- get data ---
df = bf.get_buffydata_from_wikipedia('../data/Episode Information.txt')
fig_buffy = bf.plot_buffy_viewers(df)
list_writers, list_directors = bf.get_filmakers(df)

# --- state variables ---
if 'refresh_count' not in st.session_state:
    st.session_state.refresh_count = 0
if 'last_writer' not in st.session_state:
    st.session_state.last_writer = None
if 'last_director' not in st.session_state:
    st.session_state.last_director = None
if 'last_change' not in st.session_state:
    st.session_state.last_change = None

# --- Row 1 ---
row1 = st.container()
with row1:
    st.subheader("Episode explorer")
    text_source = st.empty()   # create placeholder
    text_source.write('Data sourced from Wikipedia: [Buffy the Vampire Slayer episode guide](https://en.wikipedia.org/wiki/List_of_Buffy_the_Vampire_Slayer_episodes)')
    col1, col2 = st.columns([3, 1])  # wider plot column

    with col2:

        st.subheader("Filters")
        text_info = st.empty()   # create placeholder

        options = ["Select a writer..."] + list(list_writers.keys())
        selected_writer = st.selectbox(
            'Writers',
            options=options,
            key='writer',
            index=0,
            format_func=lambda w: w if w == "Select a writer..." else f"{w} ({list_writers[w]})"
        )
        if st.session_state.last_writer != selected_writer:
            st.session_state.last_writer = selected_writer
            st.session_state.last_change = 'writer'

        options = ["Select a director..."] + list(list_directors.keys())
        selected_director = st.selectbox(
            'Directors',
            options=options,
            key='director',
            index=0,
            format_func=lambda d: d if d == "Select a director..." else f"{d} ({list_directors[d]})"
        )
        if st.session_state.last_director != selected_director:
            st.session_state.last_director = selected_director
            st.session_state.last_change = 'director'

        if st.session_state.refresh_count == 0:
            text_info.write('No filter applied')
        else:
            text_info.write(f'Filtering by {st.session_state.last_change} = {st.session_state.last_writer if st.session_state.last_change == "writer" else st.session_state.last_director}')

        with col1:

            # first render: no prior selection action yet
            filter_var = st.session_state.last_change
            if filter_var == 'writer':
                filter_value = st.session_state.last_writer
            elif filter_var == 'director':
                filter_value = st.session_state.last_director
            print(filter_var, filter_value)

            fig = bf.filter_plot(fig_buffy, df, filter_var, filter_value)
            st.plotly_chart(fig, use_container_width=True)

# --- Row 3 (full width) ---
st.divider()
st.session_state.refresh_count +=1

text_refresh = st.empty()   # create placeholder
text_refresh.write(f"Page refreshed {st.session_state.refresh_count} times")

