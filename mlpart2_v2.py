# -*- coding: utf-8 -*-
"""MLpart2_V2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1HOqO4nnUU2bz4UUFakhqS73uodX2Zw6H
"""

# install spacy
!pip install --upgrade spacy
!python -m spacy download en_core_web_md

!pip install clean-text

import numpy as np # numpy is a library that allows us to work with vectors and matrices
import matplotlib.pyplot as plt # visualisation library
import pandas as pd # pandas is a library that allows us to work with DataFrames
import seaborn as sns
import spacy
from cleantext import clean
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
from sklearn.metrics import ConfusionMatrixDisplay
from sklearn.metrics import accuracy_score, accuracy_score
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.svm import LinearSVC
from sklearn.neighbors import NearestNeighbors
from sklearn.naive_bayes import MultinomialNB
from scipy import stats
from sklearn.metrics import balanced_accuracy_score
from time import time as tt
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.semi_supervised import SelfTrainingClassifier

# Connect google colab to your google drive.
# Note that you need to be logged in to your google account for this step to work

from google.colab import drive
drive.mount('/content/drive')

# Load the data
data_df= pd.read_csv('/content/drive/MyDrive/100_fill_comp1804_coursework_dataset_23-24.csv')

# data_df_raw

# creating the dataframe for the task2 only taking the features we need for the task one
features_task2 = ['paragraph','lexicon_count', 'difficult_words', 'text_clarity']
task2_df = data_df[features_task2].copy()
task2_df

# drop duplicates
task2_df = task2_df.drop_duplicates()
print(f"Number of duplicates after dropping : {task2_df.duplicated().sum()}")

# creating new dataframe for the preprocessing
task2_df_text_preprocessing = task2_df.copy()

print('How many texts have the newline character "\\n"?')
#I'm using the backslash symbol twice so that python doesn't actually start a new line! The extra backslash is called an "escape character".

print(task2_df_text_preprocessing['paragraph'].str.contains("\n").sum())

# paragraph cleaning.
from cleantext import clean

def clean_text(x):
  """ Define standard cleaning procedure """
  return clean(x,
    fix_unicode=True,               # fix various unicode errors
    lower=True,                     # change all text to lowercase
    no_line_breaks=True,           # this removes occurrences of the newline character "\n"
    no_punct=False,                 # let's NOT remove punctuations for the time being
    no_urls=True,                  # replace all URLs with a special token (below)
    replace_with_url="",          # we decide to replace urls with nothing
    no_emails=True,                # replace all email addresses with a special token
    replace_with_email="",        # we decide to replace emails with nothing
    no_phone_numbers=True,         # replace all phone numbers with a special token
    replace_with_phone_number="",   # we decide to replace phone numbers with nothing
    lang="en"                       # set to 'de' for German special handling
    )


  # not removing punctiation now will deal with it after splitting in to tokens.

task2_df_text_preprocessing[['clean_paragraph']] = task2_df_text_preprocessing[['paragraph']].apply(lambda x: x.apply(clean_text))

task2_df_text_preprocessing

# Tokenization
# Create an NLP pipeline
nlp = spacy.load('en_core_web_md')

# let's create a nice function to tokenize a single text document
import string
EXTRA_PUNCT = string.punctuation

# import Spacy
import spacy
# create the Spacy pipeline
nlp = spacy.load('en_core_web_md')

def preprocess_text_with_spacy(text_):
  """
  This function takes a Spacy doc and returns the list of its lemmas,
  after removing stop words and punctuations
  """
  # process document with Spacy
  # Note that if we were to first run all the documents through Spacy
  # (remember the nlp.pipe()) it would be faster because Spacy processes
  # multiple documents in parallel. However we'd have to create an intermediate
  # variable or column where to store all the Spacy objects, then process them
  # one by one and add the results to our dataframe.
  doc_ = nlp(text_)
  # here we take the lemmas, and now we also want to but only keep those that are NOT stop words, only digits, or punctuation.
  lemmas_ = [token.lemma_ for token in doc_ if not (token.is_stop or token.is_punct or token.is_digit)]
  # remember when I said punctuation is tricky?
  # Spacy misses some characters that we want to remove that can also be considered punctuation (= and +)
  # Here is where we remove them
  return [lemma for lemma in lemmas_ if lemma not in EXTRA_PUNCT]

