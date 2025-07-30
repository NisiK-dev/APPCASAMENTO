import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuração do banco de dados Supabase
database_url = os.environ.get('DATABASE_URL')

if not database_url:
    print("⚠️ DATABASE_URL não encontrada, usando SQLite local")
    database_url = 'sqlite:///instance/wedding_rsvp.db'
else:
    print(f"✅ Conectando ao banco: {database_url.split('@')[1] if '@' in database_url else 'local'}")

# Ajusta URL do Postgres se necessário
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Configurações para melhor conexão com Supabase
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 30,
    'max_overflow': 0,
}

db = SQLAlchemy(app)

# Importar modelos (se estiver em arquivo separado)
try:
    import models
    print("✅ Modelos importados com sucesso!")
except ImportError:
    print("⚠️ Arquivo models.py não encontrado")

# Importar rotas (se estiver em arquivo separado)
try:
    import routes
    print("✅ Rotas importadas com sucesso!")
except ImportError:
    print("⚠️ Arquivo routes.py não encontrado")

if __name__ == '__main__':
    app.run(debug=True)

# Final check for Render deploy
