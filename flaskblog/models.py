from datetime import datetime
from flaskblog import db, login_manager
from flask_login import UserMixin

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
        return 'User {0} {1}'.format(self.id,self.firstname)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    usertags = db.relationship('User', secondary='tagmapper', backref=db.backref('usertags', lazy='dynamic'))
    notetags = db.relationship('Note', secondary='notemapper', backref=db.backref('notetags', lazy='dynamic'))

    def __repr__(self):
        return "Post('{self.id}', '{self.name}')"

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return "Note('{self.title}', '{self.date_created}')"

tagmapper = db.Table('tagmapper',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')))

notemapper = db.Table('notemapper',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('note_id', db.Integer, db.ForeignKey('note.id')))
