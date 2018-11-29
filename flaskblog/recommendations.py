import numpy as np
import scipy
import pandas as pd
import math
import random
import sklearn
from nltk.corpus import stopwords
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse.linalg import svds
from create_notes import get_notes_df,get_interactions_df

def smooth_user_preference(x):
	return math.log(1+x, 2)

event_type_strength = {
   'VIEW': 1.0,
   'LIKE': 2.0, 
   'BOOKMARK': 2.5, 
   'FOLLOW': 3.0,
   'COMMENT CREATED': 4.0,  
}
notes_df = get_notes_df()
interactions_df = get_interactions_df()
print notes_df.head(2)
print interactions_df.head(2)

note_id = 'contentId'
notes_userid = 'authorPersonId'
content_col = 'text'
interactions_userid = 'personId'

interactions_df['eventStrength'] = interactions_df['eventType'].apply(lambda x: event_type_strength[x])
	#print interactions_df.head(3)
users_interactions_count_df = interactions_df.groupby([interactions_userid, note_id]).size().groupby(interactions_userid).size()
#print('# users: %d' % len(users_interactions_count_df))
users_with_enough_interactions_df = users_interactions_count_df[users_interactions_count_df >= 5].reset_index()[[interactions_userid]]
#print('# users with at least 5 interactions: %d' % len(users_with_enough_interactions_df))


#print('# of interactions: %d' % len(interactions_df))
interactions_from_selected_users_df = interactions_df.merge(users_with_enough_interactions_df, 
               how = 'right',
               left_on = interactions_userid,
               right_on = interactions_userid)
#print('# of interactions from users with at least 5 interactions: %d' % len(interactions_from_selected_users_df))


interactions_full_df = interactions_from_selected_users_df \
                    .groupby([interactions_userid, note_id])['eventStrength'].sum() \
                    .apply(smooth_user_preference).reset_index()
interactions_full_indexed_df = interactions_full_df.set_index(interactions_userid)


def get_items_interacted(userid, interactions_df):
	    # Get the user's data and merge in the movie information.
	    interacted_items = interactions_df.loc[userid][note_id]
	    return set(interacted_items if type(interacted_items) == pd.Series else [interacted_items])

class ProfileBuilder:
	def __init__(self,tfidf_matrix,item_ids):
		self.tfidf_matrix = tfidf_matrix
		self.item_ids = item_ids

	def get_item_profile(self,item_id):
	    idx = self.item_ids.index(item_id)
	    item_profile = self.tfidf_matrix[idx:idx+1]
	    return item_profile

	def get_item_profiles(self,ids):
	    item_profiles_list = [self.get_item_profile(x) for x in ids]
	    item_profiles = scipy.sparse.vstack(item_profiles_list)
	    return item_profiles

	def build_users_profile(self,person_id, interactions_indexed_df):
	    interactions_person_df = interactions_indexed_df.loc[person_id]
	    user_item_profiles = self.get_item_profiles(interactions_person_df[note_id])
	    
	    user_item_strengths = np.array(interactions_person_df['eventStrength']).reshape(-1,1)
	    #Weighted average of item profiles by the interactions strength
	    user_item_strengths_weighted_avg = np.sum(user_item_profiles.multiply(user_item_strengths), axis=0) / np.sum(user_item_strengths)
	    user_profile_norm = sklearn.preprocessing.normalize(user_item_strengths_weighted_avg)
	    return user_profile_norm

	def build_users_profiles(self): 
	    interactions_indexed_df = interactions_full_df[interactions_full_df[note_id] \
	                                                   .isin(notes_df[note_id])].set_index(interactions_userid)
	    user_profiles = {}
	    for person_id in interactions_indexed_df.index.unique():
	        user_profiles[person_id] = self.build_users_profile(person_id, interactions_indexed_df)
	    return user_profiles



