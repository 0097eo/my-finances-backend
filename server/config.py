from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_restful import Api
from flask_jwt_extended import JWTManager
from sqlalchemy import MetaData
from datetime import timedelta

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myfinances.db'
app.secret_key = b"\xa4\x82\x9fs\xf2\x81\xa4'&\xfd\xf1\x07\xe2\x1b>\xc7"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=10)


metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
})


db = SQLAlchemy(metadata=metadata)
db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
api = Api(app)
jwt = JWTManager(app)
CORS(app)