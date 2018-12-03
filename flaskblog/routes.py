from flask import Flask, render_template, url_for, flash, redirect, request, abort, session
from flaskblog.forms import RegistrationForm, LoginForm, NoteForm, NoteFormUpdate, LikeForm
from flaskblog import app,db,bcrypt
from flask_login import login_user,current_user,logout_user, login_required
from flaskblog.models import User, Tag, Note, Interaction, get_notes_df, get_interactions_df
import datetime
now = datetime.datetime.now()
import math
import pandas as pd

import numpy as np
import scipy
import math
import random
import sklearn
from nltk.corpus import stopwords
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse.linalg import svds
from sklearn.metrics.pairwise import linear_kernel
from elasticsearch import Elasticsearch
app.es = Elasticsearch('http://localhost:9200')
app.index_name = 'notes'
def smooth_user_preference(x):
    return math.log(1+x, 2)

event_type_strength = {
   'view': 1.0,
   'like': 2.0, 
   'bookmark': 2.5, 
   'follow': 3.0,
   'comment': 4.0,
}
note_id = 'contentId'
notes_userid = 'authorPersonId'
content_col = 'text'
interactions_userid = 'personId'

def add_notes_to_index():
    check_index = None
    try:
        check_index = app.es.indices.get_alias(app.index_name)
    except Exception as detail:
        pass
    if check_index is None:
        notes = Note.query.all()
        for note in notes:
            add_to_index(app.index_name,note)
    else:
        print('Indexing done')

def update_cache():
    app.notes_df = get_notes_df()
    app.interactions_df,app.user_words_df  = get_interactions_df()
    print('user vs words shape')
    print(app.user_words_df.head(1))
    app.interactions_df['eventStrength'] = app.interactions_df['eventType'].apply(lambda x: event_type_strength[x])

    app.users_interactions_count_df = app.interactions_df.groupby([interactions_userid, note_id]).size().groupby(interactions_userid).size()

    app.users_with_enough_interactions_df = app.users_interactions_count_df[app.users_interactions_count_df >= 0].reset_index()[[interactions_userid]]

    app.interactions_from_selected_users_df = app.interactions_df.merge(app.users_with_enough_interactions_df, 
                   how = 'right',
                   left_on = interactions_userid,
                   right_on = interactions_userid)


    app.interactions_full_df = app.interactions_from_selected_users_df \
                        .groupby([interactions_userid, note_id])['eventStrength'].sum() \
                        .apply(smooth_user_preference).reset_index()
    app.interactions_full_indexed_df = app.interactions_full_df.set_index(interactions_userid)

def get_items_interacted(userid, interactions_df):
    ret = []
    try:
        print('INTERACTED_ITEMS')
        interacted_items = interactions_df.loc[userid][note_id]
        print(interacted_items)
    except:
        print('EXCEPTION')
        pass
        return ret
    return set(interacted_items if type(interacted_items) == pd.Series else [interacted_items])


