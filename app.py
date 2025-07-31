import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import locale # Importe o módulo locale
from datetime import datetime # Importe datetime para uso futuro se necessário

load_dotenv()

app = Flask(__name__)

# Configuração do banco de dados
database_url = os.environ.get('DATABASE_URL')

if not database_url:
    print("⚠️ DATABASE_URL não encontrada, usando SQLite local")
    database_url = 'sqlite:///instance/wedding_rsvp.db'
else:
    print(f"✅ Conectando ao banco: {database_url.split('@')[1] if '@' in database_url else 'local'}")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 30,
    'max_overflow': 0,
}

# --- INÍCIO DA ALTERAÇÃO PARA LOCALIDADE ---
# Tenta definir a localidade para português do Brasil.
# Isso é crucial para que datetime.strptime() possa entender nomes de meses como "Outubro".
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
    print("✅ Localidade definida para 'pt_BR.utf8'")
except locale.Error:
    print("⚠️ Aviso: A localidade 'pt_BR.utf8' não está disponível. A análise de datas com nomes de meses pode falhar.")
    print("   Por favor, verifique a configuração do seu ambiente (ex: Render) para instalar os pacotes de localidade.")
# --- FIM DA ALTERAÇÃO PARA LOCALIDADE ---


# Inicializar DB
from models import db
db.init_app(app)

# Importar rotas DEPOIS de inicializar DB
with app.app_context():
    try:
        import routes
        print("✅ Rotas importadas com sucesso!")
    except ImportError as e:
        print(f"⚠️ Erro ao importar routes: {e}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

