import pandas as pd
from datetime import datetime
from collections import Counter
from itertools import count
import plotly.express as px
import plotly.graph_objects as go
import copy
import re

# Define the regex pattern to match the line format and capture the relevant fields
# Of the semi-structured text data downloaded from Wikipedia - 
# https://en.wikipedia.org/wiki/List_of_Buffy_the_Vampire_Slayer_episodes

def test():
    print("RUNNING TEST MSG")
    return 56

# read a line from the suppied file and parse it using the regex pattern, returning a dictionary of the captured fields
# this regex pattern captures the following groups:
# n1, n2, n3: the three numbers at the start of the line
# quoted: the quoted text (episode title)
# text1 and text1b: the two text fields separated by a tab (director and writer)
# date: the date in the format "Month Day, Year"  
# value: the numeric value at the end of the line (viewers in millions)
# ref: the optional reference in square brackets (not used in this code but captured for  
def _parse_line(line):
    """Parse a line from the text data file and return a dictionary of the captured fields."""

    pattern = re.compile(
        r"""
        ^\s*
        (?P<n1>\d+)\s+
        (?P<n2>\d+)\s+
        (?P<n3>\d+)\s+
        "(?P<quoted>[^"]+)"\s+
        (?P<text1>[^\t]*)\t(?P<text1b>[^\t]*)\s+
        (?P<date>[A-Za-z]+\s+\d{1,2},\s+\d{4})\s+
        (?P<value>\d+(?:\.\d+)?)
        (?P<ref>\[\d+\])?
        $
        """,
        re.VERBOSE
    )

    m = pattern.match(line)
    if not m:
        return None  # or raise error

    d = m.groupdict()

    # Convert types
    d["n1"] = int(d["n1"])
    d["n2"] = int(d["n2"])
    d["n3"] = int(d["n3"])
    d["date"] = datetime.strptime(d["date"], "%B %d, %Y")

    return d

# get the dataframe from the file
# file must be structured according to the regex definition above, 
# which is the format of the text data downloaded from Wikipedia
# https://en.wikipedia.org/wiki/List_of_Buffy_the_Vampire_Slayer_episodes
def get_buffydata_from_wikipedia(filename):
    """Return a dataframe of Buffy the Vampire Slayer episode data from a text file downloaded from Wikipedia."""

    # read the text and create a pandas dataframe
    header = []
    rows = []

    with open(filename) as f:
        for lineno, line in enumerate(f, start=1):
            if lineno == 1:
                header = line.split()
                header.append('Junk')  # add an extra column for the junk at the end of the line
                continue

            parsed = _parse_line(line)
            if parsed:
                rows.append(parsed)

    # convert to a pandas df
    df = pd.DataFrame(rows)
    # set the column names
    df.columns = header
    # drop the Junk column
    df = df.drop(columns=["Junk"])
    # make sure Viewers is numeric, coercing errors to NaN
    df["Viewers"] = pd.to_numeric(df["Viewers"], errors="coerce")
    # make sure release dat is just a date, not a datetime, by converting to datetime and then taking the date part
    df["Release"] = pd.to_datetime(df["Release"]).dt.date

    return(df)

# get meta data for each series, supply the main adversary, the colour to use for the plot, 
# from the data get the start episode number and a formatted tick label for the x axis
def _buffy_series_metadata(df):
    """Define some Series metadata and get start episode number and formatted tick label for each series from the data, 
       returning a dictionary of all the series-related data that we need for the plot."""

    # Define lists for series, adversaries and colors
    list_series = [1,2,3,4,5,6,7]
    list_adversaries = ["The Master", "Angelus", "Mayor Wilkins", "Adam", "Glorificus", "The Trio", "The First"]
    list_colours = ['orange', 'green', 'blue', 'brown', 'red', 'purple', 'grey']

    # find the start and end episode numbers for each series, and the start date of each series
    series_starts = (
        df.groupby("Series")
        .agg(
            start_ep=("Number", "min"),
            final_ep=("Number", "max"),
            start_date=("Release", "min"),
        )
        .reset_index()
        .sort_values("Series")
    )

    # build the tick text from the start and end episode numbers and the start date, 
    # using HTML formatting to create a multi-line label
    series_starts["tick"] = (
        "Ep. "
        + series_starts["start_ep"].astype(str)
        + "-"
        + series_starts["final_ep"].astype(str)
        + "<br>"
        + pd.to_datetime(series_starts["start_date"]).dt.strftime("%B %Y")
    )

    list_start_ep = series_starts["start_ep"].tolist()
    list_ticks = series_starts["tick"].tolist()

    # create a dictionary of all the series-related data that we need for the plot, 
    # using a dictionary comprehension to combine the lists into a single dictionary
    series_info = {
        s: {"adversary": a, "colour": c, "start_ep": d, "tick": t}
        for s, a, c, d, t in zip(list_series, list_adversaries, list_colours, list_start_ep, list_ticks)
    }

    return(series_info)