@app.route("/", methods=['GET', 'POST'])
@app.route("/index", methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            session['likes'] = 0
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('index.html', title='Login', form=form)


@app.route("/home")
def home():
    trending_notes = get_personal_recommendations(current_user.id,topn=20)
    content_notes = get_content_based_recommendations(current_user.id,topn=20)
    print('Content based IDS ')
    ids = content_notes['contentId']
    print(ids)
    trending_ids = trending_notes['contentId']
    print('Trending based IDS ')
    print(trending_ids)
    notes_c = []
    notes_t = []
    notes_collab = []
    for id_ in ids:
        notes_c.append(Note.query.filter_by(id = id_).first())
    for id_ in trending_ids:
        notes_t.append(Note.query.filter_by(id = id_).first())
    # else:
    #notes = Note.query.order_by(Note.date_created.desc()).filter_by(mode='public').all()
    collab_ids = get_collab_filtering(current_user.id,topn=10)
    for id_ in collab_ids:
        notes_collab.append(Note.query.filter_by(id = id_).first())

    return render_template('home.html', notes_trending = notes_t, recommendations_notes = notes_c,collab_notes =notes_collab )

@app.route("/note/<int:note_id>/like", methods=['GET', 'POST'])
@login_required
def like(note_id):
    notes = Note.query.get_or_404(note_id)
    notes.likes += 1
    db.session.commit()

    users = User.query.filter_by(id=current_user.id).first_or_404()
    interaction = Interaction(date = now, event='like', user_id = users.id, note_id = note_id)
    db.session.add(interaction)
    db.session.commit()
    update_cache()
    notes = Note.query.get_or_404(note_id)
    return render_template('note.html', note=notes)

@app.route("/note/<int:note_id>/bookmark", methods=['GET', 'POST'])
@login_required
def bookmark(note_id):
    notes = Note.query.get_or_404(note_id)
    users = User.query.filter_by(id=current_user.id).first_or_404()
    interaction = Interaction(date = now, event='bookmark', user_id = users.id, note_id = note_id)
    db.session.add(interaction)
    db.session.commit()
    notes1 = Note.query.order_by(Note.date_created.desc()).filter_by(mode='public').all()
    app.interactions_df = get_interactions_df()
    trending_notes = get_personal_recommendations(current_user.id,topn=1000)
    content_notes = get_content_based_recommendations(current_user.id,topn=7)
    ids = content_notes['contentId']
    trending_ids = trending_notes['contentId']
    notes_c =  Note.query.filter(Note.id.in_(ids)).all()
    notes_t =  Note.query.filter(Note.id.in_(trending_ids)).all()
    #notes = Note.query.order_by(Note.date_created.desc()).filter_by(mode='public').all()
    return render_template('home.html',notes_trending = notes_t, recommendations_notes = notes_c )

@app.route("/note/<int:note_id>/follow", methods=['GET', 'POST'])
@login_required
def follow(note_id):
    notes = Note.query.get_or_404(note_id)
    users = User.query.filter_by(id=current_user.id).first_or_404()
    interaction = Interaction(date = now, event='follow', user_id = users.id, note_id = note_id)
    db.session.add(interaction)
    db.session.commit()
    notes1 = Note.query.order_by(Note.date_created.desc()).filter_by(mode='public').all()
    app.interactions_df = get_interactions_df()
    trending_notes = get_personal_recommendations(current_user.id,topn=1000)
    content_notes = get_content_based_recommendations(current_user.id,topn=7)
    ids = content_notes['contentId']
    trending_ids = trending_notes['contentId']
    notes_c =  Note.query.filter(Note.id.in_(ids)).all()
    notes_t =  Note.query.filter(Note.id.in_(trending_ids)).all()
    #notes = Note.query.order_by(Note.date_created.desc()).filter_by(mode='public').all()
    return render_template('home.html', notes_trending = notes_t, recommendations_notes = notes_c)

@app.route("/note/<int:note_id>/comment", methods=['GET', 'POST'])
@login_required
def comment(note_id):
    notes = Note.query.get_or_404(note_id)
    users = User.query.filter_by(id=current_user.id).first_or_404()
    interaction = Interaction(date = now, event='comment', user_id = users.id, note_id = note_id)
    db.session.add(interaction)
    db.session.commit()
    notes1 = Note.query.order_by(Note.date_created.desc()).filter_by(mode='public').all()
    trending_notes = get_personal_recommendations(current_user.id,topn=1000)
    content_notes = get_content_based_recommendations(current_user.id,topn=7)
    ids = content_notes['contentId']
    trending_ids = trending_notes['contentId']
    notes_c =  Note.query.filter(Note.id.in_(ids)).all()
    notes_t =  Note.query.filter(Note.id.in_(trending_ids)).all()
    #notes = Note.query.order_by(Note.date_created.desc()).filter_by(mode='public').all()
    return render_template('home.html', notes_trending = notes_t, recommendations_notes = notes_c )



@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(firstname=form.firstname.data, lastname=form.lastname.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        interests = form.interests.data
        for interest in interests:
            tag=int(interest)
            tagid=Tag.query.filter_by(id=tag).first()
            user.usertags.append(tagid)
            db.session.commit()
        db.session.commit()
        flash(f'Account created for {form.firstname.data}!','success')
        return redirect(url_for('index'))
    return render_template('register.html', title='Register', form=form)



# @app.route("/login", methods=['GET', 'POST'])
# def login():
#     if current_user.is_authenticated:
#         return redirect(url_for('home'))
#     form = LoginForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         if user and bcrypt.check_password_hash(user.password, form.password.data):
#             login_user(user, remember=form.remember.data)
#             next_page = request.args.get('next')
#             return redirect(next_page) if next_page else redirect(url_for('home'))
#         else:
#             flash('Login Unsuccessful. Please check email and password', 'danger')
#     return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    session.pop('likes', None)
    logout_user()
    return redirect(url_for('index'))


@app.route("/account")
@login_required
def account():
    user = User.query.filter_by(id=current_user.id).first_or_404()
    notes = Note.query.order_by(Note.date_created.desc()).filter_by(user_id = current_user.id)
    notecount = Note.query.filter_by(user_id = current_user.id).count()
    return  render_template('account.html', notes = notes, count = notecount, user = user)

@app.route("/note/new", methods=['GET', 'POST'])
@login_required
def new_note():
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(title=form.title.data, content=form.content.data, user_id=current_user.id, date_created= now, mode=form.display_mode.data )
        db.session.add(note)
        db.session.commit()
        interests = form.interests.data
        for interest in interests:
            tag=int(interest)
            tagid=Tag.query.filter_by(id=tag).first()
            note.notetags.append(tagid)
            db.session.commit()
        db.session.commit()
        interaction = Interaction(date = now, event='comment', user_id = current_user.id, note_id = note.id)
        db.session.add(interaction)
        db.session.commit()
        update_cache()
        return redirect(url_for('home'))
    return render_template('create_note.html', title='New Note', form=form, legend='New Note')

@app.route("/note/<int:note_id>")
def note(note_id):
    notes = Note.query.get_or_404(note_id)
    users = User.query.filter_by(id=current_user.id).first_or_404()
    interaction = Interaction(date = now, event='view', user_id = users.id, note_id = note_id)
    db.session.add(interaction)
    db.session.commit()
    update_cache()
    return render_template('note.html', note=notes)

@app.route("/note/<int:note_id>/update", methods=['GET', 'POST'])
@login_required
def update_note(note_id):
    notes = Note.query.get_or_404(note_id)
    if notes.author.id != current_user.id:
        abort(403)
    form = NoteFormUpdate()
    if form.validate_on_submit():
        notes.title = form.title.data
        notes.content = form.content.data
        notes.mode = form.display_mode.data
        for n in notes.notetags:
            tagid=Tag.query.filter_by(id=n.id).first()
            notes.notetags.remove(tagid)
            db.session.commit()
        db.session.commit()
        interests = form.interests.data
        for interest in interests:
            tag=int(interest)
            tagid=Tag.query.filter_by(id=tag).first()
            notes.notetags.append(tagid)
            db.session.commit()
        db.session.commit()
        flash('Your Note has been updated!', 'success')
        return redirect(url_for('note', note_id=notes.id))
    elif request.method == 'GET':
        form.title.data = notes.title
        form.content.data = notes.content
        form.display_mode.data = notes.mode
        temp =[]
        for n in notes.notetags:
            temp.append(str(n.id))
        form.interests.data = temp
    return render_template('create_note.html', title='Update Note', form=form, legend='Update Note')



@app.route("/note/<int:note_id>/delete", methods=['POST'])
@login_required
def delete_note(note_id):
    notes = Note.query.get_or_404(note_id)
    if notes.author.id != current_user.id:
        abort(403)
    db.session.delete(notes)
    for n in notes.notetags:
        tagid=Tag.query.filter_by(id=n.id).first()
        notes.notetags.remove(tagid)
        db.session.commit()
    db.session.commit()
    flash('The Note has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route("/user/<int:user_id>")
def user_notes(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    notecount = Note.query.filter_by(user_id = user.id).count()
    notes = Note.query.filter_by(author=user)\
        .order_by(Note.date_created.desc())
    return render_template('user_notes.html', notes=notes, user=user, count = notecount)

@app.route("/tag/<int:tag_id>")
def tags(tag_id):
    tags = Tag.query.get_or_404(tag_id)
    tagcount = Tag.query.filter_by(id = tag_id).count()
    return render_template('tags.html', tags=tags, tagcount = tagcount)


@app.errorhandler(404)
def error_404(error):
    return render_template('404.html'), 404


@app.errorhandler(403)
def error_403(error):
    return render_template('403.html'), 403


@app.errorhandler(500)
def error_500(error):
    return render_template('500.html'), 500





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
        interactions_indexed_df = app.interactions_full_df[app.interactions_full_df[note_id] \
                                                       .isin(app.notes_df[note_id])].set_index(interactions_userid)
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
        try:
            interacted_items = interactions_df.loc[userid][note_id]
        except:
            pass
            return []
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
    item_popularity_df = app.interactions_full_indexed_df.groupby(note_id)['eventStrength'].sum().sort_values(ascending=False).reset_index()
    popularity_model = PopularityRecommender(item_popularity_df, app.notes_df)
    recommendations_df = popularity_model.recommend_items(for_user_id,items_to_ignore=get_items_interacted(for_user_id,app.interactions_full_indexed_df),topn=topn,verbose=verbose)
    #recommendations_df = popularity_model.recommend_items(for_user_id,items_to_ignore=[],topn=topn,verbose=verbose)
    return recommendations_df


def get_collab_filtering(for_user_id,topn=10):
    tfidf = TfidfVectorizer()
    df = app.user_words_df
    tfidf_matrix = tfidf.fit_transform(df['text'])
    print('Users vs Features(Words)')
    print(tfidf_matrix.shape)
    user_indices = pd.Series(df.index, index=df['user_id']).drop_duplicates()
    indices_user = pd.Series(df['user_id'], index=df.index).drop_duplicates()
    app.cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
    user = 3
    idx = user_indices[for_user_id]
    print('Cosine sim')
    print(app.cosine_sim[idx])

    sim_scores = list(enumerate(app.cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:11]
    print('Similar users')
    req_ids = set()
    already_interacted = get_items_interacted(for_user_id,app.interactions_full_indexed_df)
    for i in sim_scores:
        sim_user = indices_user[i[0]]
        this_user_notes = get_items_interacted(sim_user,app.interactions_full_indexed_df)
        for note in this_user_notes:
            if note not in already_interacted:
                req_ids.add(note)
    
    rec_ids  = list(req_ids)
    print('Recommended Nptes Collab')
    print(rec_ids)
    return rec_ids






def get_content_based_recommendations(for_user_id,topn=10,verbose=False):
    stopwords_list = stopwords.words('english')
    vectorizer = TfidfVectorizer(analyzer='word',
                     ngram_range=(1, 2),
                     min_df=0.003,
                     max_df=0.5,
                     max_features=5000,
                     stop_words=stopwords_list)
    item_ids = app.notes_df[note_id].tolist()
    tfidf_matrix = vectorizer.fit_transform(app.notes_df[content_col])
    tfidf_feature_names = vectorizer.get_feature_names()
    
    profile_builer = ProfileBuilder(tfidf_matrix,item_ids)
    user_profiles = profile_builer.build_users_profiles()
    content_based_recommender_model = ContentBasedRecommender(item_ids, app.notes_df,user_profiles,tfidf_matrix)
    recommendations_df = content_based_recommender_model.recommend_items(for_user_id,items_to_ignore=get_items_interacted(for_user_id,app.interactions_full_indexed_df),topn=topn,verbose=verbose)
    #recommendations_df = content_based_recommender_model.recommend_items(for_user_id,items_to_ignore=[],topn=topn,verbose=verbose)
    return recommendations_df


def add_to_index(index, note):
    if not app.es:
        return
    payload = {}
    payload['text'] = note.title + note.content
    app.es.index(index=index, doc_type=index, id=note.id,
                                    body=payload)

def remove_from_index(index, model):
    if not app.es:
        return
    app.es.delete(index=index, doc_type=index, id=model.id)


def search(query,index):
    result = query_index(index,query,1,10)
    result_notes = []
    for note in result['hits']['hits']:
        note_id = note['_id']
        actual_note = Note.query.filter_by(id=note_id).first()
        result_notes.append(actual_note)
    return result_notes



def query_index(index, query, page, per_page):
    if not app.es:
        return [], 0
    search = app.es.search(
        index=index, doc_type=index,
        body={'query': {'match': {'text':query}},'from': (page - 1) * per_page, 'size': per_page})
    return search