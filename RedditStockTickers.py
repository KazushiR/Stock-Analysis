import praw, os, nltk, re
from dotenv import load_dotenv, find_dotenv
from praw.models import MoreComments
import yfinance as yf
from collections import Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv(find_dotenv(".env.txt"))

Reddit = praw.Reddit( #This gets the login for the Reddit API
    client_id=os.getenv("reddit_key"),
    client_secret=os.getenv("reddit_secret"),
    user_agent=os.getenv("user_agent"),
    username=os.getenv("reddit_username"),
    password=os.getenv("reddit_pasword"))

wsb_subreddit = Reddit.subreddit("wallstreetbets") #Picks out a subreddit and from there, will go through each comment to get stock information
reddit_sentimental_analysis = {} #This is the initiate the NLTK to analyze each sentence.
countered_dict = {} #THis is an empty dictionary for the number of times a stock is mentioned

sid_obj = SentimentIntensityAnalyzer() #This is to initiate the Vader Sentiment score for each stock

top_ticker_symbols = [] #This is the top most mentioned stock from Reddit
negative_list = [] #This is the sentimental analysis for the negative mentions
positive_list = [] #This is the sentimental analysis for the positive mentions
positive_ticker_symbol = {} #Turns the list into a dictionary
negative_ticker_symbol = {} #Turns the negative list into a dictionary

def get_wsb_tickers(top_ticker_symbols): #This function looks through the submissions and analyzes each sentence
    Nouns = lambda pos: pos[:2] == "NN" #THis lambda looks through the "stock_ticker_list" comments and tries to find anything that is labeled a Noun
    pattern = r'[A-Z]+\b' #This also looks through the "stock_ticker_list" and tried to find a pattern that only mentions stocks that is only upper case
    for submissions in wsb_subreddit.hot(limit = 10): #This goes through the comments for the top 10 posts and gets each comment
        for top_level_comment in submissions.comments:
            if isinstance(top_level_comment, MoreComments):
                continue
            stock_tickers = nltk.word_tokenize(top_level_comment.body)#this seperates each word from the tokenizer and labels each word from the comments
            stock_ticker_list = list(set([word 
                                          for (word, pos ) in nltk.pos_tag(stock_tickers) if Nouns(pos) and re.findall(pattern, word) 
                                          and len(yf.Ticker(word).info) >10 
                                          and not word.startswith("/u/")])) #This portion goes through the tagged comments. Then, checks to see if it's a capitalized word that is three letters long, then goes through a yfinance and looks up the word to see if it's a stock
            top_ticker_symbols = top_ticker_symbols + stock_ticker_list #This adds the number of times a ticker is mentioned and puts it into a list
    reddit_total_mentions = dict(Counter(top_ticker_symbols)) #This looks at the list and counts the same ticker and puts it into a dictionary format
    return reddit_total_mentions


def stock_sentimental_analysis(top_ticker_symbols): #This function takes the "reddit_total_mentions and stock, looks through the reddit API and looks at the new comments of each post to analyze the sentence if the stock is mentioned
        sorted_list = sorted(top_ticker_symbols, key = top_ticker_symbols.get, reverse = True)[:10] #this sorts the dictionary to the top 10 tickers
        for submissions in wsb_subreddit.hot(limit = 10): #Gets the top 10 posts
            for top_level_comment in submissions.comments:
                if isinstance (top_level_comment, MoreComments):
                    continue
                finding_ticker = (top_level_comment.body).split() #Splits up the comments
                stock_placement = [ticker for ticker in sorted_list for word in finding_ticker if ticker == word]  #This checks the comments to see if the stock ticker is in the comment
                if [ticker for ticker in sorted_list for word in finding_ticker if ticker == word]:#if it is, it sentamentalizes the sentence and gives it a score.
                    sentiment_dict = sid_obj.polarity_scores(top_level_comment.body)
                    for ticker_symbol in stock_placement:
                        if sentiment_dict["compound"] >=.05:#If the sentimental score is above a .05, then it will go into the positive list
                            positive_list.append(ticker_symbol)
                        elif sentiment_dict["compound"] <= -.05:#If the sentimental score is less then -.05, then it will go into the negative list
                            negative_list.append(ticker_symbol)
        #The two statements below takes the #sentimental score of the positive list and negative list and counts it up. From there, it counts the number of positive or negative sentences.
        positive_ticker_symbol = dict(Counter(positive_list))
        negative_ticker_symbol = dict(Counter(negative_list))
        return positive_ticker_symbol, negative_ticker_symbol

