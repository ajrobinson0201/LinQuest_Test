**LinQuest Interview Project**

**Table of Contents:**
* Environment
* Getting Started
* Usage
* Endpoints
* Templates
* Docker

**Environment** 
* Python3, version 11

**Important Files**

*app/data/database.py*
* the database.py file uses psycopg2 to generate the connection with the database

*app/data/preprocessing/preprocessing.py*
* the preprocessing.py file serves two important functions:
1. It allows the user to visualize the first line of the tweets.jl file. This is important because the user needs to observe and then get rid of any noise or irrelevant data to the project
2. It iterates through the tweets.jl file and performs several functions that are crucial to the project such as:
    * cleaning the data. It gets rid of any noise and irrelevant data and, when necessary, uses lemmatization, removes stop words, and removes any non-alphabetical character.
    * performing sentiment analysis using TextBlob on the cleaned data and returns both sentiment values and their respective categories to be displayed on the web app
    * creating embedding vectors using BERT for each tweet so that similarity searches can be performed within the web app based on the vector values
    * formatting the values into a format that can be read into the database
    * using the SQL INSERT VALUES function to insert the desired values into the database

*app/api/database.py*
* the database.py file in the api folder creates a local session of the databse using sqlalchemy

*app/api/models.py*
* the models.py file uses the database to create the class object Tweets, which will be referenced by each of the endpoints. 

*app/api/main.py*
* The main.py file is, as the name suggests, the main file for this project. It carries out several functions including:
    * creating an instance of and mounting the FastAPI app
    * utilizing Jinja2 to create a dynamic web app using the templates (read about the html templates in the Templates section of this README)
    * opening and closing the database session as needed
    * defining each of the endpoints and the associated functions that handle various HTTP requests

**Getting Started**

*Library Installation:*
* The Docker should install all necessary libraries from the requirements.txt file, but in the case that the use wants to manually install, the following code will install the necessary libraries:
    * pip install psycopg2 spacy torch textblob transformers sqlalchemy pydantic fastapi starlette jinja2 nltk numpy
    * python -m spacy download en_core_web_sm

*Creating the Database*
* For users on Visual Studio Code, go to the extensions tab and install the SQLTools and PostgreSQL extensions. 
* Open an instance of SLQTools and create a PostgreSQL Database Connection. The information that I used to create my database is as follows:</br>
        user = "aaronrobinson",</br>
        password = "test",</br>
        host = "localhost",</br>
        port = "5432",</br>
        database = "tweets_db")
* ***If any of the database values (user, password, host, port, and database) used by a contributer or user is different than the values shared above, make sure to alter the database connection code in preprocessing.py (lines 105-109) and the URL_Database value in database.py (line 6) to match the values and URL chosen by the contributer or user.***

* Run the preprocessing.py file, which is found in the app folder to create the PostgreSQL database from the tweets.jl by pressing the play button in the top right corner of the VSC window. The code should run for about 5 minutes to fully establish the database. The user will know that the database has been fully established when "Done!" appears in the Terminal Window. 

**Usage**

*Start the FastAPI Server*
* uvicorn app.api.main:app --reload

*Open your browser and navigate to*
* http://127.0.0.1:8000

**Endpoints** 

* There are 6 endpoints found in the main.py file, which is in the api folder:
1. **Redirect**
* **URL:** "/"
* **Method:** GET
* **Description:** Redirects the web app to the "/home/" page if not given a specific path
2. **Home**
* **URL:** "/home/"
* **Method:** GET
* **Description:** Acts as a homepage for the web app. It displays the 10 most recent tweets in the database
1. **Tweets By Date**
* **URL:** "/tweets_by_date/"
* **Method:** GET
* **Description:** Allows the user to input two data values and retrieves the tweets that fall between those two dates, including the tweets that occured on those dates
1. **Tweets By Keyword**
* **URL:** "/tweets_by_keyword/"
* **Method:** GET
* **Description:** Allows the user to input a word value and retrieves tweets that contain the given value
1. **Most Frequent Words**
* **URL:** "/most_frequent/"
* **Method:** GET
* **Description:** Allows the user to input an integer value and retrieves the input number of most frequently used words in the database and displays each of  the words and the number of times it was used. 
1. **Similar Tweets**
* **URL:** "/similar_tweets/"
* **Method:** GET
* **Description:** When the user presses the "Find Similar Tweets" button, which is displayed in each tweet object on the web page, the web app displays the top 10 tweets that are deemed similar to the selected tweet based on the embedding vector that is assigned to each tweet.

**Templates**

*The templates used in this project were largely based off of the format provided in the UDemy Course: "Learn FastAPI, Python, REST APIs, Bootstrap, SQLite, Jinja, and web security; all while creating 3 full-stack web apps". Much of the web apps formatting pulls directly from bootstrap.com*

1. **footer.html**
* **Description:** Creates the footer for the web app using a preset script from bootstrap.com
2. **header.html** 
* **Description:** Creates the header for the web app using a stylesheet from bootstrap.com
3. **home.html**
* **Description:** home.html is the main user interface. It pulls the values from the footer, header, and navbar html files and adds the body of the web app. The endpoints each return an object called "tweets", which houses each of the individual queried tweet values and displays the tweet's date created, full text, and sentiment value and the Find Similar Tweets Button.
4. **most_frequent.html**
* **Description:** Shares the same interface as the home.html with the header, footer, and navbar, but the /most_frequent/ endpoint returns a list of tuples, which are displayed in a similar fashion in the most_frequent.html file as the tweets in the home.html file
5. **navbar.html**
* **Description:** navbar.html is where most of the user's actions take place (besides pressing the Find Similar Tweets Button). This html files creates the input boxes for each enpoint as well as Search buttons, when necessary. 
6. **similar_tweets.html**
* **Description:** The similar_tweets.html files shares the exact same format as the home.html files, except that it adds a row at the top of the body of the web app for the target tweet that was selected by pressing the Find Similar Tweets button.

**Docker**

*Installation*
* Go to https://docs.docker.com/desktop/ and click to install

*Usage*
* In the CLI, run docker compose up --build to load up the libraries from the requirements.txt file
* In the CLI, run uvicorn app.api.main:app --reload
* The web app will load up at http://127.0.0.1:8000 