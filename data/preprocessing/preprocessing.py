import json
import os
from datetime import datetime
import psycopg2
import spacy
import torch
from textblob import TextBlob
from transformers import BertModel, BertTokenizer

'''
The following code is used to observe the first line of the data in order to figure out which values are relevant to the project
'''
# Get the current directory of preprocessing.py
current_dir = os.path.dirname(__file__)

# Specify the path in a way that is reproducable
file_path = os.path.join(current_dir, '../tweets.jl')

# Print the file path for debugging
print(f"File path: {file_path}")

# Function to read and print the first line from a JSON Lines file
def view_first_line(file_path):
    try:
        # Open the tweets.jl file
        with open(file_path, 'r') as file:
            # Read the first line
            first_line = file.readline().strip()
            # Parse the first line
            data = json.loads(first_line)
            # Print the first line
            print(data)
    # Print the error message if the file is not found
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    
# Call the function to view the first line
view_first_line(file_path)

'''
Data relevant to this project, and therefore should be kept, are date tweeted (created_at), text, full_text, and language the tweet was written in (lang),
which are all in the document section of the file. The text data will be cleaned using SpaCy by lemmatization, which will reduce the words to their base form, 
removing stop words, which do not significantly impact the meaning of the text, and removing values that do not consist of alphabetic characters. 
'''

# Load in SpaCy for data cleaning
nlp = spacy.load('en_core_web_sm')
# Load in bert for embedding
nlp2 = spacy.load('en_core_web_trf')

# Function to clean text using SpaCy
def clean_text(text):
    doc = nlp(text)
    # Iterate over the tokens in the text and lemmatize and save the tokens that are not stop words and contain only alphabetic characters
    cleaned_tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    # Join the cleaned tokens with a space
    cleaned_text = ' '.join(cleaned_tokens)
    return cleaned_text

'''
The BERT model will be used to create the embeddings, which can be used for the similarity search later on in the project. The code and explanations for the 
BERT model is largely influenced by a blog called "How to use BERT Sentence Embedding for Clustering text" by Nikita Sharma, found at:
https://techblog.assignar.com/how-to-use-bert-sentence-embedding-for-clustering-text/. 
'''

# Load BERT model and tokenizer
bert = BertModel.from_pretrained("bert-base-uncased")
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

# Function to get embedding values from the text
def get_embeddings(text):
    # Split the text into single word tokens
    tokens = tokenizer.tokenize(text)
    # Convert the tokens into id coutnerparts
    indexed_tokens = tokenizer.convert_tokens_to_ids(tokens)
    # Add a batch dimension so that the tokens can be fed through the bert model
    tokens_tensor = torch.tensor([indexed_tokens])
    # Prevents tracking gradients, which reduces memory usage and speeds us computations
    with torch.no_grad():
        # Create a variable that contains all of the elements produced by the bert model
        outputs = bert(tokens_tensor)
        # Creat a variable of the averages among the hidden states across all tokens
        embeddings = outputs[0].mean(dim=1) 
    # Return a NumPy array if the embedding values
    return embeddings.numpy()

# flattens the array
def flatten_array(array):
    return array.flatten()

'''
This next section begins by connecting to the tweets_db PostgreSQL database. The database was created in the PostgreSQL_DB file, which is also in the data
folder. After creating the connection with the database, the following code iterates throught the tweets.jl file line by line, picks the keys that will be kept,
and cleans the text data using the clean_text function from above. Once the data is clean, it formats the text in the manner that will be accepted by the
database and can be used during the project, and then uses SQLs INSERT function to add each row to the database.

TextBlob was used for the sentiment analysis. This code came from a project I worked on previously, where I ran a sentiment analysis on tech reviews for 
different devices. 
'''
# Create the connection with the database
try: 
    connection = psycopg2.connect(
        user = "aaronrobinson",
        password = "test",
        host = "localhost",
        port = "5432",
        database = "tweets_db")
    cursor = connection.cursor()
    
    # Open the tweets.jl file and iterate through it line by line
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            try:
                # The results variable is assigned the parsed json text
                results = json.loads(line)
                data = results['document']
                # If full_text is not in the data, preserve the text from the 'text' value before 'text' gets cleaned and remove any single "'"
                if 'full_text' not in data:
                    data['full_text']= data['text'].replace("'", "''")
                else:
                    data['full_text']= data['full_text'].replace("'", "''")
                # Use the clean_text function found above to clean the text data in data['document']
                if 'text' in data:
                    data['text']= clean_text(data['text'])
                # If the clean_text function removes all words from 'text', the array will end up being empty, which causes a diminsionality error.
                # These next lines of code prevent the error at the cost of using the full, unedited text, which may slightly change the vector values, but 
                # keeps the diminsionality greater than 0
                if len(data['text']) != 0:
                    embedding_vector = get_embeddings(data['text'])
                else:
                    embedding_vector = get_embeddings(data['full_text'])
                
                # These next lines were useful for formatting the vector so that it would not cause issues loading into the database
                embedding_vector = flatten_array(embedding_vector)
                embedding_vector = str(embedding_vector.tolist())
                
                # Edit the created_at value into a more readable format
                date = datetime.strptime(data['created_at'], "%a %b %d %H:%M:%S %z %Y").strftime("%Y-%m-%d")
                # Format the data so that they will be accepted into the VALUES section of the query
                data['created_at'] = f"'{date}'"
                data['lang'] = f"'{data['lang']}'"
                data['text'] = f"'{data['text']}'"
                if 'full_text' in data:
                    data['full_text'] = f"'{data['full_text']}'"
                else:
                    data['full_text'] = data['text']

                # Perform sentiment analysis using TextBlob
                blob = TextBlob(data['text'])
                sentiment_val = blob.sentiment.polarity

                # Determine sentiment category
                if sentiment_val > 0:
                    sentiment_category = 'Positive'
                elif sentiment_val < 0:
                    sentiment_category = 'Negative'
                else:
                    sentiment_category = 'Neutral'
                # Format the sentiment category so that it will be accepted into the PostgreSQL database
                sentiment = f"'{sentiment_category}'"
                # Format the embedding_vector so that it will be accepted into the PostgreSQL database
                if len(embedding_vector) == 0:
                    embedding_vector = None
                else:
                    embedding_vector = f"'{embedding_vector}'"

                # Create a string representing SQLs INSERT VALUES function
                insert_query = f"INSERT INTO tweets(created_at, lang, text, full_text, sentiment, sentiment_val, embedding_vector) VALUES ({data['created_at']}, {data['lang']}, {data['text']}, {data['full_text']}, {sentiment}, {sentiment_val}, {embedding_vector})"
                
                # Execute the query
                cursor.execute(insert_query)
                connection.commit()
                   
            # If there is an error, print out the error message
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
except (Exception, psycopg2.Error) as error:
    print("Error:", error, data['created_at'], data['text']) 

# This is just so that I know when the code was completed
print('Done!')