from time import time as tt
t0 = tt()
task2_df_text_preprocessing['tokenized_paragraph'] = task2_df_text_preprocessing['clean_paragraph'].apply(preprocess_text_with_spacy)
print(f'Time elapsed is {(tt()-t0):.2f} seconds')
task2_df_text_preprocessing

# let's create a nice function to tokenize a single text document
import string
EXTRA_PUNCT = string.punctuation

# import Spacy
import spacy
# create the Spacy pipeline
nlp = spacy.load('en_core_web_md')


# Let's make the easy function first, where we simply return Spacy's default document embedding.
def get_spacy_doc_embedding(text_):
  ''' Given a text document, return the Spacy document embedding. '''
  doc_ = nlp(text_)
  return doc_.vector

# Now the more convoluted way.
def compute_avg_lemma_embedding(text_):
  """
  This function takes a Spacy doc and returns the average word embedding,
  ONLY for selected tokens.
  """

  doc_ = nlp(text_)
    # We will do something slightly different than last time. Today, we compute the
  # average word embedding only based on selected lemmas.
  avg_embedding = np.zeros_like(doc_.vector)
  token_counter = 0
  for token in doc_:
    if (token.is_stop or token.is_punct or token.is_digit or (token.lemma_ in EXTRA_PUNCT)):
      continue
    avg_embedding += token.vector
    token_counter+=1 # we keep track of this to turn the sum into an average

  if token_counter>0:
    avg_embedding = avg_embedding/token_counter
  return avg_embedding

# embed training data (it takes a bit more than 2 minutes! A bit of patience is needed)
# (use the cleaned text!)
from time import time as tt
t0 = tt()
# Note a couple of new things in the following application of the apply function:
# 1. The resulting embedding for each row is a list of number.
# 2. Since the plan is to join it back to the original dataframe, we want the result
# to be returned as a dataframe itself to make things easier later on (which is why we wrap the result into pd.Series())

# Join the list of tokens into a single string
task2_df_text_preprocessing['tokenized_paragraph_str'] = task2_df_text_preprocessing['tokenized_paragraph'].apply(lambda x: ' '.join(x))

task2_df_emb = task2_df_text_preprocessing['tokenized_paragraph_str'].apply(lambda x: pd.Series(get_spacy_doc_embedding(x)))

# 3. since they have the same index we can join the dataframe with the word embeddings with the old one
task2_df_new = task2_df_emb.join(task2_df_text_preprocessing[['tokenized_paragraph','clean_paragraph','lexicon_count','difficult_words','text_clarity']])
# the next line is just because scikit-learn doesn't like column names that are not strings
task2_df_new.columns = task2_df_new.columns.astype(str)
print(f'Time elapsed is {(tt()-t0):.2f} seconds')
task2_df_new

good_data = task2_df_text_preprocessing[["tokenized_paragraph", "lexicon_count",	"difficult_words",	"text_clarity"]]
good_data_bkp = good_data

task2_df_new

# Step 3: Split the data into features and target variable
clean_raw_data = task2_df_new.drop(columns=["tokenized_paragraph",	"clean_paragraph"], inplace=False)
clean_raw_data.dropna(subset=[col for col in clean_raw_data.columns if col != 'text_clarity'], inplace=True)

# clean_raw_data.dropna(inplace=True)

training_data = clean_raw_data[:99]
# training_data.dropna(inplace=True)

label_encoder = LabelEncoder()
training_data['text_clarity'] = label_encoder.fit_transform(training_data['text_clarity'])

