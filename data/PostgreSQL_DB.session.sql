'''
This SQL code is used to create a table called tweets, which will house the data that will be used for the rest of the project
'''

CREATE TABLE tweets (
    id SERIAL PRIMARY KEY,
    created_at TEXT,
    lang TEXT,
    text TEXT,
    full_text TEXT,
    sentiment TEXT,
    sentiment_val FLOAT,
    embedding_vector TEXT
);

TRUNCATE TABLE tweets;

--Alter the created_at column type to DATE
ALTER TABLE tweets
ALTER COLUMN embedding_vector TYPE TEXT

--Check values in tweets
SELECT * FROM tweets;
