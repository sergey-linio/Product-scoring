from sqlalchemy import Column, Integer, String
from main import db
import json


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String)
    level = db.Column(db.Integer)
    parents = db.Column(db.String)
    scores = db.Column(db.String)

    def __init__(self, category_id=None, name=None, level=None, parents=None, scores=None):
        self.category_id = category_id
        self.name = name
        self.level = level
        self.parents = json.dumps(parents)
        self.scores = json.dumps(scores)

    def get_scores(self):
        return json.loads(self.scores) or {}

    def get_parents(self):
        return json.loads(self.parents) or []

    def __repr__(self):
        return '<Category %r>' % (self.id)