X = training_data.drop(columns=["text_clarity"], inplace=False)
y = training_data['text_clarity']

y.value_counts()

from sklearn.model_selection import train_test_split
from imblearn.over_sampling import RandomOverSampler


# Step 4: Split the data into train and temporary sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Step 5: Handle class imbalance by oversampling the minority classes on training data
oversampler = RandomOverSampler()
X_resampled, y_resampled = oversampler.fit_resample(X_train, y_train)

y_resampled.value_counts()

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
# from sklearn.compose import ColumnTransformer


# Define ColumnTransformer
ct = ColumnTransformer(
    transformers=[
        (
            "scaling",  # name of the transformation
            StandardScaler(),  # scaler to apply
            [str(i) for i in range(300)]  # columns to scale
        )
    ],
    remainder="passthrough",  # keep non-transformed columns
    verbose_feature_names_out=False  # keep column names simple
)

# Step 6: Create a pipeline including logistic regression classifier and hyperparameter tuning
pipeline = Pipeline([
     ('scaling', ct),  # scaling step
    ('classifier', LogisticRegression(max_iter= 100))  # Logistic Regression classifier
])

# Step 7: Define hyperparameters grid for tuning
param_grid = {
    'classifier__C': [0.001, 0.01, 0.1, 1, 10, 100],  # Regularization parameter
    'classifier__penalty': ['l1', 'l2']  # Penalty norm
}

# Step 8: Perform Grid Search Cross-Validation to find the best hyperparameters
grid_search = GridSearchCV(pipeline, param_grid, cv=5, scoring='accuracy', verbose=1)
grid_search.fit(X_resampled, y_resampled)

# Best hyperparameters found
best_params = grid_search.best_params_
print("Best Hyperparameters:", best_params)

# Step 9: Train the pipeline with the best hyperparameters on the available labeled data
best_pipeline = grid_search.best_estimator_
best_pipeline.fit(X_resampled, y_resampled)

# Step 10: Evaluate the model
predictions = best_pipeline.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print("Test accuracy:", accuracy)

import pandas as pd

# Assuming 'label_encoder' is already defined and 'clean_raw_data' is your DataFrame

# Step 1: Separate out rows with missing 'text_clarity'
missing_values = clean_raw_data[clean_raw_data['text_clarity'].isnull()].copy()

# Step 2: Drop 'text_clarity' column for prediction
missing_values.drop(columns=['text_clarity'], inplace=True)

# Step 3: Predict missing values
predicted_values = best_pipeline.predict(missing_values)

# Step 4: Inverse transform the predicted labels to get the original string labels
predicted_labels = label_encoder.inverse_transform(predicted_values)

# Step 5: Assign predicted values back to the missing rows
missing_values['text_clarity'] = predicted_labels

# Step 6: Join predicted values back with the original dataframe
clean_raw_data.update(missing_values)

# Step 7: Check value counts after filling missing values
print(clean_raw_data['text_clarity'].value_counts())

# task1_data_ready_to_split DataFrame resuffle
shuffled_df = clean_raw_data.sample(frac=1.0, random_state=42)  # Set random_state for reproducibility

# dataframe before suffling
# shuffled_df
# Reset the index if needed
shuffled_df.reset_index(drop=True, inplace=True)

# Display the shuffled DataFrame
shuffled_df

clean_raw_task2 = shuffled_df.copy()


from sklearn.preprocessing import LabelEncoder
lblEncoder_X = LabelEncoder()
lblEncoder_X = lblEncoder_X.fit(clean_raw_task2['text_clarity'])

clean_raw_task2['label_clarity'] = lblEncoder_X.transform(clean_raw_task2['text_clarity'])
print(clean_raw_task2['label_clarity'].value_counts())


clean_raw_task2

#unnecessary column dropped.
clean_raw_task2_bef = clean_raw_task2.copy()
columns_to_drop = ['text_clarity']
task2_bef = clean_raw_task2_bef.drop(columns=columns_to_drop, inplace=False)
task2_bef

