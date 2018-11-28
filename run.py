from flaskblog import app
from flaskblog import db

def create_tables():
    db.create_all()



if __name__=='__main__':
    create_tables()
    app.run(debug=True)
