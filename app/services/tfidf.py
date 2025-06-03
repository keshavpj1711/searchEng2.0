import re  # Python RegEx(Regular Expression) For text cleaning
import math  # Calculating log for IDF
from collections import Counter
from typing import List, Dict, Set  # For type hinting

# What we want

# 1. Text preprocessing 
# To clean and standardize the text content of your articles
# Tokenization, Lowercasing, Removing punctuation, and
# Removing stop words: basically words which don't add meaning like "is", "an", "in" etc.


DEFAULT_STOP_WORDS = set([
    "a", "about", "above", "after", "again", "against", "ain", "all", "am", "an",
    "and", "any", "are", "aren", "arent", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can", "cannot",
    "could", "couldn", "couldnt", "d", "did", "didn", "didnt", "do", "does",
    "doesn", "doesnt", "doing", "don", "dont", "down", "during", "each", "few",
    "for", "from", "further", "had", "hadn", "hadnt", "has", "hasn", "hasnt",
    "have", "haven", "havent", "having", "he", "hed", "hell", "hes", "her",
    "here", "heres", "hers", "herself", "him", "himself", "his", "how", "hows",
    "i", "id", "ill", "im", "ive", "if", "in", "into", "is", "isn", "isnt",
    "it", "its", "itself", "lets", "ll", "m", "ma", "me", "mightn", "mightnt",
    "more", "most", "mustn", "mustnt", "my", "myself", "needn", "neednt", "no",
    "nor", "not", "now", "o", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "re", "s", "same",
    "shan", "shant", "she", "shed", "shell", "shes", "should", "shouldn",
    "shouldnt", "shouldve", "so", "some", "such", "t", "than", "that", "thatll",
    "thats", "thatve", "the", "their", "theirs", "them", "themselves", "then",
    "there", "theres", "these", "they", "theyd", "theyll", "theyre", "theyve",
    "this", "those", "through", "to", "too", "under", "until", "up", "ve", "very",
    "was", "wasn", "wasnt", "we", "wed", "well", "were", "weren", "werent",
    "what", "whats", "when", "whens", "where", "wheres", "which", "while", "who",
    "whos", "whom", "why", "whys", "will", "with", "won", "wont", "would",
    "wouldn", "wouldnt", "y", "you", "youd", "youll", "youre", "youve", "your",
    "yours", "yourself", "yourselves","article", "section", "figure", "table", "reference", 
    "references", "citation", "citations", "external", "links", "see", "also", "page", "pages",
    "volume", "chapter", "edition", "et", "al" , "isbn", "history", "notes", "further", "reading",
    "doi", "retrieved", "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december" 
])

def preprocess_text(text: str, stop_words: Set[str] = DEFAULT_STOP_WORDS) -> List[str]:  # This is just to show that it outputs a list
  if not text: 
    return []

  text = text.lower()  # Lowercase
  text = re.sub(r'[^\w\s]', '', text)  # Only selecting numbers, spaces and alphanumerics, discarding puntuation and stuff
  # [^\w\s] matches anything that is not a word and not a white space and replaces it with '': empty string
  tokens = text.split()

  # removing the stop words
  processed_tokens: List[str] = []
  for token in tokens:
    if token not in stop_words: 
      processed_tokens.append(token)

  return processed_tokens

def calculate_tf(tokens: List[str]) -> Dict[str, float]:
  if not tokens: 
    return {}

  total_terms_in_doc = len(tokens)

  # collections.Counter is efficent for these tasks
  term_counts = Counter(tokens)

  # calculating the tf_scores = (no of occurence)/(total terms in doc)
  tf_scores: Dict[str, float] = {}
  for term, count in term_counts.items():
    tf_scores[term] = count / total_terms_in_doc
   
  return tf_scores


# IDF = log(N/df_t); N being the total docs and df_t being the number of docs in which the term is present
def calculate_idf(corpus_tokens: List[List[str]]) -> Dict[str, float]:
  if not corpus_tokens:
    return {}

  total_docs = len(corpus_tokens)

  # Now to find df_t
  doc_frequencies: Dict[str, int] = Counter()
  for doc_tokens in corpus_tokens:
    # Getting the unique term in each doc
    unique_terms_in_doc = set(doc_tokens)
    # Traversing through terms and counting there occurence
    for term in unique_terms_in_doc:
      doc_frequencies[term] += 1
    
  idf_scores: Dict[str, float] = {}

  for term, df in doc_frequencies.items():
    if df > 0:
      idf_scores[term] = math.log((total_docs/df))
    else: 
      idf_scores[term] = 0.0

  return idf_scores


def calculate_tfidf(tokens: List[str], idf_scores: Dict[str, float]) -> Dict[str, float]:
  """
  Calculates the TF-IDF score for each term in a document, given the document's tokens and the corpus IDF scores.
  TF-IDF(term, document) = TF(term, document) * IDF(term)
  
  Args:
    tokens: A list of preprocessed tokens from a single document.
    idf_scores: A dictionary where keys are terms and values are their IDF scores (calculated from the entire corpus).
    
  Returns:
    A dictionary where keys are terms and values are their TF-IDF scores for the given document.
  """
  tf_scores = calculate_tf(tokens) # Get TF scores for the document
  
  tfidf_scores: Dict[str, float] = {}
  for term, tf in tf_scores.items():
    # Get IDF score for term.  If term not in IDF (rare case), treat IDF as 0 (not important).
    idf = idf_scores.get(term, 0.0) # 0 if term not in IDF
    tfidf_scores[term] = tf * idf
    
  return tfidf_scores


if __name__ == "__main__":
  pass