# X contains features, y contains labels
X_task2= task2_bef.drop(columns=['label_clarity'], inplace=False)
# print(task1_data_ready_to_split)
y_task2 = task2_bef['label_clarity']  # Specify the column containing the target variable
# print(X_task2,y_task2)

from sklearn.model_selection import train_test_split

# Splitting data in to train test and validation in the ratio of 60:20:20.
# Split the data into training and test sets
X_train_before, X_test, y_train_before, y_test = train_test_split(X_task2, y_task2, test_size=0.2, random_state=42)

# Further split the training data into training and validation sets
X_train, X_val, y_train, y_val = train_test_split(X_train_before, y_train_before, test_size=0.25, random_state=42)

from imblearn.over_sampling import RandomOverSampler

# Applying RandomOverSampler to balance the training data
oversampler = RandomOverSampler(random_state=0)
X_train_resampled, y_train_resampled = oversampler.fit_resample(X_train, y_train)

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression

# Define ColumnTransformer
ct = ColumnTransformer(
    transformers=[
        (
            "scaling",  # name of the transformation
            StandardScaler(),  # scaler to apply
            [str(i) for i in range(300)]  # columns to scale
        )
    ],
    remainder="passthrough",  # keep non-transformed columns
    verbose_feature_names_out=False  # keep column names simple
)

# Create the pipeline
clf_ = Pipeline(
    steps=[
        ('scaling', ct),  # scaling step
        ('clf', LogisticRegression())  # logistic regression classifier
    ]
)

# Define hyperparameters for grid search
hparameters = {
    'clf__penalty': ['l2'],
    'clf__C': [0.001, 0.01, 0.1, 1, 10],  # Expanded range
}

# Grid search
clf_search = GridSearchCV(
    clf_,  # pipeline object
    hparameters,  # hyperparameters to tune
    scoring='accuracy',  # evaluation metric
    cv=5,  # cross-validation folds
    return_train_score=True  # return training scores
)

from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from time import time as tt


# create the GridSearch function
# original data
clf_search = GridSearchCV(clf_, hparameters, scoring= "accuracy", cv= 5,
                          return_train_score=True)

# let's also time it (it's goint to take time, nothing's wrong!)
t0 = tt()
_ =clf_search.fit(X_train_resampled, y_train_resampled)
print(f'Time taken to train gridsearch: {tt()-t0:.2f} seconds.')

# evaluation
cv_res = pd.DataFrame(clf_search.cv_results_)
interesting_columns = ['mean_test_score','std_test_score','mean_train_score','std_train_score']
interesting_columns = interesting_columns + [t for t in cv_res.columns if 'param_' in t]
cv_res[interesting_columns]

# Get the best estimator for further analysis of the results using the test set
# Does it still perform well?
best_clf = clf_search.best_estimator_
print(best_clf)

# validation
# Compute predictions and evaluation metrics using the best estimator
# original data
y_validation = best_clf.predict(X_val)
print(classification_report(y_val, y_validation, target_names = ['clear_enough', 'not_clear_enough'] ))

cm= ConfusionMatrixDisplay.from_estimator(best_clf, X_val, y_val)

# testing
# Compute predictions and evaluation metrics using the best estimator
# original data
y_test_predicted = best_clf.predict(X_test)
print(classification_report(y_test, y_test_predicted, target_names = ['clear_enough', 'not_clear_enough'] ))

cm= ConfusionMatrixDisplay.from_estimator(best_clf, X_test, y_test)

# trivial baseline
from sklearn.dummy import DummyClassifier
trivial_clf = DummyClassifier(strategy="stratified")
trivial_clf.fit(X_train, y_train)

y_trivial = trivial_clf.predict(X_test)
print(classification_report(y_test, y_trivial, target_names = ['clear_enough', 'not_clear_enough'] ))

cm= ConfusionMatrixDisplay.from_estimator(trivial_clf,X_test , y_test)