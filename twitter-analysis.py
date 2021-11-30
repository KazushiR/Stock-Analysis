import tweepy, os, sqlite3
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from RedditStockTickers import top_ticker_symbols, get_wsb_tickers, stock_sentimental_analysis
from dotenv import find_dotenv, load_dotenv
from collections import Counter

load_dotenv(find_dotenv(".env.txt"))

sid_obj = SentimentIntensityAnalyzer() #NLTK Vader Analysis

def add_stocks_to_db(reddit_total_mentions, stock_sentimental_positive, stock_sentimental_negative, total_mentions, positive, negative ):
    print((reddit_total_mentions, stock_sentimental_positive, stock_sentimental_negative, total_mentions, positive, negative ))
    conn = sqlite3.connect("Twitter_Reddit.db")
    ticker_table = conn.cursor()
    ticker_table.execute("CREATE TABLE IF NOT EXISTS STOCK_TICKERS 
                         (Stock_Ticker TEXT,
                          Reddit_Total_Mentions 
                          INTEGER, 
                          Reddit_Positive_Mentions Integer, 
                          Reddit_Negative_Mentions INTEGER, 
                          Twitter_Total_Mentions Integer, 
                          Twitter_Positive_Mentions  INTEGER, 
                          Twitter_Negative_Mentions INTEGER);")
    sorted_list = sorted(reddit_total_mentions, key = reddit_total_mentions.get, reverse = True)[:10]
    for stock_ticker in sorted_list:
        temp_tuple = (reddit_total_mentions, stock_sentimental_positive, stock_sentimental_negative, total_mentions, positive, negative)
        for values in temp_tuple:
            if (stock_ticker in values) == False:
                values[stock_ticker] = 0
        print("here")
        print(reddit_total_mentions[stock_ticker])
        print(values)
        data = ticker_table.execute("SELECT * FROM STOCK_TICKERS")
        check_data = data.fetchall()
        if len(check_data) == 0:
            key_word = "add"
        else:
            for stocks in check_data:
                print(stocks)
                if stocks[0] == stock_ticker:
                    key_word = "update"
                elif stocks[0] == stock_ticker:
                    key_word = "add"
        if key_word == "update":
            ticker_table.execute(f"""UPDATE STOCK_TICKERS SET
                    Stock_Ticker = ?,
                    Reddit_Total_Mentions = ?,
                    Reddit_Positive_Mentions = ?,
                    Reddit_Negative_Mentions = ?,
                    Twitter_Total_Mentions = ?,
                    Twitter_Positive_Mentions  = ?,
                    Twitter_Negative_Mentions = ?
                WHERE
                Stock_Ticker = '{stock_ticker}';""",
                (
                stock_ticker,
                reddit_total_mentions[stock_ticker],
                stock_sentimental_positive[stock_ticker],
                stock_sentimental_negative[stock_ticker],
                total_mentions[stock_ticker],
                positive[stock_ticker],
                negative[stock_ticker]
                ))
            conn.commit()
        elif key_word == "add":
            ticker_table.execute("INSERT INTO STOCK_TICKERS Values(?,?,?,?,?,?,?);" ,
                 (
                stock_ticker,
                reddit_total_mentions[stock_ticker],
                stock_sentimental_positive[stock_ticker],
                stock_sentimental_negative[stock_ticker],
                total_mentions[stock_ticker],
                positive[stock_ticker],
                negative[stock_ticker]
                ))
            conn.commit()
    conn.close()

def twitter_sentimental_analysis(top_ticker_symbols ):
    negative_list = []
    positive_list = []
    total_mentions = []
    auth = tweepy.OAuthHandler(os.getenv("twitter_api_key"), os.getenv("twitter_api_key_secret"))#Authentication for Twitter
    auth.set_access_token(os.getenv("twitter_api_token"), os.getenv("twitter_api_secret"))
    api = tweepy.API(auth)
    sorted_list = sorted(dict(Counter(top_ticker_symbols)), key = dict(Counter(top_ticker_symbols)).get, reverse = True)[:10]
    for stock_tickers in sorted_list:
        for tweet in tweepy.Cursor(api.search_tweets, q = f"${stock_tickers}  -filter:retweets", lang = "en").items(100):
            no_emoji_tweet = tweet.text.encode("ascii", "ignore").decode("utf8") #ignore emoji's
            sentiment_dict = sid_obj.polarity_scores(no_emoji_tweet)
            if stock_tickers in no_emoji_tweet:
                total_mentions.append(stock_tickers)
                if sentiment_dict["compound"] >= 0.05:
                    positive_list.append(stock_tickers)
                elif sentiment_dict["compound"] <=-.05:
                    negative_list.append(stock_tickers)
    positive_twitter_symbol = dict(Counter(positive_list))
    negative_twitter_symbol = dict(Counter(negative_list))
    total_twitter_mention = dict(Counter(total_mentions))
    return positive_twitter_symbol, negative_twitter_symbol, total_twitter_mention

reddit_total = get_wsb_tickers(top_ticker_symbols)
reddit_sentimental = stock_sentimental_analysis(reddit_total)

twitter = twitter_sentimental_analysis(reddit_total)
add_stocks_to_db(reddit_total, reddit_sentimental[0], reddit_sentimental[1], twitter[2], twitter[0], twitter[1])
