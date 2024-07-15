from datetime import date
from pydantic import BaseModel
from typing import List, Annotated, Dict, Optional
from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse
from starlette.status import HTTP_400_BAD_REQUEST
from collections import defaultdict
import nltk
from nltk.cluster import KMeansClusterer
import numpy as np
import json

'''
The concepts that make up this file and the html files in the templates folder come from the Udemy Courses: "Learn FastAPI, Python, REST APIs, Bootstrap, SQLite,
Jinja, and web security; all while creating 3 full-stack web apps" and REST APIs with Flask and Python in 2024"
Code that represents the connection between the PostgreSQL Database and the APIs was based largely on Eric Roby's FastAPI Tutorial, "How to Build a FastAPI
app with PostgreSQL"
'''
# Using Jinja2 makes it easier to generate dynamic web pages with python
templates = Jinja2Templates(directory = "templates")

# Creates an instance of FastAPI
app = FastAPI()

# Loads in the table that was created in the preprocessing.py file
models.Base.metadata.reflect(bind = engine)

# Mount the static directory as a route to serve static files for the web page
app.mount("/static", StaticFiles(directory = "static"), name = "static")


# Create a class that represents the table in PostgreSQL
class Tweets(BaseModel):
    created_at: date
    lang: str
    text: str
    full_text: str
    sentiment: int
    sentiment_category: str

# Opens and closes the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Creates a variable, db_dependency, using the get_db function above to easily open and close a session within the endpoints
db_dependency = Annotated[Session, Depends(get_db)]

'''
The next section of code includes the endpoints and the functions that are utilized by the endpoints.
'''

# This endpoint redirects the page to 'home' if a location is not specified
@app.get("/", response_class = RedirectResponse)
async def root(request: Request):
    return RedirectResponse(url = "/home")

# The home page just includes the 10 (by default) most recent tweets
@app.get("/home/")
async def get_top_tweets(db: db_dependency, request: Request, skip: int = 0, limit: int = 10):
    # the tweets variable represents the results of the database query that occurs after db.query()
    tweets = db.query(models.Tweets).offset(skip).limit(limit).all()
    # the home.html is returned with the tweets query values displayed in the body of the web page
    return  templates.TemplateResponse("home.html", {"request": request, "tweets":tweets, "title": "Home"})

# The first main endpoint, tweets_by_date, takes two dates (defaulted as 1/1/2018 and 1/10/2018) and returns all of the tweets found between and including
# those dates
@app.get("/tweets_by_date/")
async def get_tweet_by_date(db: db_dependency, request: Request, start_date: date , end_date: date):
    tweets = db.query(models.Tweets).filter(models.Tweets.created_at >= start_date, models.Tweets.created_at <= end_date).all()
    return  templates.TemplateResponse("home.html", {"request": request, "tweets":tweets, "title": "Tweets By Date"})

# The next endpoint, tweets_by_keyword, takes a keyword (defaulted as 'politics') and finds all tweets that contain that keyword
@app.get("/tweets_by_keyword/")
async def get_tweet_by_keyword(db: db_dependency, request: Request, keyword: str):
    tweets = db.query(models.Tweets).filter(models.Tweets.full_text.contains(keyword)).all()
    return  templates.TemplateResponse("home.html", {"request": request, "tweets":tweets, "title": "Tweets By Keyword"})

# This code largely comes from https://www.geeksforgeeks.org/python-program-for-most-frequent-word-in-strings-list/
# but was edited to meet the project requirements 
def get_count(tweet_list, rank):
    # defaultdict is a fast way to initialize a dictionary that uses a default value of 0
    temp = defaultdict(int)
    # tweet_list is a list of all tweets, created in the endpoint below. in this instance, sub is a single tweet
    for sub in tweet_list:
        # word represents each word that comes out of the sub.split() method
        for word in sub.split():
            # using the word as a key value, temp adds one to the value each time it encounters the word
            temp[word] += 1
    # sorted_words is a sorted list by the number values (x[1]) of each temp dictionary pair and then sorts by descending 
    sorted_words = sorted(temp.items(), key = lambda x: x[1], reverse = True)
    # rank_list is an empy list that will contain the N number of items, depending on the value of rank
    rank_list = []
    # Initialize i at 0 so that it can iterate through sorted_words until it is equal to rank
    i = 0
    while i <= rank:
        rank_list.append(sorted_words[i])
        i += 1
    # Prevent users from asking for a rank value that is larger than the total number of unique words
    if rank <= len(sorted_words):
        result = rank_list
    else:
        result = f"Error. There are only {len(sorted_words)}. Please choose a value equal to or fewer than {len(sorted_words)}"
    return result

