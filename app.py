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

# REMOVIDO: @app.before_first_request (depreciado)
# A conexão será testada quando necessário

# Função para testar conexão (chamada manualmente quando necessário)
def test_db_connection():
    try:
        with app.app_context():
            db.engine.execute('SELECT 1')
            print("✅ Conexão com banco estabelecida com sucesso!")
            return True
    except Exception as e:
        print(f"❌ Erro na conexão com banco: {e}")
        return False

# Importar suas rotas aqui (se estiver em arquivo separado)
# from routes import *

if __name__ == '__main__':
    app.run(debug=True)
