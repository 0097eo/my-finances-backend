from config import app, db
from models import User, Budget, BudgetCategory, Transaction
from datetime import datetime, timedelta
import random
from decimal import Decimal

def seed_database():
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()

        # Create sample users
        print("Creating users...")
        users = [
            {
                "name": "John Doe",
                "email": "john@example.com",
                "password": "password123"
            },
            {
                "name": "Jane Smith",
                "email": "jane@example.com",
                "password": "password456"
            }
        ]

        created_users = []
        for user_data in users:
            user = User(
                name=user_data["name"],
                email=user_data["email"]
            )
            user.set_password(user_data["password"])
            db.session.add(user)
            created_users.append(user)
        
        db.session.commit()

        # Create budgets for each user
        print("Creating budgets...")
        months = ['January 2024', 'February 2024', 'March 2024']
        budget_names = ['Monthly Budget', 'Vacation Fund', 'Emergency Fund']
        
        for user in created_users:
            for month in months:
                budget = Budget(
                    user_id=user.id,
                    name=f"{user.name}'s {random.choice(budget_names)}",
                    amount=float(random.uniform(3000, 5000)),
                    month=month,
                    created_at=datetime.utcnow()
                )
                db.session.add(budget)
                db.session.commit()

                # Create budget categories for each budget
                print(f"Creating budget categories for {budget.name}...")
                categories = [
                    {"name": "Housing", "color": "#FF0000", "allocation": Decimal('1200.00')},
                    {"name": "Transportation", "color": "#00FF00", "allocation": Decimal('400.00')},
                    {"name": "Food", "color": "#0000FF", "allocation": Decimal('600.00')},
                    {"name": "Entertainment", "color": "#FFFF00", "allocation": Decimal('300.00')},
                    {"name": "Utilities", "color": "#FF00FF", "allocation": Decimal('200.00')},
                    {"name": "Healthcare", "color": "#00FFFF", "allocation": Decimal('150.00')},
                ]

                created_categories = []
                for cat in categories:
                    category = BudgetCategory(
                        budget_id=budget.id,
                        name=cat["name"],
                        alocated_amount=cat["allocation"],
                        color=cat["color"]
                    )
                    db.session.add(category)
                    created_categories.append(category)
                db.session.commit()

                # Create transactions for each category
                print(f"Creating transactions for {budget.name}...")
                transaction_descriptions = {
                    "Housing": ["Rent", "Property Tax", "Home Insurance", "Maintenance"],
                    "Transportation": ["Gas", "Car Payment", "Bus Pass", "Car Insurance"],
                    "Food": ["Groceries", "Restaurant", "Coffee Shop", "Take Out"],
                    "Entertainment": ["Movies", "Concert", "Video Games", "Hobbies"],
                    "Utilities": ["Electricity", "Water", "Internet", "Phone"],
                    "Healthcare": ["Doctor Visit", "Medication", "Dental", "Vision"]
                }

                # Create transactions over the past 30 days
                for category in created_categories:
                    num_transactions = random.randint(3, 8)
                    for _ in range(num_transactions):
                        transaction_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))
                        description = random.choice(transaction_descriptions[category.name])
                        # Convert the random amount to Decimal with 2 decimal places
                        amount = Decimal(str(round(random.uniform(10, float(category.alocated_amount) / 2), 2)))
                        
                        transaction = Transaction(
                            user_id=user.id,
                            budget_category_id=category.id,
                            amount=float(amount),  # Convert back to float since Transaction.amount is Float
                            description=description,
                            created_at=transaction_date,
                            type='expense'
                        )
                        db.session.add(transaction)

                    # Add some income transactions
                    if category.name == "Housing":  # Using Housing category for income
                        income_sources = ["Salary", "Freelance", "Investment", "Side Gig"]
                        income_transaction = Transaction(
                            user_id=user.id,
                            budget_category_id=category.id,
                            amount=float(Decimal(str(round(random.uniform(2000, 4000), 2)))),
                            description=random.choice(income_sources),
                            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                            type='income'
                        )
                        db.session.add(income_transaction)

                db.session.commit()

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()