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
            
            access_token = create_access_token(identity=str(user.id))

            return {
                "message": "Login successful",
                "access_token": access_token,
                "user_id": user.id
            }
        
        except Exception as e:
            return {"error": str(e)}, 500
        

class Profile(Resource):
    @jwt_required()
    def get(self):
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get_or_404(current_user_id)

            return {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }, 200 
        
        except Exception as e:
            return {"error": str(e)}, 422
    
class TransactionResource(Resource):
    @jwt_required()
    def get(self):
        try:
            user_id = get_jwt_identity()
            transactions = Transaction.query.filter_by(user_id=user_id).all()
            return [{
                "id": t.id,
                "user_id": t.user_id,
                "budget_category_id": t.budget_category_id,
                "created_at": t.created_at.isoformat(),
                "amount": t.amount,
                "description": t.description,
                "type": t.type
            } for t in transactions], 200
        except Exception as e:
            return {"error": str(e)}, 500
    
    @jwt_required
    def post(self):
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            required_fields = ["budget_category_id", "amount", "type", "description"]

            for field in required_fields:
                if field not in data:
                    return {"error": f"Missing {field} field"}, 400
            
            category = BudgetCategory.query.get(data["budget_category_id"])
            if not category:
                return {"error": "Category does not exist"}, 400
        
            new_transaction = Transaction(
                user_id=user_id,
                budget_category_id=data["budget_category_id"],
                amount=data["amount"],
                description=data["description"],
                type=data["type"]
            )

            db.session.add(new_transaction)
            db.session.commit()

            return {"message": "Transaction created successfully"}, 201
        
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
        

    @jwt_required
    def delete(self, transaction_id):
        try:
            user_id = get_jwt_identity()
            transaction = Transaction.query.get(transaction_id)
            if not transaction:
                return {"error": "Transaction does not exist"}, 400
            if transaction.user_id != user_id:
                return {"error": "Unauthorized"}, 401

            db.session.delete(transaction)
            db.session.commit()

            return {"message": "Transaction deleted successfully"}, 200
        
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
        
class BudgetResource(Resource):
    @jwt_required
    def get(self):
        try:
            user_id = get_jwt_identity()
            budgets = Budget.query.filter_by(user_id=user_id).all()
            return jsonify([{
                'id': b.id,
                'name': b.name,
                'amount': float(b.amount),
                'month': b.month,
                'categories': [{
                    'id': cat.id,
                    'name': cat.name,
                    'allocated_amount': float(cat.alocated_amount),
                    'color': cat.color
                    } for cat in b.categories]
            } for b in budgets])
        
        except Exception as e:
            return {"error": str(e)}, 500
        
    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        data = request.get_json()

        # Validate budget data
        if not all(key in data for key in ['name', 'amount', 'month', 'categories']):
            return {'error': 'Missing required budget fields'}, 400

        try:
            # Create budget
            new_budget = Budget(
                user_id=user_id,
                name=data['name'],
                amount=data['amount'],
                month=data['month']
            )
            db.session.add(new_budget)
            db.session.flush()

            # Create budget categories
            for category in data['categories']:
                budget_category = BudgetCategory(
                    budget_id=new_budget.id,
                    name=category['name'],
                    alocated_amount=category['allocated_amount'],
                    color=category.get('color', '#000000')
                )
                db.session.add(budget_category)

            db.session.commit()
            return {
                'message': 'Budget created successfully',
                'budget_id': new_budget.id
            }, 201

        except IntegrityError:
            db.session.rollback()
            return {'error': 'Budget creation failed'}, 400
            
    
    @jwt_required()
    def put(self, budget_id):
        user_id = get_jwt_identity()
        budget = Budget.query.filter_by(id=budget_id, user_id=user_id).first()
        
        if not budget:
            return {'error': 'Budget not found'}, 404

        data = request.get_json()
        try:
            # Update budget details
            budget.name = data.get('name', budget.name)
            budget.amount = data.get('amount', budget.amount)
            budget.month = data.get('month', budget.month)

            # Update or create categories
            if 'categories' in data:
                # Remove existing categories
                BudgetCategory.query.filter_by(budget_id=budget_id).delete()
                
                for category in data['categories']:
                    new_category = BudgetCategory(
                        budget_id=budget_id,
                        name=category['name'],
                        alocated_amount=category['allocated_amount'],
                        color=category.get('color', '#000000')
                    )
                    db.session.add(new_category)

            db.session.commit()
            return {'message': 'Budget updated successfully'}, 200

        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 400
        
    @jwt_required()
    def delete(self, budget_id):
        user_id = get_jwt_identity()
        budget = Budget.query.filter_by(id=budget_id, user_id=user_id).first()
        
        if not budget:
            return {'error': 'Budget not found'}, 404

        try:
            # Delete associated categories first
            BudgetCategory.query.filter_by(budget_id=budget_id).delete()
            
            # Delete budget
            db.session.delete(budget)
            db.session.commit()
            
            return {'message': 'Budget deleted successfully'}, 200
        
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 400

api.add_resource(Register, '/register')
api.add_resource(Login, '/login')
api.add_resource(Profile, '/profile')
api.add_resource(TransactionResource, '/transactions', '/transactions/<int:transaction_id>')
api.add_resource(BudgetResource, '/budgets', '/budgets/<int:budget_id>')






if __name__ == '__main__':
    app.run(port=5555, debug=True)