# create the plot of viewers per episode, with vertical bands for each series, 
# using the series metadata for the band colours and annotations, and custom x axis ticks
def plot_buffy_viewers(df):
    """Create a Plotly line chart of Buffy the Vampire Slayer episode viewers, with vertical bands for each series"""

    # get the series information
    series_info = _buffy_series_metadata(df)

    # Define lists for series, adversaries, hover text, and colors
    list_hover = ["Series", "Episode", "Title"]

    # y axis limits with some padding
    ymin = df["Viewers"].min() - 1
    ymax = df["Viewers"].max() + 2 

    # Step 1. Basic chart
    fig = px.line(
        df,
        x="Number",
        y="Viewers",
        title = 'Viewers per Episode - Click on a marker for episode details',
        labels = {"Number": "Episode Number and Release Date", 
                "Viewers": "Viewers (millions)"},
        custom_data = list_hover, # for use later in a custom hover template
        range_y=[ymin, ymax]
    )

    # Step 2. Add vertical bands for each series, with annotations
    for series in series_info:
        group = df[df["Series"] == series]
        
        xmin = group["Number"].min()
        xmax = group["Number"].max()
        
        fig.add_vrect(
            x0=xmin,
            x1=xmax,
            fillcolor = series_info[series]['colour'],
            opacity=0.1,
            line_width=0,
            annotation_text= f"Series {series}<br>{series_info[series]['adversary']}", # Format as HTML
            annotation_position="inside top", # Positions the text
        )

    # Step 3. Customise x axis ticks
    fig.update_xaxes(
        tickmode='array',
        tickvals=[series_info[series]['start_ep'] for series in series_info], # Use the tick positions from the series info
        ticktext=[series_info[series]['tick'] for series in series_info],
        tickangle=0.1
    )

    # Step 4. Customise hover template, line and marker style
    fig.update_traces(
        mode="lines+markers",
        marker=dict(size=8, color='#FFDFA8', opacity=0.6, line=dict(width=2, color='purple')),
        selected=dict(marker=dict(opacity=0.6)),
        unselected=dict(marker=dict(opacity=0.6)),
        line_color='#786FB0', line_width=1,
        hovertemplate = "Episode %{customdata[0]}-%{customdata[1]} : %{customdata[2]}"
    )

    # Step 5. Customise overall layout
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",

        hoverlabel=dict(
            bgcolor="white",
            font_size=14
        )
    )

    return(fig)

# ammend the plot to highlight the episodes that match the filter criteria, with a custom hover template showing the series, 
# episode number and title
def filter_plot(fig, df, filter_var, filter_value):
    """Add a trace to the Buffy Series plot highlighting episodes that match the filter criteria"""
    fig2 = copy.deepcopy(fig)

    if filter_var == 'writer' and filter_value == 'Select a writer...':
        return(fig2)
    if filter_var == 'director' and filter_value == 'Select a director...':
        return(fig2)

    list_hover = ["Series", "Episode", "Title"]

    if filter_var == 'director':
        df_highlight = df[df["Director"].str.contains(filter_value, case=False, na=False)]
    elif filter_var == 'writer':
        df_highlight = df[df["Writer"].str.contains(filter_value, case=False, na=False)]


    fig2.add_trace(
        go.Scatter(
            x=df_highlight["Number"],
            y=df_highlight["Viewers"],
            mode="markers",
            marker=dict(color="red", size=15, opacity=0.6),
            selected=dict(marker=dict(opacity=0.6)),
            unselected=dict(marker=dict(opacity=0.6)),
            customdata=df_highlight[list_hover],
            hovertemplate = "Episode %{customdata[0]}-%{customdata[1]} : %{customdata[2]}",
            name=f"",
            showlegend=False,
        )
    )

    return(fig2)

# supply a text string containing the writer(s) or director(s) of an episode, and return a cleaned version 
# of the string with extra text and formatting removed, ready for counting, individuals are delimited by &
def _clean_names(name):
    """Return a list of names cleaned of extra text and formatting, ready for counting."""
    name = name.replace('"','')
    name = name.replace('Story by : ','')
    name = name.replace('Teleplay by : ','& ')
    return(name)

# return two person based lists of writers and directors with how many episodes they worked on, using the 
# Counter class to count the occurrences of each name in the cleaned lists
def get_filmakers(df):
    """Return two person based lists of writers and directors with how many episodes they worked on"""
    list_writers_orig = df['Writer'].to_list()
    list_directors_orig = df['Director'].to_list()

    # writers
    list_writers_orig = df['Writer'].to_list()
    list_writers_clean = [_clean_names(name) for name in list_writers_orig]
    list_writers_unique = []
    for item in list_writers_clean:
        parts = item.split("&")
        for p in parts:
            list_writers_unique.append(p.strip())

    list_writers = Counter(list_writers_unique)
    list_writers = dict(list_writers.most_common())

    # directors
    list_directors = Counter(list_directors_orig)
    list_directors = dict(list_directors.most_common())

    return(list_writers, list_directors)

# get details for an episode given the episode number, returning a dictionary of the details for that episode, 
# or None if the episode number is not found
def get_episode_details(df, episode_number):
    """Return a dictionary of details for the specified episode number."""
    episode = df[df["Number"] == episode_number]
    if episode.empty:
        return None
    
    episode_detail =  episode.to_dict(orient="records")[0]
    episode_text = f"Episode {episode_detail['Series']}-{episode_detail['Episode']} : {episode_detail['Title']} <br>" \
                    f"Director: {episode_detail['Director']} <br>" \
                    f"Writer: {episode_detail['Writer']} <br>" \
                    f"Release Date: {episode_detail['Release']} <br>" \
                    f"Viewers: {episode_detail['Viewers']}"
    return(episode_text)