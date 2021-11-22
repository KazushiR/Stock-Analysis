import praw, os, nltk, re
from dotenv import load_dotenv, find_dotenv
from praw.models import MoreComments
import yfinance as yf
from collections import Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv(find_dotenv(r"C:\Users\kazna\OneDrive\Desktop\PythonProjects\environmental_passwords for sites\.env.txt"))

Reddit = praw.Reddit(
    client_id=os.getenv("reddit_key"),
    client_secret=os.getenv("reddit_secret"),
    user_agent=os.getenv("user_agent"),
    username=os.getenv("reddit_username"),
    password=os.getenv("reddit_pasword"))

wsb_subreddit = Reddit.subreddit("wallstreetbets")
reddit_sentimental_analysis = {}
countered_dict = {}

sid_obj = SentimentIntensityAnalyzer()

top_ticker_symbols = []
negative_list = []
positive_list = []
positive_ticker_symbol = {}
negative_ticker_symbol = {}

def get_wsb_tickers(top_ticker_symbols):
    Nouns = lambda pos: pos[:2] == "NN"
    pattern = r'[A-Z]+\b'
    for submissions in wsb_subreddit.hot(limit = 1):
        print(submissions.title)
        submissions.comment_limit = 3
        for top_level_comment in submissions.comments:
            if isinstance(top_level_comment, MoreComments):
                continue
            stock_tickers = nltk.word_tokenize(top_level_comment.body)
            stock_ticker_list = list(set([word for (word, pos ) in nltk.pos_tag(stock_tickers) if Nouns(pos) and re.findall(pattern, word) and len(yf.Ticker(word).info) >10 and not word.startswith("/u/")]))
            top_ticker_symbols = top_ticker_symbols + stock_ticker_list
    reddit_total_mentions = dict(Counter(top_ticker_symbols))
    return reddit_total_mentions


def stock_sentimental_analysis(top_ticker_symbols):
        pattern = r'[A-Z]+\b'
        sorted_list = sorted(top_ticker_symbols, key = top_ticker_symbols.get, reverse = True)[:10]
        for submissions in wsb_subreddit.hot(limit = 1):
            submissions.comment_limit = 3
            for top_level_comment in submissions.comments:
                temp_dict = {}
                if isinstance (top_level_comment, MoreComments):
                    continue
                finding_ticker = (top_level_comment.body).split()
                stock_placement = [ticker for ticker in sorted_list for word in finding_ticker if ticker == word]
                if [ticker for ticker in sorted_list for word in finding_ticker if ticker == word]:
                    sentiment_dict = sid_obj.polarity_scores(top_level_comment.body)
                    for ticker_symbol in stock_placement:
                        if sentiment_dict["compound"] >=.05:
                            positive_list.append(ticker_symbol)
                        elif sentiment_dict["compound"] <= -.05:
                            negative_list.append(ticker_symbol)

        positive_ticker_symbol = dict(Counter(positive_list))
        negative_ticker_symbol = dict(Counter(negative_list))
        return positive_ticker_symbol, negative_ticker_symbol