# The next endpoint utilized the function above, get_count(), to find the top N (10 by defauly) most frequently used words
@app.get("/most_frequent/")
async def get_most_frequent(db:db_dependency, request: Request, n: int):
    # In order to begin at 0, but allow the user to type in the number they want to see, n has to equal 1 less than the input value
    n = n -1
    # Only use the cleaned 'text' value to prevent stop words, like 'the' to be chosen as the most common word
    tweets = db.query(models.Tweets.text).all()
    # Creates a list of tweets so that get_count can iterate and split them
    full_texts = [tweet for (tweet,) in tweets]
    # Initiate get_count and return the result to the result variable 
    result = get_count(full_texts, n)
    # Display the result on the web page as n + 1, to revise the 1 that was subtracted earlier
    #return {f"The Top {n+1} Most Frequest Word(s) is": result}
    return  templates.TemplateResponse("most_frequent.html", {"request": request, "tweets":result, "title": "Most Frequent Words"})

'''
The last endpoint, which finds the similarity between tweets using cosine similarity was influenced by a couple of resources. The first was a Udemy course 
called "NLP - Natural Langauge Processing with Python", but small parts were pulled from blogs like "Introduction to Embedding, Clustering, and Similarity" by
Mathias Gronne at: https://towardsdatascience.com/introduction-to-embedding-clustering-and-similarity-11dd80b00061, and "How to use BERT Sentence Embedding for 
Clustering text" by Nikita Sharma, found at: https://techblog.assignar.com/how-to-use-bert-sentence-embedding-for-clustering-text/, which I mentioned in 
the preprocessing file. 
'''

# This function performs the cosine similarity function on the given tweet and each target tweet
def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1)*np.linalg.norm(vec2))

# The final endpoint uses embedding and cosine similarity to find the top_n (defaulted at 10) tweets similar to a tweet given by ID (defaulted at 71000)
@app.get("/similar_tweets/", response_model = List[Tweets])
async def get_similar_tweets(db:db_dependency, request:Request, tweet_id: int, top_n: int = 10):
    # the endpoint begins by querying the tweet that matches the ID given in the function above
    target_tweet = db.query(models.Tweets).filter(models.Tweets.id == tweet_id).first()
    # If the tweet id does not exist, an error will be raised
    if not target_tweet:
        raise HTTPException(status_code= 404, detail = "Tweet not found")
    
    # Here, the target tweet is identified and begins to be formatted
    target_vector = target_tweet.embedding_vector
    # Formatting the vectors turned in to a multi line process, but the next three lines seemed to get the vector in the correct format for cosine similarity
    target_vector_str = target_vector
    target_vector_list = json.loads(target_vector_str)
    target_vector = np.array(target_vector_list, dtype = float)

    # Retrieve all of the tweets from the database
    all_tweets = db.query(models.Tweets).all()
    # Create an empty list for the tweet, similarity tuples
    similarities = []

    # Start iterating through all of the tweets
    for tweet in all_tweets:
        # Ignore the tweet with a matching ID, as it will always be the most similar to itself
        if tweet.id != tweet_id:
            # Perform the same formatting process on each tweet in all_tweets that was performed on the target tweet above
            tweet_embedding_str = tweet.embedding_vector
            tweet_embedding_list = json.loads(tweet_embedding_str)
            tweet_embedding = np.array(tweet_embedding_list, dtype = float)
            # Use the cosine_similarity function from above to retrieve the similarity value between the target tweet and the tweet from all_tweets
            similarity = cosine_similarity(target_vector, tweet_embedding)
            # append the tweet, similarity tuple to the similarities list
            similarities.append((tweet, similarity))
    # Same as sorting the sorted_words in the top N most frequent words, this next line of code sorts for the highest similarity values
    similarities.sort(key=lambda x:x[1], reverse = True)
    # similar_tweets is a list made up of the tweets and similarity values that rank the top_n closest to the target tweet
    similar_tweets = [tweet for tweet, similarity in similarities[:top_n]]
    # Return the similar_tweets list in the home.html format, which will appear on the web page
    return  templates.TemplateResponse("similar_tweets.html", {"request": request, "tweets":similar_tweets, "target_tweet": target_tweet, "title": "Similar Tweets"})
    
    