from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji
import re
from PIL import Image
import numpy as np
import nltk
from emot.emo_unicode import UNICODE_EMOJI, EMOTICONS_EMO
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import string

#URL extractor
def extract_urls(input_string):
    regex=r'\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b'
    matches = re.findall(regex, input_string)
    return matches

def fetch_stats(selected_user,df):

    if selected_user != 'All Users':
        df = df[df['user'] == selected_user]

    # fetch the number of messages
    num_messages = df.shape[0]

    # fetch the total number of words
    words = []
    for message in df['message']:
        words.extend(message.split())

    # fetch number of media messages
    num_media_messages = df[df['message'] == '<Media omitted>'].shape[0]

    # fetch number of links shared
    links = []
    for message in df['message']:
        links.extend(extract_urls(message))

    return num_messages,len(words),num_media_messages,len(links)

def most_busy_users(df):
    bleh = df[df['user'] != 'group_notification']
    bleh = bleh[bleh['message'] != '<Media omitted>']
    author_df = bleh["user"].value_counts().reset_index()
    author_df.rename(columns={"index":"Author", "user":"Number of messages"}, inplace=True)
    author_df["Total %"] = round(author_df["Number of messages"]*100/df.shape[0], 2)
    return author_df

def create_wordcloud(selected_user,df):

    f = open('stopwords.txt', 'r', encoding='utf-8')
    stop_words = f.read()

    if selected_user != 'All Users':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification']
    temp = temp[temp['message'] != '<Media omitted>']
    temp['message'] = temp['message'].apply(lambda x: re.split('https:\/\/.*', str(x))[0])

    def remove_stop_words(message):
        y = []
        for word in message.lower().split():
            if word not in stop_words:
                y.append(word)
        return " ".join(y)
    custom_mask = np.array(Image.open('cloud.jpg'))
    wc = WordCloud(width=500,height=500,min_font_size=10,max_font_size=175,background_color='white', mask=custom_mask, colormap='gist_rainbow_r')
                
    temp['message'] = temp['message'].apply(remove_stop_words)
    df_wc = wc.generate(temp['message'].str.cat(sep=" "))
    return df_wc

def emoji_helper(selected_user,df):
    if selected_user != 'All Users':
        df = df[df['user'] == selected_user]

    emojis = []
    for message in df['message']:
        emojis.extend([c for c in message if c in emoji.UNICODE_EMOJI['en']])

    emoji_df = pd.DataFrame(Counter(emojis).most_common(len(Counter(emojis))))
    emoji_df = emoji_df.rename(columns={0:'emoji',1:'count'})

    return emoji_df

def monthly_timeline(selected_user,df):

    if selected_user != 'All Users':
        df = df[df['user'] == selected_user]
    df = df[df['user'] != 'group_notification']
    timeline = df.groupby(['year', 'month_num', 'month']).count()['message'].reset_index()

    time = []
    for i in range(timeline.shape[0]):
        time.append(timeline['month'][i] + "-" + str(timeline['year'][i]))

    timeline['time'] = time

    return timeline

def week_activity_map(selected_user,df):

    if selected_user != 'All Users':
        df = df[df['user'] == selected_user]
    df = df[df['user'] != 'group_notification']
    return df['Days'].value_counts()

def week_strat_user(selected_user,df):
    bleh = df[df['user'] != 'group_notification']
    df2 = bleh.groupby(['Days','user'])['message'].count()
    df3 = df2.to_frame().reset_index()
    return df3

def month_strat_user(selected_user,df):
    if selected_user != 'All Users':
      df = df[df['user'] == selected_user]
    bleh = df[df['user'] != 'group_notification']
    df4 = bleh.groupby(['month','user'])['message'].count()
    df5 = df4.to_frame().reset_index()
    return df5

def activity_heatmap(selected_user,df):

    if selected_user != 'All Users':
        bleh = df[df['user'] == selected_user]
    else:
        bleh = df[df['user'] != 'group_notification']
    user_heatmap = bleh.pivot_table(index='Days', columns='hour', values='message', aggfunc='count').fillna(0)
    return user_heatmap

def df_to_plotly(df):
    return {'z': df.values.tolist(),
            'x': df.columns.tolist(),
            'y': df.index.tolist()} 

def convert_emojis(text):
    for emot in UNICODE_EMOJI:
        text = text.replace(emot, UNICODE_EMOJI[emot].replace(" ","_"))
    return text

def convert_emoticons(text):
    for emot in EMOTICONS_EMO:
        text = text.replace(emot, EMOTICONS_EMO[emot].replace(" ","_"))
    return text

def sentiment_preprocess(text):
  text = convert_emoticons(text)
  text = convert_emojis(text)
  text = text.replace("_", " ")
  text = text.replace(":"," ")
  text = text.translate(str.maketrans('','',string.punctuation))
  return text

def sentiment_analysis(selected_user,df):
    if selected_user != 'All Users':
        bleh = df[df['user'] == selected_user]
        bleh = bleh[bleh['message'] != '<Media omitted>']
    else:
        bleh = df[df['user'] != 'group_notification']
        bleh = bleh[bleh['message'] != '<Media omitted>']
    data = bleh.copy()
    data['message'] = data['message'].apply(lambda x: re.split('https:\/\/.*', str(x))[0])
    data["processed_message"] = data["message"].apply(lambda x: sentiment_preprocess(x))
    nltk.download('vader_lexicon')
    sentiments = SentimentIntensityAnalyzer()
    data["Positive"] = [sentiments.polarity_scores(i)["pos"] for i in data["processed_message"]]
    data["Negative"] = [sentiments.polarity_scores(i)["neg"] for i in data["processed_message"]]
    data["Neutral"] = [sentiments.polarity_scores(i)["neu"] for i in data["processed_message"]]
    sentiment = []
    for i in range(data.shape[0]):
        if data.iloc[i]['Positive'] > data.iloc[i]['Negative'] and data.iloc[i]['Positive'] > data.iloc[i]['Neutral']:
            largest = 'Positive'
        elif data.iloc[i]['Negative'] > data.iloc[i]['Positive'] and data.iloc[i]['Negative'] > data.iloc[i]['Neutral']:
            largest = 'Negative'
        elif data.iloc[i]['Neutral'] > data.iloc[i]['Positive'] and data.iloc[i]['Neutral'] > data.iloc[i]['Negative']:
            largest = 'Neutral'
        sentiment.append(largest)
    data['Sentiment'] = sentiment
    data = data[data['message'] != '']
    m = data[['user',"message", "Sentiment", "month", "year"]]
    df4 = m.groupby(['user','Sentiment'])['message'].count()
    df5 = df4.to_frame().reset_index()
    return m,df5

        
