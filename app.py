import re
import io
import string
import helper
import pandas as pd
import seaborn as sns
import streamlit as st
import plotly.express as px
from st_aggrid import AgGrid
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.graph_objects as go

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

st.sidebar.title("WhatsApp Chat Analyzer")
st.sidebar.markdown('**Creator:** Luke Chugh')
#Clock Format
clock_format = st.sidebar.selectbox('Select clock format of your device:', ['12 hour (AM/PM)', '24 hour'])
date_format = st.sidebar.selectbox('Select date format of your device:', ['dd/mm/yyyy', 'mm/dd/yyyy', 'yyyy/mm/dd'])

sample_file_path = "./sample_chat.txt"
use_sample_file = st.sidebar.checkbox("Use Sample WhatsApp Chat File", value=False)
if use_sample_file:
    with open(sample_file_path, 'rb') as file:
        uploaded_file = io.BytesIO(file.read())
        st.sidebar.markdown('<p style="font-size: 16px;">Reload to upload exported chat</p>', unsafe_allow_html=True)
else:
    uploaded_file = st.sidebar.file_uploader("Upload WhatsApp exported chat in .txt format:", type=["txt"])

def preprocess(data, clock_format='12 hour (AM/PM)', date_format='dd/mm/yyyy'):
    # Normalize non-breaking spaces to regular spaces
    data = data.replace('\u202F', ' ')

    # Define format and pattern based on user input
    if clock_format == '12 hour (AM/PM)':
        if date_format == 'dd/mm/yyyy':
            formats = ['%d/%m/%Y, %I:%M %p - ', '%d/%m/%y, %I:%M %p - ']
        elif date_format == 'mm/dd/yyyy':
            formats = ['%m/%d/%Y, %I:%M %p - ', '%m/%d/%y, %I:%M %p - ']
        elif date_format == 'yyyy/mm/dd':
            formats = ['%Y/%m/%d, %I:%M %p - ', '%y/%m/%d, %I:%M %p - ']
        pattern = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s[AaPp][Mm]\s-\s'
    else:
        if date_format == 'dd/mm/yyyy':
            formats = ['%d/%m/%Y, %H:%M - ', '%d/%m/%y, %H:%M - ']
        elif date_format == 'mm/dd/yyyy':
            formats = ['%m/%d/%Y, %H:%M - ', '%m/%d/%y, %H:%M - ']
        elif date_format == 'yyyy/mm/dd':
            formats = ['%Y/%m/%d, %H:%M - ', '%y/%m/%d, %H:%M - ']
        pattern = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s'

    # Split the messages and dates
    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)
    df = pd.DataFrame({'user_message': messages, 'message_date': dates})
    
    # Parse date strings
    parsed_dates = []
    for date in df['message_date']:
        for fmt in formats:
            try:
                parsed_dates.append(datetime.strptime(date, fmt))
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Date string {date} does not match any known format.")
    
    df['date'] = parsed_dates

    # Extract user and message content
    users = []
    messages = []
    for message in df['user_message']:
        entry = re.split(r'([\w\W]+?):\s', message)
        if entry[1:]:
            users.append(entry[1])
            messages.append(entry[2])
        else:
            users.append('group_notification')
            messages.append(entry[0])
    
    df['user'] = users
    df['message'] = messages
    df['message'] = df['message'].replace(r'\n', '', regex=True) 
    df.drop(columns=['user_message', 'message_date'], inplace=True)
    
    # Extract date components
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['Days'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute
    df['only_date'] = df['date'].dt.date
    
    return df

if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    data = bytes_data.decode('utf-8')
    df = preprocess(data)
    # Fetch Users
    user_list = df['user'].unique().tolist()
    user_list.remove('group_notification')
    user_list.sort()
    user_list.insert(0, 'All Users')
    selected_user = st.sidebar.selectbox('Show Analysis With Respect to:', user_list)
    # Start Analysis
    if st.sidebar.button("Show Analysis"):

        # Stats Area
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user,df)

        # To Show name of the group as title
        #name = uploaded_file.name
        #name = name.split('WhatsApp Chat with ')
        #name = name[1]
        #st.title(name[:-4])
        
        st.title("Top Statistics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.header("Total Messages")
            st.title(num_messages)
        with col2:
            st.header("Total Words")
            st.title(words)
        with col3:
            st.header("Media Shared")
            st.title(num_media_messages)
        with col4:
            st.header("Links Shared")
            st.title(num_links)

        # monthly timeline
        st.title("Monthly Timeline")
        timeline = helper.monthly_timeline(selected_user,df)
        fig = go.Figure(data=go.Scatter(x=timeline['time'], y=timeline['message'],mode='lines+markers', line_color="#0000ff"))
        fig.update_layout(yaxis_title="<b>Number of messages</b>",font=dict(family="Courier New, monospace",size=18, color="black"),width=900, height=600)
        st.plotly_chart(fig)

        # activity map
        st.title('Activity Map')
        col1,col2 = st.columns(2)
        
        if selected_user == 'All Users':
            st.header("Most busy day")
            busy_day = helper.week_strat_user(selected_user, df)
            fig = px.bar(busy_day, x="Days", y="message", color="user",pattern_shape="user",labels={"message": "<b>Number of messages</b>", "Days": "<b>Days of the week</b>"})
            fig.update_layout(showlegend=True, width=800, height=600)
            st.plotly_chart(fig)

            st.header("User activity per month")
            busy_month = helper.month_strat_user(selected_user, df)
            fig = px.line_polar(busy_month, r="message", theta="month", color='user', line_close=True,color_discrete_sequence=px.colors.qualitative.Light24)
            fig.update_layout(showlegend=True, width=650, height=650, margin=dict(l=100, r=20, t=20, b=20))
            st.plotly_chart(fig)

        else:
            st.header("Most busy day")
            busy_day = helper.week_activity_map(selected_user,df)
            new_df = busy_day.to_frame().reset_index()
            fig = px.bar(new_df, x='index', y='Days',color='index',pattern_shape="index",labels={"Days": "<b>Number of messages</b>", "index": "<b>Days of the week</b>"})   
            fig.update_layout(showlegend=False) 
            st.plotly_chart(fig)
            
            st.header("Most busy month")
            busy_month = helper.month_strat_user(selected_user,df)
            fig = px.line_polar(busy_month, r="message", theta="month", color='user', line_close=True,color_discrete_sequence=px.colors.qualitative.Light24)
            fig.update_traces(fill='toself')
            fig.update_layout(showlegend=False, width=600, height=600)
            st.plotly_chart(fig)

        st.title("Weekly Activity Map")
        layout = go.Layout(title = 'z = Number of messages', title_x=0.5,
                  yaxis={"title": '<b>Days of the week</b>'},
                  width=800,
                  height=600,
                  xaxis={"title": '<b>Time period in 24 hour format</b>',"tickangle": 30}, 
                  xaxis_nticks = 25,xaxis_showgrid=True, yaxis_showgrid=True)
        fig = go.Figure(data=go.Heatmap(helper.df_to_plotly(helper.activity_heatmap(selected_user,df))),layout=layout)
        st.plotly_chart(fig)

        # finding the busiest users in the group(Group level)
        if selected_user == 'All Users':
            st.title('Most Busy Users')
            author_df = helper.most_busy_users(df)
            fig = go.Figure()
            labels = author_df["Author"].values
            parents = []
            fig.add_trace(go.Treemap(labels = labels, parents = [""]*len(labels),values =  author_df["Number of messages"].values, 
                         textinfo = "label+value+percent parent",textfont={'size':14},meta={"title.text":"Hi"}))
            fig.update_layout(title_text="Total Messages: "+ str(df.shape[0]), font_size=20, title_x=0.5,width=900, height=600)
            st.plotly_chart(fig)

        # WordCloud
        st.title("Wordcloud")
        df_wc = helper.create_wordcloud(selected_user,df)
        fig,ax = plt.subplots()
        plt.axis("off")
        plt.tight_layout(pad=0)
        ax.imshow(df_wc)
        st.pyplot(fig)

        # emoji analysis
        emoji_df = helper.emoji_helper(selected_user,df)
        
        st.title("Emoji Analysis")
        if emoji_df.shape == (0,0):
            st.write("No emoji found")
        else:
            fig = px.pie(emoji_df.head(20), values='count', names='emoji')
            fig.update_traces(hoverinfo='label+percent', textinfo='label+value', showlegend=False)              
            st.plotly_chart(fig)

        # sentiment analysis
        st.title("Sentiment Analysis")
        dataframe,df5 = helper.sentiment_analysis(selected_user,df)
        st.write('Move the slider or to see the sentiment analysis of the messages')
        AgGrid(dataframe)
        if selected_user == 'All Users':
            st.header("Overall distribution of sentiments")
            fig = go.Figure(data=[go.Pie(labels=df5['Sentiment'], values=df5['message'], hole=.5)])
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(showlegend=False, width=600, height=600,annotations=[dict(text='Sentiment Analysis', x=0.5, y=0.5, font_size=20, showarrow=False)]) 
            st.plotly_chart(fig)
            
            st.header("Sentiments stratified by user")
            fig = px.bar(df5, x="Sentiment", y="message", color="user",pattern_shape="user",labels={"message": "<b>Number of messages</b>", "Sentiment": "<b>Sentiments</b>"})
            fig.update_layout(showlegend=True, width=800, height=600)
            st.plotly_chart(fig)
        else:
            st.header("Overall distribution of sentiments")
            fig = go.Figure(data=[go.Pie(labels=df5['Sentiment'], values=df5['message'], hole=.5)])
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(showlegend=False, width=600, height=600,annotations=[dict(text='Sentiment Analysis', x=0.5, y=0.5, font_size=20, showarrow=False)]) 
            st.plotly_chart(fig)
