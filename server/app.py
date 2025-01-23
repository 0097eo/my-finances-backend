from config import app, db, api
from models import User, Transaction, BudgetCategory, Budget
from flask_restful import Resource, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask import jsonify
from sqlalchemy.exc import IntegrityError

class Register(Resource):
    def post(self):
        try:
            data = request.get_json()
            required_fields = ["name", "email", "password"]
            for field in required_fields:
                if field not in data:
                    return {"error": f"Missing {field} field"}, 400
                
            if User.query.filter_by(email=data["email"]).first():
                return {"error": "email already exists"}, 400
            if User.query.filter_by(name=data["name"]).first():
                return {"error": "username already exists"}, 400
            
            new_user = User(
                name=data["name"],
                email=data["email"],
            )
            new_user.set_password(data["password"])

            db.session.add(new_user)
            db.session.commit()

            return {"message": "User created successfully"}, 201
        
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
            

class Login(Resource):
    def post(self):
        try:
            data = request.get_json()

            if "email" and "password" not in data:
                return {"error": "Missing email or password field"}, 400
            
            user = User.query.filter_by(email=data["email"]).first()

            if not user or not user.check_password(data["password"]):
                return {"error": "Invalid email or password"}, 400
            
            access_token = create_access_token(identity=user.id)

            return {
                "message": "Login successful",
                "access_token": access_token,
                "user_id": user.id
            }
        
        except Exception as e:
            return {"error": str(e)}, 500
        

class Profile(Resource):
    @jwt_required
    def get(self):
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            return {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        
        except Exception as e:
            return {"error": str(e)}, 500
    


api.add_resource(Register, '/register')
api.add_resource(Login, '/login')
api.add_resource(Profile, '/profile')






if __name__ == '__main__':
    app.run(port=5555, debug=True)