import tweepy, os, sqlite3, click
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from RedditStockTickers import top_ticker_symbols, get_wsb_tickers, stock_sentimental_analysis
from dotenv import find_dotenv, load_dotenv
from collections import Counter
from datetime import datetime
import yfinance as yf

load_dotenv(find_dotenv(r".env.txt"))

sid_obj = SentimentIntensityAnalyzer() #NLTK Vader Analysis

date =(datetime.now()).strftime("%B_%Y")#Get the date for today to add it into the database

@click.command()
@click.argument("Stock info")#Added a cli command to get information from CLI.
def get_stock_data(top_ticker_symbols):
    stock = yf.Ticker(top_ticker_symbols) #Gets the stock price of the ticker
    if len(stock.info["logo_url"]) == 0:
        Stock_Value = stock.info["regularMarketPrice"]
    else:
        Stock_Value = stock.info["currentPrice"]
    return Stock_Value
    click.ech("Getting stock prices....")

@click.command()
@click.argument("Data_set")
def twitter_sentimental_analysis(top_ticker_symbols):
    negative_list = []
    positive_list = []
    total_mentions = []
    auth = tweepy.OAuthHandler(os.getenv("twitter_api_key"), os.getenv("twitter_api_key_secret"))#Authentication for Twitter
    auth.set_access_token(os.getenv("twitter_api_token"), os.getenv("twitter_api_secret"))#initialize the token for to get information on the twitter API
    api = tweepy.API(auth) #Login to the twitter API
    sorted_list = sorted(dict(Counter(top_ticker_symbols)), key = dict(Counter(top_ticker_symbols)).get, reverse = True)[:10] #gets the top stocks from a subreddit
    for stock_tickers in sorted_list:
        for tweet in tweepy.Cursor(api.search_tweets, q = f"${stock_tickers}  -filter:retweets", lang = "en").items(100): #Retrieves retweets from Twitter
            no_emoji_tweet = tweet.text.encode("ascii", "ignore").decode("utf8") #ignore emoji's in the tweets
            sentiment_dict = sid_obj.polarity_scores(no_emoji_tweet) #Uses the Vader library and inputs the retweets inside
            if stock_tickers in no_emoji_tweet: #If the ticker is insite the retweet, it will append it to the total list for Twitter and give it a negative or positive score
                total_mentions.append(stock_tickers)
                if sentiment_dict["compound"] >= 0.05:
                    positive_list.append(stock_tickers)
                elif sentiment_dict["compound"] <=-.05:
                    negative_list.append(stock_tickers)
    positive_twitter_symbol = dict(Counter(positive_list)) #Turns the ticker into a dictionary and counts the total positive retweets
    negative_twitter_symbol = dict(Counter(negative_list)) #Turns the ticker into a dictionary and counts the total negative retweets
    total_twitter_mention = dict(Counter(total_mentions)) #Gets the total number of tweets
    click.echo("Dataset has been created") #When accessing this script from the CLI, it will let you know once it gets the database and shows the information in the CLI
    click.echo(f"""Positive Twitter Sentimental Analysis:{positive_twitter_symbol},
        Negative Twitter Sentimental Analysis: {negative_twitter_symbol},
        Total Mention of Stocks on Twitter: {total_twitter_mention}
        """)
    return positive_twitter_symbol, negative_twitter_symbol, total_twitter_mention




@click.command()
@click.argument("dataset")#Lets the user create the database within the CLI
def add_stocks_to_db(date, reddit_total_mentions, stock_sentimental_positive, stock_sentimental_negative, total_mentions, positive, negative):
    conn = sqlite3.connect("Twitter_Reddit.db")#Creates a dataset in a db format
    ticker_table = conn.cursor()
    ticker_table.execute(f"""CREATE TABLE IF NOT EXISTS STOCK_TICKERS_{date}# If the table does not exists, it creates a new table
        (Stock_Ticker TEXT,
        Stock_Price INTEGER,
        Reddit_Total_Mentions INTEGER,
        Reddit_Positive_Mentions Integer,
        Reddit_Negative_Mentions INTEGER,
        Twitter_Total_Mentions Integer,
        Twitter_Positive_Mentions  INTEGER,
        Twitter_Negative_Mentions INTEGER);""")
    sorted_list = sorted(reddit_total_mentions, key = reddit_total_mentions.get, reverse = True)[:10] #Goes through a sorted list 
    for stock_ticker in sorted_list:
        stock_price = get_stock_data(stock_ticker)
        temp_tuple = (reddit_total_mentions, stock_sentimental_positive, stock_sentimental_negative, total_mentions, positive, negative) #Creates a tuple to see if a stock ticker is in the each table
        for values in temp_tuple:  #If a stock ticker is not mentioned at all within Twitter or Reddit. it will then make the totalvalue or the sentimental value equal to 0
            if (stock_ticker in values) == False:
                values[stock_ticker] = 0
        data = ticker_table.execute(f"SELECT * FROM STOCK_TICKERS_{date}") #We then get the dataset from the table itself
        check_data = data.fetchall()
        if len(check_data) == 0: #If the dataset is completely empty, it will add in a fresh new data.
            key_word = "add"
        else: #If it is not empty, it will check to see if any of the stock needs to be added in or updated.
            for stocks in check_data:
                print(stocks)
                if stocks[0] == stock_ticker:
                    key_word = "update"
                elif stocks[0] == stock_ticker:
                    key_word = "add"
        if key_word == "update": #If the stock ticker is already in the table, it will update the current values.
            ticker_table.execute(f"""UPDATE STOCK_TICKERS_{date} SET
                    Stock_Price = {stock_price},
                    Reddit_Total_Mentions = Reddit_Total_Mentions + ?,
                    Reddit_Positive_Mentions = Reddit_Positive_Mentions + ?,
                    Reddit_Negative_Mentions = Reddit_Negative_Mentions + ?,
                    Twitter_Total_Mentions = Twitter_Total_Mentions + ?,
                    Twitter_Positive_Mentions  = Twitter_Positive_Mentions + ?,
                    Twitter_Negative_Mentions = Twitter_Negative_Mentions + ?
                WHERE
                Stock_Ticker = '{stock_ticker}';""",
                (
                reddit_total_mentions[stock_ticker],
                stock_sentimental_positive[stock_ticker],
                stock_sentimental_negative[stock_ticker],
                total_mentions[stock_ticker],
                positive[stock_ticker],
                negative[stock_ticker]
                ))
            conn.commit()
        elif key_word == "add": #If the stock ticker is not in the data, then it will add in the values.
            ticker_table.execute(f"INSERT INTO STOCK_TICKERS_{date} Values(?,?,?,?,?,?,?,?);" ,
                 (
                stock_ticker,
                stock_price,
                reddit_total_mentions[stock_ticker],
                stock_sentimental_positive[stock_ticker],
                stock_sentimental_negative[stock_ticker],
                total_mentions[stock_ticker],
                positive[stock_ticker],
                negative[stock_ticker]
                ))
            conn.commit()
    conn.close()
    click.echo("The database has been created. The database is located at: ") #Lets the user know where the file has been created
    click.echo(os.path.realpath("Twitter_Reddit.db"))

if __name__=="__main__":
    add_stocks_to_db()
    twitter_sentimental_analysis()

