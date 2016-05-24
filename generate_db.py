import pickle
import os

from main import db
from models import Category

data = pickle.load(open('data.pickle'))

try:
    os.remove('test.db')
except OSError:
    pass


db.drop_all()
db.create_all()

for element in data:
    c = Category(
        element['id'],
        element['name'],
        element['level'],
        element['parents'],
    )
    db.session.add(c)

db.session.commit()