class PopularityRecommender:
    
    MODEL_NAME = 'Popularity'
    
    def __init__(self, popularity_df, items_df=None):
        self.popularity_df = popularity_df
        self.items_df = items_df
        
    def get_model_name(self):
        return self.MODEL_NAME

    def get_items_interacted(self,userid, interactions_df):
	    # Get the user's data and merge in the movie information.
	    interacted_items = interactions_df.loc[userid][note_id]
	    return set(interacted_items if type(interacted_items) == pd.Series else [interacted_items])
        
    def recommend_items(self, user_id, items_to_ignore=[], topn=10, verbose=False):
        # Recommend the more popular items that the user hasn't seen yet.
        recommendations_df = self.popularity_df[~self.popularity_df[note_id].isin(items_to_ignore)] \
                               .sort_values('eventStrength', ascending = False) \
                               .head(topn)

        if verbose:
            if self.items_df is None:
                raise Exception('"items_df" is required in verbose mode')

            recommendations_df = recommendations_df.merge(self.items_df, how = 'left', 
                                                          left_on = note_id, 
                                                          right_on = note_id)[['eventStrength', note_id, content_col]]


        return recommendations_df


class ContentBasedRecommender:
    
    MODEL_NAME = 'Content-Based'
    
    def __init__(self, item_ids,items_df,user_profiles,tfidf_matrix):
        self.item_ids = item_ids
        self.items_df = items_df
        self.user_profiles = user_profiles
        self.tfidf_matrix = tfidf_matrix
        
    def get_model_name(self):
        return self.MODEL_NAME
        
    def _get_similar_items_to_user_profile(self, person_id, topn=1000):
        #Computes the cosine similarity between the user profile and all item profiles
        cosine_similarities = cosine_similarity(self.user_profiles[person_id], self.tfidf_matrix)
        #Gets the top similar items
        similar_indices = cosine_similarities.argsort().flatten()[-topn:]
        #Sort the similar items by similarity
        similar_items = sorted([(self.item_ids[i], cosine_similarities[0,i]) for i in similar_indices], key=lambda x: -x[1])
        return similar_items
        
    def recommend_items(self, user_id, items_to_ignore=[], topn=10, verbose=False):
        similar_items = self._get_similar_items_to_user_profile(user_id)
        #Ignores items the user has already interacted
        similar_items_filtered = list(filter(lambda x: x[0] not in items_to_ignore, similar_items))
        
        recommendations_df = pd.DataFrame(similar_items_filtered, columns=[note_id, 'recStrength']) \
                                    .head(topn)

        if verbose:
            if self.items_df is None:
                raise Exception('"items_df" is required in verbose mode')

            recommendations_df = recommendations_df.merge(self.items_df, how = 'left', 
                                                          left_on = note_id, 
                                                          right_on = note_id)[['recStrength', note_id,content_col]]

        return recommendations_df


def get_personal_recommendations(for_user_id,topn=10,verbose=False):
	
	
	#print('# of unique user/item interactions: %d' % len(interactions_full_df))
	#print interactions_full_df.head(9)

	item_popularity_df = interactions_full_indexed_df.groupby(note_id)['eventStrength'].sum().sort_values(ascending=False).reset_index()
	#print item_popularity_df.head(10)

	popularity_model = PopularityRecommender(item_popularity_df, notes_df)
	recommendations_df = popularity_model.recommend_items(for_user_id,items_to_ignore=popularity_model.get_items_interacted(for_user_id,interactions_full_indexed_df),topn=topn,verbose=verbose)
	print 'Recommended items: Trending notes'
	print recommendations_df.head(10)


def get_content_based_recommendations(for_user_id,topn=10,verbose=False):
	stopwords_list = stopwords.words('english')
	vectorizer = TfidfVectorizer(analyzer='word',
                     ngram_range=(1, 2),
                     min_df=0.003,
                     max_df=0.5,
                     max_features=5000,
                     stop_words=stopwords_list)
	item_ids = notes_df[note_id].tolist()
	tfidf_matrix = vectorizer.fit_transform(notes_df[content_col])
	tfidf_feature_names = vectorizer.get_feature_names()
	#print tfidf_matrix
	profile_builer = ProfileBuilder(tfidf_matrix,item_ids)
	user_profiles = profile_builer.build_users_profiles()
	content_based_recommender_model = ContentBasedRecommender(item_ids, notes_df,user_profiles,tfidf_matrix)
	recommendations_df = content_based_recommender_model.recommend_items(for_user_id,items_to_ignore=get_items_interacted(for_user_id,interactions_full_indexed_df),topn=topn,verbose=verbose)
	print recommendations_df.head(10)





if __name__ == '__main__':
	user_id = -1479311724257856983
	#get_personal_recommendations(-1479311724257856983,topn=10,verbose=True)
	get_content_based_recommendations(user_id,topn=10,verbose=True)
