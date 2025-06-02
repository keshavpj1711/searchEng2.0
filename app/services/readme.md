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


