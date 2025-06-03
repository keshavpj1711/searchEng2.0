# Services 

This is where all the services that we are using for our Search Engine is placed.
Services present are: 
- TF-IDF Scorer
- Search Logic

## TF-IDF Score

- It's a numerical statistics used to measure the importance of a word in a document relative to a corpus(collection of data).

There are two aspects to it which are: 
  - **TF(Term Frequency)**: Basically how often a term appears in a document.
  - **IDF(Inverse Document Frequency)**: How rare is the term across the entire corpus.

### The Formula

> **TF-IDF Score = TF * IDF**

### A simple example

Example of the Calculation :\
Let’s say that the term “car” appears 25 times in a document that contains 1,000 words.\
We’d calculate the term frequency (TF) as follows:\
**TF = 25/1,000 = 0.025**\
Next, let’s say that a collection of related documents contains a total of 15,000 documents.\
If 300 documents out of the 15,000 contain the term “car,” we would calculate the inverse document frequency as follows:\
**IDF = log 15,000/300 = 1.69**\
Now, we can calculate the TF-IDF score by multiplying these two numbers:\
**TF-IDF = TF x IDF = 0.025 x 1.69 = 0.04225**\

### Implementation 

Our TF-IDF scorer will involve several steps:

- Text Preprocessing: Cleaning and preparing the text from your articles (e.g., tokenizing, lowercasing, removing punctuation, removing common "stop words").

- Calculating Term Frequency (TF): How often each word appears in a single document.

- Calculating Inverse Document Frequency (IDF): How rare or common each word is across all documents in your database.

- Calculating TF-IDF Scores: Multiplying TF by IDF for each word in each document.

## When will we use TF-IDF?

### During Indexing

When a document is added to our system. We will: 
1. preprocess it's text
2. Calculate it's TF of each word in that doc
3. Compute TF-IDF score for each word in that specific doc and update your stored list of TF-IDF scores

Now this Computing of TF-IDF is the most important step and we will have to think more and more about it.

### During Searching(Ranking)

When user submit a search query to our "/search" endpoint, what will happen:
1. Pre process the search query 
2. For each term use the inverted index to find all the document that contain the term
3. Retrieve the pre-calculated TF-IDF score of that query term for each of those documents.
4. Combine these TF-IDF scores to calculate an overall relevance score for each document with respect to the query. The simplest way is to sum the TF-IDF scores of all query terms found in a document
5. Rank the documents based on this relevance score and return the top results.

> TF-IDF scores are calculated when documents are processed/indexed, and these pre-calculated scores are then used during a search to rank documents.

