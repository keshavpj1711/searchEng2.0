# Services 

This is where all the services that we are using for our Search Engine is placed.
Services present are: 
- TF-IDF Scorer
- Search Logic

# TF-IDF Score

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
  - This is one of the complex part, discussion for handling of this is [here](#idf-dictionary)

- Calculating TF-IDF Scores: Multiplying TF by IDF for each word in each document.

## When will we use TF-IDF?

### During Indexing

When a document is added to our system. We will: 
1. preprocess it's text
2. Calculate it's TF of each word in that doc
3. Compute TF-IDF score for each word in that specific doc and update your stored list of TF-IDF scores

Now this Computing of TF-IDF is the most important step and we will have to think more about it.

### During Searching(Ranking)

When user submit a search query to our "/search" endpoint, what will happen:
1. Pre process the search query 
2. For each term use the inverted index to find all the document that contain the term
3. Retrieve the pre-calculated TF-IDF score of that query term for each of those documents.
4. Combine these TF-IDF scores to calculate an overall relevance score for each document with respect to the query. The simplest way is to sum the TF-IDF scores of all query terms found in a document
5. Rank the documents based on this relevance score and return the top results.

> TF-IDF scores are calculated when documents are processed/indexed, and these pre-calculated scores are then used during a search to rank documents.

## IDF Dictionary

We are following a systematic approach for creating our IDF Dictionary. It's needed because we have to multiply it with tf in order to get the tf_idf score for a term, for a particular document.

### Building of IDF

Steps involved in creating our IDF Dict are: 

-  fetches all the present articles
  - puts all the data into a list 
      ```python 
      cursor = conn.cursor()
      cursor.execute("SELECT title, content FROM articles WHERE content IS NOT NULL")
      rows = cursor.fetchall()
      for row in rows:
        # Combine title and content into one document, giving title extra weight
        combined_text = f"{row['title']} {row['title']} {row['content']}"
        contents.append(combined_text)
      ```
  - We have **given title an increased weight** in order to improve the search

- Using the `contents` list whose each element is a string that is comprised of title x 2 and the content
  - preprocessing each and every element of `contents` giving us corpus_tokens
- Total documents = length(contents)
- Now the IDF is calculated using the number of docs in which a term occurs and total docs 
  - The implemented logic is held in the `calculate_idf_with_freq()` which gives us idf_dict as well as the word_to_doc_freq


## Important data we need to store in order to calculate the TF-IDF score for a particular term of a specific document

- **IDF Scores Dictionary:**\
> uses the document_freq in order to calculate idf_scores
Maps each term to its current IDF value.\
Example: { "python": 1.2, "database": 0.8, ... }

- **Document Frequency Dictionary (df_t):**\
Maps each term to the number of documents it appears in.\
Example: { "python": 300, "database": 150, ... }

- **Total Document Count (N):**\
The total number of documents in your corpus.

> Inverted Index: Maps terms to the list of documents (and optionally TF-IDF scores) that contain them.
> Not from TF-IDF scores


## Compute TF-IDF score for each word in that specific doc and update your stored list of TF-IDF scores

This is one of the major problems to tackle. At this point since the dataset is small what we are doing is just for testing and development purposes.

### First Approach

> This is the first approach i am going to follow and over time this might not be the approach i am using so please see accordingly

rebuilding the data like: 
- IDF Score Dictonary
- Document Freq: Maps each term to the number of docs it appears in
- Total document count
every time server restart

What this approach follows is that the **idf scores for the newly added document is calculated based on the previous data available**.\
This does decrease our quality of search but it is simpler to implement.

### At some point in future approach

- **Incremental Updates**: That is only when the documents are added or removed we make changes to these above mentioned data
- **Background Processing**: Using Celery to rebuilding this data asynchronously


# Building Inv Index 

Here's the format of the inverted index we are trying to build: \
`term -> [(doc_id, tf_idf_score), (doc_id, tf_idf_score), (doc_id, tf_idf_score), ...]`

## What we need?

To build it we need somethings before hand: 
- The articles from the db
- the idf_dict for terms

## The process

- We fetch the generated/stored idf_scores for terms and all the articles from our db to process

- For each article:
  - Get it's doc_id
  - **Get combined text**: title + title + content
    - the title is added two times to give weights to the title 
  - **Preprocess the combined text** to get tokens so that we can parse through each term 
  - From these tokens we calculate their tf_idf_score using our function.
  - **For each term** in the tf_idf_scores_dict **we check if it's present in the inv index** or not
    - if NOT, we create a entry for that term as `term: [(doc_id, tf_idf_score)]` in the inv index
    - if YES, we add the `(doc_id, tf_idf_score)` to the list for that term

> Now at the end we sort tf_idf scores as highest first for each term 
```python 
for term in inverted_index:
    inverted_index[term].sort(key=lambda x: x[1], reverse=True)
```


# Search Logic

Implementing the search logic is pretty simple once we have our inverted index. When implementing our `/search` we are going to call this with the parameter being the search terms.

## What we need 

- Our inverted index 
- fetching documents by id

## The process

In the process first we are going to process the search terms and then going to fetch the articles wrt to the document score.

### Creating document_scores_dict 

Searching docs to fetch and getting their document scores

- For each token in the search string we fetch the respective documents

- Then we make a document_scores_dict by combining the tf_idf scores for search_query terms. 
  - For example we have search_query as **"indexes text"**
  - Now **"indexes"** is present in doc_id 1, 23, 21 and 40.
  - And **"text"** is present in doc_id 21, 30, 40 and 60.
  - Formulating the document_scores_dict:
    ```python
    {
      1: tf_idf_score for "indexes",
      21: tf_idf_score for "indexes" + "text", 
      23: tf_idf_score for "indexes",
      30: tf_idf_score for "text", 
      40: tf_idf_score for "indexes" + "text",
      60: tf_idf_score for "text",
    }
    ```

### Fetching document details

After we have our `document_scores_dict` we can fetch the details of the document with doc_ids present in the dict.

This is done in order to return this to the user with article title, content and other details.

Now before fetching we first sort the `document_scores_dict` to have the documents with highest scores to be fetched first.