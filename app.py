import requests
import os
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import time
import streamlit as st
from ast import literal_eval
import warnings
warnings.filterwarnings('ignore')       

st.set_page_config(
    page_title="Jakarta Air Quality Dashboard",
    page_icon="💨",
    layout="wide"
)

#css file
with open('style.css')as f:
 st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)

@st.cache_data(ttl="2h", persist=False)
def get_data():

    #get data
    lat = -6.1753942  #jkt coordinate
    lon = 106.827183
    API_key = st.secrets["api_key"] #api_key
    start_date = 1483203600 #01/01/2017 00:00:00
    end_date = int(time.mktime(datetime.now().timetuple()))
    url = f'http://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={start_date}&end={end_date}&appid={API_key}'

    result = requests.get(url).content

    datetime_list = []
    aqi_category_list = []
    co_list = []
    no_list = []
    no2_list = []
    o3_list = []
    so2_list = []
    pm25_list = []
    pm10_list = []
    nh3_list = []

    for item in literal_eval(result.decode('utf8'))['list']:
        datetime_list.append(item['dt'])
        aqi_category_list.append(item['main']['aqi'])
        co_list.append(item['components']['co'])
        no_list.append(item['components']['no'])
        no2_list.append(item['components']['no2'])
        o3_list.append(item['components']['o3'])
        so2_list.append(item['components']['so2'])
        pm25_list.append(item['components']['pm2_5'])
        pm10_list.append(item['components']['pm10'])
        nh3_list.append(item['components']['nh3'])

    data = pd.DataFrame({'datetime':datetime_list,
                        'AQI_category':aqi_category_list,
                        'CO':co_list,
                        'NO':no_list,
                        'NO2':no2_list,
                        'O3':o3_list,
                        'SO2':so2_list,
                        'PM2.5':pm25_list,
                        'PM10':pm10_list,
                        'NH3':nh3_list})
    
    #change unix datetime format
    data['datetime'] = data['datetime'].apply(lambda x: datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'))

    #change aqi category
    #1 = Good, 2 = Fair, 3 = Moderate, 4 = Poor, 5 = Very Poor.
    # Another conversion table (UK, USA, China) -> https://openweathermap.org/air-pollution-index-levels
    category = {1:"Good",
                2:"Fair",
                3:"Moderate",
                4:"Poor",
                5:"Very Poor"}

    data['AQI_category'] = data['AQI_category'].map(category)

    return data

df = get_data()
df['datetime'] = pd.to_datetime(df['datetime'])

#create dashboard title
st.header('Jakarta Air Quality Dashboard 💨')
st.markdown('\n')

ct_metrics = st.container()
with ct_metrics:

    #create metrics for each pollutant
    last_up, p1, p2, p3, p4, dt_filter  = st.columns([3,1,1,1,1,2])
    aqi_cat, p5, p6, p7, p8, download_data = st.columns([3,1,1,1,1,2])

    #datetime filter 
    with dt_filter:
        d = st.date_input(
            "Date Range",
            (datetime.date(df['datetime'].iloc[0]), datetime.date(df['datetime'].iloc[-1])),
            datetime.date(df['datetime'].iloc[0]),
            datetime.date(df['datetime'].iloc[-1]),
            format="MM.DD.YYYY",
            )
    
    #data filtered with date     
    df2 = df[(df['datetime'].dt.date>=d[0])&(df['datetime'].dt.date<=d[1])] 


    #download data 
    with download_data:
        csv = df2.to_csv().encode('utf-8')

        st.download_button(
        "📄 Download CSV",
        csv,
        "file.csv",
        "text/csv",
        key='download-csv'
        )

    #metrics
    with last_up:
        st.metric('Last Update',max(df2['datetime']).strftime("%a %d/%m/%Y %H:%M:%S"))

    with p1: #pm2.5
        delta_pm25 = round(df2['PM2.5'].diff().iloc[-1],2)
        st.metric("PM 2.5 (μg/m3)", df2['PM2.5'].iloc[-1], delta=delta_pm25, delta_color='inverse')

    with p2: #pm10
        delta_pm10 = round(df2['PM10'].diff().iloc[-1],2)
        st.metric("PM 10 (μg/m3)", df2['PM10'].iloc[-1], delta=delta_pm10, delta_color='inverse')

    with p3: #no
        delta_no = round(df2['NO'].diff().iloc[-1],2)
        st.metric("NO (μg/m3)", df2['NO'].iloc[-1], delta=delta_no, delta_color='inverse')

    with p4: #no2
        delta_no2 = round(df2['NO2'].diff().iloc[-1],2)
        st.metric("NO2 (μg/m3)", df2['NO2'].iloc[-1], delta=delta_no2, delta_color='inverse')

    with aqi_cat: #aqi category
        st.metric('AQI Category',df2['AQI_category'].iloc[-1])

    with p5: #co
        delta_co = round(df2['CO'].diff().iloc[-1],2)
        st.metric("CO (μg/m3)", df2['CO'].iloc[-1], delta=delta_co, delta_color='inverse')

    with p6: #so2
        delta_so2 = round(df2['SO2'].diff().iloc[-1],2)
        st.metric("SO2 (μg/m3)", df2['SO2'].iloc[-1], delta=delta_so2, delta_color='inverse')

    with p7: #o3
        delta_o3 = round(df2['O3'].diff().iloc[-1],2)
        st.metric("O3 (μg/m3)", df2['O3'].iloc[-1], delta=delta_o3, delta_color='inverse')

    with p8: #nh3
        delta_nh3 = round(df2['NH3'].diff().iloc[-1],2)
        st.metric("NH3 (μg/m3)", df2['NH3'].iloc[-1], delta=delta_nh3, delta_color='inverse')


st.markdown('\n')

line_title, pollutant, freq = st.columns([3,1,1])

tres = {'CO':12400, 'NO':100, 'NO2':150, 'O3':140,'SO2':250, 'PM2.5':50, 'PM10':100, 'NH3':200}

#line chart
def line_chart(df,x,y,xlabel,treshold):
    fig = px.line(df, x=x,y=y, markers=True, color_discrete_sequence=['#800016'])
    fig.update_layout(xaxis_title=None, plot_bgcolor='#FFFBFB',margin=dict(l=0,r=0,b=0,t=20), height=380)
    #fig.layout.xaxis.fixedrange = True
    #fig.layout.yaxis.fixedrange = True
    fig.update_yaxes(title=f'Concentration of {y} (μg/m3)', gridcolor='#C46B6B',title_font=dict(size=18),tickfont_size=15)
    fig.update_xaxes(title=xlabel,title_font=dict(size=18), tickfont_size=15)
    
    #poor limit
    #fig.add_hrect(y0=treshold, y1=df[y].max()+10, line_width=0, fillcolor="#FFD7DE", opacity=0.3, layer='below')
    
    fig.add_hline(y=treshold,
              line_dash='dash', 
              line_color='black', 
              annotation_text= f'Poor limit of {y} = {treshold} μg/m3',
              annotation_position='top right', 
              annotation_font_color='black',
              annotation_bgcolor="white")

    return fig

#last 24 hours
if freq_opt=='Last 24 Hours':
    df3 = df2[df2['datetime'].dt.date == df2['datetime'].dt.date.iloc[-1]][[pol_opt,'datetime']].rename(columns={'datetime':'Date Time'})
    #replace negative outlier with 0
    pol = df3._get_numeric_data()
    pol[pol<0] = 0

    fig = line_chart(df3, 'Date Time',pol_opt,"Hour", tres[pol_opt])
    st.plotly_chart(fig, use_container_width=True)

#daily
elif freq_opt=='Daily Grouped':
    df3 = df2[[pol_opt,'datetime']]
    #replace negative outlier with 0
    pol = df3._get_numeric_data()
    pol[pol<0] = 0

    df3 =  df3.resample('D',on='datetime').mean().round(2).reset_index()
    df3 = df3.rename(columns={'datetime':'Date'})
    fig = line_chart(df3, 'Date',pol_opt,"Date", tres[pol_opt])
    st.plotly_chart(fig, use_container_width=True)

#hourly
elif freq_opt=='Hourly Grouped':
    df3 = df2[[pol_opt,'datetime']]
    #replace negative outlier with 0
    pol = df3._get_numeric_data()
    pol[pol<0] = 0

    df3['Hour'] = df3['datetime'].dt.hour
    df3 = df3[[pol_opt,'Hour']].groupby('Hour').mean().round(2).reset_index()
    fig = line_chart(df3,'Hour',pol_opt,"Hour", tres[pol_opt])
    st.plotly_chart(fig, use_container_width=True)

#day of week
elif freq_opt=='Day of Week Grouped':
    df3 = df2[[pol_opt,'datetime']]
    #replace negative outlier with 0
    pol = df3._get_numeric_data()
    pol[pol<0] = 0

    df3['Day Name'] = df3['datetime'].dt.day_name()
    df3['day'] = df3['datetime'].dt.dayofweek
    df3 = df3[[pol_opt,'Day Name','day']].groupby(['day','Day Name']).mean().round(2).reset_index().sort_values('day',ascending=True)
    fig= line_chart(df3, 'Day Name', pol_opt,"Day of Week", tres[pol_opt])
    st.plotly_chart(fig, use_container_width=True)

#monthly
elif freq_opt=='Monthly Grouped':
    df3 = df2[[pol_opt,'datetime']]
    #replace negative outlier with 0
    pol = df3._get_numeric_data()
    pol[pol<0] = 0
    
    df3['Month Year'] = df3['datetime'].dt.strftime('%Y-%m')
    df3 = df3[[pol_opt,'Month Year']].groupby(['Month Year']).mean().round(2).reset_index()
    fig= line_chart(df3, 'Month Year', pol_opt,"Year Month", tres[pol_opt])
    st.plotly_chart(fig, use_container_width=True)

#realtime
else:
    df3 = df2[[pol_opt,'datetime']]
    #replace negative outlier with 0
    pol = df3._get_numeric_data()
    pol[pol<0] = 0

    df3 = df3.rename(columns={'datetime':'Datetime'})
    fig= line_chart(df3, 'Datetime', pol_opt,"Datetime", tres[pol_opt])
    st.plotly_chart(fig, use_container_width=True)

#pivot table (heatmap)
st.markdown("\n")
st.markdown(f"### Average Concentration of {pol_opt} Grouped by Hour and Day")

df3 = df2[[pol_opt,'datetime']]
#replace negative outlier with 0
pol = df3._get_numeric_data()
pol[pol<0] = 0

df3['Hour'] = df3['datetime'].dt.hour
df3['Day of Week'] = df3['datetime'].dt.day_name()
pivot = pd.pivot_table(df3, values=pol_opt, columns="Hour", index="Day of Week", aggfunc='mean').round(2)

day_dict={'Sunday':0,'Monday':1,'Tuesday':2,'Wednesday':3,'Thursday':4,'Friday':5,'Saturday':6}
pivot = pivot.sort_values('Day of Week', key=lambda x: x.map(day_dict), ascending=True)
hm = px.imshow(pivot, aspect='auto', text_auto=True, color_continuous_scale=["#F2EEEE","#A13A49","#800016"])
hm.update_yaxes(title_font=dict(size=18),tickfont_size=15)
hm.update_xaxes(title_font=dict(size=18),tickfont_size=15)
hm.update_layout(margin=dict(l=0,r=0,b=0,t=20))
st.plotly_chart(hm, use_container_width=True)

st.markdown('\n')
st.markdown('Created by Subkhan Rian Romadhon (2023) | Data Source: openweathermap')
