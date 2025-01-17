import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
import random
import re
import base64
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_folium import folium_static
from datetime import datetime
from io import BytesIO
import pos_tagging as ps


def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data


def get_table_download_link(df, format, file_name):
    if format == "CSV":
        csv = df.to_csv(index=False)
        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(csv.encode()).decode()
        return f'<a href="data:file/csv;base64,{b64}" download="{file_name}.csv">Download CSV file</a>'
    elif format == "Excel":
        excel = to_excel(df)
        b64 = base64.b64encode(excel).decode()
        return f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}.xlsx">Download Excel file</a>'
    elif format == "JSON":
        json = df.to_json(orient='split')
        b64 = base64.b64encode(json.encode()).decode()
        return f'<a href="data:application/json;base64,{b64}" download="{file_name}.json">Download JSON file</a>'


def app():
    st.title('Tweets')
    # st.set_page_config(page_title='Bear Encounters in California')

    dataset = pd.read_csv('Social_Media_NLP/Step_5_Dashboard/final_data_tweets.csv')
    target_dataset = dataset.loc[dataset['label']==1]
    target_dataset['created_datetime'] = pd.to_datetime(target_dataset['created_datetime'], errors='coerce')
    target_dataset['date'] = target_dataset['created_datetime'].dt.date
    target_dataset['year'] = target_dataset['created_datetime'].dt.year
    target_dataset['month'] = target_dataset['created_datetime'].dt.month

    st.subheader(f'🐻 Bear Encounters in California 🌲')

    # Get user input
    # county_label = st.text_input('Enter a county label (optional)', help='eg. Riverside, San Francisco, Santa Clara')
    county_names = ['All', 'Alameda', 'Alpine', 'Amador', 'Butte', 'Calaveras', 'Colusa', 'Contra Costa', 'Del Norte',
                    'El Dorado', 'Fresno', 'Glenn', 'Humboldt', 'Imperial', 'Inyo', 'Kern', 'Kings', 'Lake',
                    'Lassen', 'Los Angeles', 'Madera', 'Marin', 'Mariposa', 'Mendocino', 'Merced', 'Modoc',
                    'Mono', 'Monterey', 'Napa', 'Nevada', 'Orange', 'Placer', 'Plumas', 'Riverside', 'Sacramento',
                    'San Benito', 'San Bernardino', 'San Diego', 'San Francisco', 'San Joaquin', 'San Luis Obispo',
                    'San Mateo', 'Santa Barbara', 'Santa Clara', 'Santa Cruz', 'Shasta', 'Sierra', 'Siskiyou',
                    'Solano', 'Sonoma', 'Stanislaus', 'Sutter', 'Tehama', 'Trinity', 'Tulare', 'Tuolumne',
                    'Ventura', 'Yolo', 'Yuba']

    county_label = st.selectbox('Select a county (optional)', county_names, help='eg. Riverside, San Francisco, Santa Clara')

    col1, col2 = st.columns(2)
    min_dt = datetime.strptime('2010-01-01', '%Y-%m-%d').date()
    max_dt = datetime.strptime('2022-12-31', '%Y-%m-%d').date()
    time_start = col1.date_input('Enter a start date (optional)', min_value=min_dt, max_value=max_dt, value=min_dt)
    time_start = '2010-01-01' if not time_start else str(time_start)
    time_end = col2.date_input('Select an end date (optional)', min_value=min_dt, max_value=max_dt, value=max_dt)
    time_end = '2022-12-31' if not time_end else str(time_end)


    # Filter dataset based on user input
    filtered_dataset = target_dataset.copy()
    if county_label != 'All':
        county_label = county_label.upper()
        filtered_dataset = filtered_dataset.loc[filtered_dataset['county'] == county_label]
    if time_start > '2010/01/01' or time_end < '2022/12/31':
        filtered_dataset = filtered_dataset.loc[(filtered_dataset['created_datetime'] >= time_start) & (filtered_dataset['created_datetime'] <= time_end)]
    filtered_data = filtered_dataset.to_dict(orient='records')


    # Download the result
    download_format = st.selectbox(f'Download the dataset of tweets in {county_label} between {time_start} and {time_end}', ['CSV', 'Excel', 'JSON'])
    file_name = f"{county_label}_{time_start}-{time_end}"
    if download_format is not None:
        st.markdown(get_table_download_link(filtered_dataset.drop(['Unnamed: 0'], axis=1), download_format, file_name),
                    unsafe_allow_html=True)
    st.write("<div style='height: 30px'></div>", unsafe_allow_html=True)


    # Display Tweets
    if len(filtered_dataset) > 0:
        num = min(10, len(filtered_dataset))
        random_texts = random.sample(filtered_dataset['content'].tolist(), k=num)
        text_block = '\n\n' + '\n\n'.join(
            ["- " + re.sub(r"http\S+|www\S+", "", ' '.join(text.split('/n'))) for text in random_texts])
        st.subheader(f'Sample tweets of Bear-encounters in {county_label} between {time_start} and {time_end}')
        st.markdown(
            f"<div style='height: 300px; overflow: scroll; background-color: rgb(244, 244, 244); padding: 10px;'>{text_block}</div>",
            unsafe_allow_html=True
        )
        st.markdown(f"<h6>Total number of records: {len(filtered_dataset)}</h6>", unsafe_allow_html=True)
        st.markdown("<h6>Data Source: Tweets from Twitter API</h6>", unsafe_allow_html=True)
        st.write("<div style='height: 30px'></div>", unsafe_allow_html=True)


        # Bear-encounter Frequency
        st.subheader(f'Frequency of Bear-encounters in {county_label} between {time_start} and {time_end}')
        yearly_count = filtered_dataset.groupby('year').size()
        seasonal_count = filtered_dataset.groupby('month').size()

        normalized_yearly_values = yearly_count.values / sum(yearly_count.values)
        marker_yearly = dict(
            color=normalized_yearly_values,
            colorscale='Earth',
            showscale=True,
            colorbar=dict(
                lenmode='fraction',
                len=0.4,
                x=1.05,
                y=0.88,
                title='Ratio'
            )
        )

        normalized_seasonal_values = seasonal_count.values / sum(seasonal_count.values)
        marker_seasonal = dict(
            color=normalized_seasonal_values,
            colorscale='Earth',
            showscale=True,
            colorbar=dict(
                lenmode='fraction',
                len=0.4,
                x=1.05,
                y=0.88,
                title='Ratio'
            )
        )

        fig = make_subplots(rows=1, cols=1)
        fig.add_trace(go.Bar(x=yearly_count.index, y=yearly_count.values, marker=marker_yearly), row=1, col=1)
        fig.update_xaxes(title_text='Year', row=1, col=1)
        fig.update_yaxes(title_text='Count', row=1, col=1)
        hover_template_year = 'Year: %{x}<br>Count: %{y}'
        fig.update_traces(hovertemplate=hover_template_year)
        fig.update_layout(
            title={
                'text': 'Yearly Bear Encounters',
                'y': 0.9,
                'x': 0.5,
                'font': {'size': 24},
                'xanchor': 'center',
                'yanchor': 'top'
            },
            plot_bgcolor='rgb(244, 244, 244)',
            paper_bgcolor='rgb(244, 244, 244)',
        )
        st.plotly_chart(fig)

        fig = make_subplots(rows=1, cols=1)
        fig.add_trace(go.Bar(x=seasonal_count.index, y=seasonal_count.values, marker=marker_seasonal), row=1, col=1)
        fig.update_xaxes(title_text='Month', row=1, col=1)
        fig.update_yaxes(title_text='Count', row=1, col=1)
        hover_template_month = 'Month: %{x}<br>Count: %{y}'
        fig.update_traces(hovertemplate=hover_template_month)
        fig.update_layout(
            title={
                'text': 'Seasonal Bear Encounters',
                'y': 0.9,
                'x': 0.5,
                'font': {'size': 24},
                'xanchor': 'center',
                'yanchor': 'top'
            },
            plot_bgcolor='rgb(244, 244, 244)',
            paper_bgcolor='rgb(244, 244, 244)'
        )
        st.plotly_chart(fig)
        st.write("<div style='height: 30px'></div>", unsafe_allow_html=True)


        # Bear-encounter map
        # Read shapefile
        ca_shapefile = 'Social_Media_NLP/Step_5_Dashboard/CA_Counties_TIGER2016.shp'
        gdf = gpd.read_file(ca_shapefile)

        # Define the CRS for the GeoDataFrame
        crs = 'EPSG:4326'

        # Set the CRS for the GeoDataFrame
        gdf = gdf.set_crs(crs)

        # Create a Folium map centered on California
        m = folium.Map(location=[36.7783, -119.4179], zoom_start=6)

        # Add California shapefile as a GeoJSON layer
        folium.GeoJson(gdf).add_to(m)

        for data in filtered_data:
            folium.CircleMarker(
                location=[data['latitude'], data['longitude']],
                radius=3,
                color='orange',
                fill=True,
                fill_color='orange',
                fill_opacity=0.8,
                popup=f"{data['date']}<br>lat: {data['latitude']:.1f}<br>lon: {data['longitude']:.1f}",
            ).add_to(m)
        st.subheader(f'Geographical Distribution of Bear-encounters in {county_label} between {time_start} and {time_end}')
        folium_static(m)

        # top 5 counties
        county_counts = target_dataset.loc[(target_dataset['created_datetime'] >= time_start) & (target_dataset['created_datetime'] <= time_end)]\
            ['county'].value_counts().sort_index()
        top_counties = sorted(county_counts.items(), key=lambda x: -x[1])[:5]

        # st.info(f"Top 5 counties with the highest number of bear encounters between {time_start} and {time_end}:")
        info_content = f"Top 5 counties with the highest number of bear encounters between {time_start} and {time_end}: \n\n" + \
                       "\n\n".join([f"- {county}: {count} encounters" for county, count in top_counties])
        st.info(info_content)
        st.write("<div style='height: 30px'></div>", unsafe_allow_html=True)


        # Compute sentiment scores
        sentiment_scores_1 = filtered_dataset['sentiment'].value_counts().sort_index()
        total_count = len(filtered_dataset)
        sentiment_ratios_1 = sentiment_scores_1 / total_count

        labels_1 = [f'{class_name} ({ratio:.1%})' for class_name, ratio in zip(sentiment_scores_1.index, sentiment_ratios_1)]
        sentiment_scores_1_sorted, labels_1_sorted = zip(*sorted(zip(sentiment_ratios_1, labels_1), key=lambda x: -x[0]))
        colors = ['#46859E', '#6998A5', '#DBDEC2', '#E2D8B1', '#D4C297', '#C8AF82', '#A67D48', '#996B35']
        fig1 = go.Figure(data=go.Pie(labels=labels_1_sorted, values=sentiment_scores_1_sorted, marker=dict(colors=colors)))
        fig1.update_traces(hovertemplate='%{label}')
        st.subheader(f'Sentiment Analysis of Bear-encounters in {county_label} between {time_start} and {time_end}')
        st.plotly_chart(fig1)


        # Word Cloud
        contents = ps.clear_text(filtered_dataset)
        noun_list, verb_list = ps.pos_tagging(contents)
        num = 50

        noun_freq = ps.count_words(ps.stemmer(noun_list)).head(num)
        noun_freq.index = noun_freq.index + 1

        verb_freq = ps.count_words(ps.stemmer(verb_list)).head(num)
        verb_freq.index = verb_freq.index + 1

        st.subheader(f'Top {len(noun_freq)} Nouns of Bear-encounters Tweets in {county_label} between {time_start} and {time_end}')
        st.markdown(
            f"<div style='height: 300px; overflow: scroll; background-color: rgb(244, 244, 244);'>{noun_freq.to_html(justify='left')}</div>",
            unsafe_allow_html=True
        )
        st.subheader(f'Top {len(verb_freq)} Verbs of Bear-encounters Tweets in {county_label} between {time_start} and {time_end}')
        st.markdown(
            f"<div style='height: 300px; overflow: scroll; background-color: rgb(244, 244, 244);'>{verb_freq.to_html(justify='left')}</div>",
            unsafe_allow_html=True
        )


    else:
        with st.container():
            st.warning(f"Oops! We don't have enough data points in {county_label} between {time_start} and {time_end}.")

