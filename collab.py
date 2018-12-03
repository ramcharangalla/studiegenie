import sys
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import optparse


test = [{'id':1,'text': 'hello how are you Worlds best Sachin'},
		{'id':2,'text': 'hello how are you'},
		{'id':3,'text': 'Sachin is the best'},
		{'id':4,'text': 'Worlds best Sachin'},
		{'id':4,'text': 'hi'}
		]

df = pd.DataFrame(test)
ans = df.loc[df['id'] == 4]
print(ans['text'].tolist())
tfidf = TfidfVectorizer()
tfidf_matrix = tfidf.fit_transform(df['text'])
print('Users vs Features(Words)')
print(tfidf_matrix.shape)
id_indices = pd.Series(df.index, index=df['id']).drop_duplicates()
indices_id = pd.Series(df['id'], index=df.index).drop_duplicates()
print(indices_id)
cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

user = 3
idx = id_indices[user]
print('Cosine sim')
print(cosine_sim[idx])

sim_scores = list(enumerate(cosine_sim[idx]))
print(sim_scores)
sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
sim_scores = sim_scores[1:11]
print(sim_scores)