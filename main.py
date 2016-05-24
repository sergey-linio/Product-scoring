from flask import Flask, render_template, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import exc
import json
from validator_helper import CategoryValidator, ImageValidator, TextValidator, NegativeValidator
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

from models import *


@app.route('/api/send_scores/<category_id>', methods=['POST'])
def get_scores(category_id):

    if not category_id.isdigit():
        abort(404)
    try:
        category = Category.query.filter(Category.category_id == category_id).one()
    except exc.NoResultFound:
        abort(404)

    scores = {}
    for key, value in request.form.items():
        if value:
            try:
                value = float(value)
            except ValueError:
                continue
            scores[key] = value
    category.scores = json.dumps(scores)
    db.session.add(category)
    db.session.commit()
    return ''


@app.route('/')
def root():
    categories = Category.query.filter(Category.level == 1).all()
    categories = filter(
        lambda x: filter(lambda a: x.category_id in a.get_parents(), Category.query.filter(Category.level == 2).all()),
        categories
    )
    return render_template(
        'select_category.html',
        categories=categories,
    )


@app.route('/<category_id>')
def show_subcategories(category_id):
    if not category_id.isdigit():
        abort(404)
    try:
        category = Category.query.filter(Category.category_id == category_id).one()
    except exc.NoResultFound:
        abort(404)

    children = filter(lambda x: int(category_id) in x.get_parents(), Category.query.filter(Category.level == 2).all())
    return render_template(
        'select_subcategory.html',
        category=category,
        children=children
    )


@app.route('/<parent_id>/<category_id>')
def show_params(parent_id, category_id):
    try:
        parent = Category.query.filter(Category.category_id == parent_id).one()
        category = Category.query.filter(Category.category_id == category_id).one()
    except exc.NoResultFound:
        abort(404)
    images_validators = [
        {
            'name': function.split('validate_')[1],
            'text': getattr(ImageValidator, function).__doc__
        }
        for function in ImageValidator.get_validators_name()
    ]
    category_validators = [
        {
            'name': function.split('validate_')[1],
            'text': getattr(CategoryValidator, function).__doc__
        }
        for function in CategoryValidator.get_validators_name()
    ]
    content_validators = [
        {
            'name': function.split('validate_')[1],
            'text': getattr(TextValidator, function).__doc__
        }
        for function in TextValidator.get_validators_name()
    ]
    negative_validators = [
        {
            'name': function.split('validate_')[1],
            'text': getattr(NegativeValidator, function).__doc__
        }
        for function in NegativeValidator.get_validators_name()
    ]

    return render_template(
        'categories.html',
        category=category,
        parent_category=parent,
        images_validators=images_validators,
        content_validators=content_validators,
        category_validators=category_validators,
        negative_validators=negative_validators,
    )


if __name__ == '__main__':
    app.run(port=8000, debug=True)
