from datetime import datetime
from flaskblog import db, login_manager
from flask_login import UserMixin
import pandas as pd

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(20), nullable=False)
    lastname = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    note = db.relationship('Note', backref='author', lazy=True)


    def __repr__(self):
        return f"User('{self.firstname}', '{self.lastname}', '{self.email}','{self.id}')"

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    usertags = db.relationship('User', secondary='tagmapper', backref=db.backref('usertags', lazy='dynamic'))
    notetags = db.relationship('Note', secondary='notemapper', backref=db.backref('notetags', lazy='dynamic'))

    def __repr__(self):
        return f"Post('{self.id}', '{self.name}')"

class Interaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    event = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=False)

    def __repr__(self):
        return f"Interaction('{self.event}', '{self.user_id}', '{self.note_id}',, '{self.date}')"

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    mode = db.Column(db.String(10), nullable=False)
    likes = db.Column(db.Integer, default= 0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Note('{self.title}', '{self.date_created}','{self.mode}','{self.likes}')"


tagmapper = db.Table('tagmapper',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')))

notemapper = db.Table('notemapper',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('note_id', db.Integer, db.ForeignKey('note.id')))


def get_notes_df():
    #notes_df = pd.read_csv(notes_f)
    notes = Note.query.all()
    notes_list = []
    for note in notes:
        d = {}
        d['contentId'] = note.id
        d['authorPersonId'] = note.user_id
        d['title'] = note.title
        d['text'] = note.content
        notes_list.append(d)
    notes_df = pd.DataFrame(notes_list)
    return notes_df
def get_interactions_df():
    interactions = Interaction.query.all()
    inters = []
    for i in interactions:
        d = {}
        d['contentId'] = i.note_id
        d['personId'] = i.user_id
        d['eventType'] = i.event
        inters.append(d)
    interactions_df = pd.DataFrame(inters)
    return interactions_df
