from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from models import db, User, Admin, Patient, Availability
from flask_migrate import Migrate
from flask_restful import Api, Resource
import os

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

db.init_app(app)
migrate = Migrate(app, db)

api = Api(app)


class Signup(Resource):
    def post(self):
        data = request.json
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        username = data.get('username')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        role = data.get('role', 'patient')
        admin_code = data.get('admin_code')

        # check if passwords match
        if password != confirm_password:
            return jsonify({"message": "Passwords do not match"}), 400
        # check if username already exists
        if User.query.filter_by(username=username).first():
            return jsonify({"message": "User already exists"}), 400
        # validate if admin
        if role == 'admin' and admin_code != '2304':
            return jsonify({"message": "Invalid admin code"})
        # create new user
        with app.app_context():
            new_user = User(first_name=first_name,
                            last_name=last_name, username=username, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            if role == 'admin':
                new_admin = Admin(user_id=new_user.id)
                db.session.add(new_admin)
                db.session.commit()
            else:
                new_patient = Patient(user_id=new_user.id)
                db.session.add(new_patient)
                db.session.commit()
            print("User commited")

        return jsonify({"message": "User created successfuly. Log in"}), 201


api.add_resource(Signup, '/signup')

# Login Endpoint


class Login(Resource):
    def post(self):
        data = request.json
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({"message": "Invalid username or password"}), 401

        return jsonify({"message": f"Welcome {user.first_name}!", "role": user.role, "username": user.username})


api.add_resource(Login, '/login')


@app.route('/users', methods=['GET'])
class User(Resource):
    def get(self):
        users = User.query.all()
        return jsonify([{
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'role': user.role
        } for user in users])


api.add_resource(User, '/user')

if __name__ == '__main__':
    app.run(debug=True)
