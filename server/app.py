#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')
        
        if not username or not password:
            return {"error": "Username and password are required."}, 422

        try:
            new_user = User(username=username, password=password, image_url=image_url, bio=bio)
            db.session.add(new_user)
            db.session.commit()

            session['user_id'] = new_user.id

            return {
                "id": new_user.id,
                "username": new_user.username,
                "image_url": new_user.image_url,
                "bio": new_user.bio
            }, 201
        except IntegrityError:
            db.session.rollback()
            return {"error": "Username already exists."}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            return {
                    "id": user.id,
                    "username": user.username,
                    "image_url": user.image_url,
                    "bio": user.bio
                }, 200
        return {"error": "Unauthorized"}, 401


class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            session['user_id'] = user.id
            return {
                "id": user.id,
                "username": user.username,
                "image_url": user.image_url,
                "bio": user.bio
            }
        return {"error": "Invalid credentials"}, 401

class Logout(Resource):
    def delete(self):
        if 'user_id' in session:
            session.pop('user_id', None)
            return {}, 204
        return {"error": "Unauthorized"}, 401


class RecipeIndex(Resource):
    def get(self):
        if 'user_id' in session:
            recipes = Recipe.query.all()
            recipes_data = [
                {
                    "title": recipe.title,
                    "instructions": recipe.instructions,
                    "minutes_to_complete": recipe.minutes_to_complete,
                    "user": {
                        "id": recipe.user.id,
                        "username": recipe.user.username,
                        "image_url": recipe.user.image_url,
                        "bio": recipe.user.bio
                    }
                }
                for recipe in recipes
            ]
            return recipes_data, 200
        return {"error": "Unauthorized"}, 401

    def post(self):
        if 'user_id' in session:
            data = request.get_json()
            title = data.get('title')
            instructions = data.get('instructions')
            minutes_to_complete = data.get('minutes_to_complete')

            if not all([title, instructions, minutes_to_complete]):
                return {"error": "Title, instructions, and minutes to complete are required."}, 422

            try:
                user_id = session['user_id']
                new_recipe = Recipe(
                    title=title,
                    instructions=instructions,
                    minutes_to_complete=minutes_to_complete,
                    user_id=user_id
                )
                db.session.add(new_recipe)
                db.session.commit()
                return {
                    "title": new_recipe.title,
                    "instructions": new_recipe.instructions,
                    "minutes_to_complete": new_recipe.minutes_to_complete,
                    "user": {
                        "id": new_recipe.user.id,
                        "username": new_recipe.user.username,
                        "image_url": new_recipe.user.image_url,
                        "bio": new_recipe.user.bio
                    }
                }, 201
            except IntegrityError:
                db.session.rollback()
                return {"error": "Could not create recipe."}, 422
        return {"error": "Unauthorized"}, 401


api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)