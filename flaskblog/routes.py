from flask import Flask, render_template, url_for, flash, redirect, request, abort, session
from flaskblog.forms import RegistrationForm, LoginForm, NoteForm, NoteFormUpdate, LikeForm
from flaskblog import app,db,bcrypt
from flask_login import login_user,current_user,logout_user, login_required
from flaskblog.models import User, Tag, Note, Interaction
import datetime
from flaskblog.recommendations import get_personal_recommendations,get_content_based_recommendations
import numpy as np
now = datetime.datetime.now()

note_id = 'contentId'
notes_userid = 'authorPersonId'
content_col = 'text'
interactions_userid = 'personId'


class RecNote:
    def __init__(self,id,content,author,title,date,author_name):
        self.id = id
        self.title = title
        self.date_created = date
        self.user_id = author
        self.content = content
        self.author_name = author_name


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
    names = ['John','Gary','Robert','George','Stephen']
    #notes = Note.query.order_by(Note.date_created.desc()).filter_by(mode='public').all()
    user_id = -1479311724257856983
    recs = []
    rec_df = get_content_based_recommendations(-1479311724257856983,topn=10,verbose=True)
    #return print(rec_df.head(2))
    for index,row in rec_df.iterrows():
        mynote = RecNote(row[note_id],row[content_col],row[notes_userid],row['title'],row['timestamp'],names[np.random.randint(0,5)])
        recs.append(mynote)
    return render_template('home.html', notes = recs)

@app.route("/note/<int:note_id>/like", methods=['GET', 'POST'])
@login_required
def like(note_id):
    notes = Note.query.get_or_404(note_id)
    like = session.get('likes')
    if like != 0:
        notes.likes = notes.likes - 1
        session['likes'] = 0
        db.session.commit()
    else:
        notes.likes = notes.likes + 1
        session['likes'] = 1
        db.session.commit()
    notes1 = Note.query.order_by(Note.date_created.desc()).filter_by(mode='public').all()
    return render_template('home.html', notes = notes1)

@app.route("/note/<int:note_id>/bookmark", methods=['GET', 'POST'])
@login_required
def bookmark(note_id):
    notes = Note.query.get_or_404(note_id)
    users = User.query.filter_by(id=current_user.id).first_or_404()
    interaction = Interaction(date = now, event='bookmark', user_id = users.id, note_id = note_id)
    db.session.add(interaction)
    db.session.commit()
    notes1 = Note.query.order_by(Note.date_created.desc()).filter_by(mode='public').all()
    return render_template('home.html', notes = notes1)

@app.route("/note/<int:note_id>/follow", methods=['GET', 'POST'])
@login_required
def follow(note_id):
    notes = Note.query.get_or_404(note_id)
    users = User.query.filter_by(id=current_user.id).first_or_404()
    interaction = Interaction(date = now, event='follow', user_id = users.id, note_id = note_id)
    db.session.add(interaction)
    db.session.commit()
    notes1 = Note.query.order_by(Note.date_created.desc()).filter_by(mode='public').all()
    return render_template('home.html', notes = notes1)

@app.route("/note/<int:note_id>/comment", methods=['GET', 'POST'])
@login_required
def comment(note_id):
    notes = Note.query.get_or_404(note_id)
    users = User.query.filter_by(id=current_user.id).first_or_404()
    interaction = Interaction(date = now, event='comment', user_id = users.id, note_id = note_id)
    db.session.add(interaction)
    db.session.commit()
    notes1 = Note.query.order_by(Note.date_created.desc()).filter_by(mode='public').all()
    return render_template('home.html', notes = notes1)



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
        flash('Note has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_note.html', title='New Note', form=form, legend='New Note')

@app.route("/note/<int:note_id>")
def note(note_id):
    notes = Note.query.get_or_404(note_id)
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
