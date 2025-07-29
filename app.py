import os
from app import app, db

def init_database():
    """Inicializa o banco de dados no Supabase"""
    print("🔄 Iniciando migração do banco...")
    print(f"🌐 DATABASE_URL configurada: {'Sim' if os.environ.get('DATABASE_URL') else 'Não'}")
    
    with app.app_context():
        try:
            # Testa a conexão primeiro
            from sqlalchemy import text
            result = db.session.execute(text('SELECT 1'))
            print("✅ Conexão com banco OK!")
            
            # Importa todos os modelos antes de criar as tabelas
            try:
                from models import *
                print("✅ Modelos importados com sucesso!")
            except ImportError as e:
                print(f"⚠️ Aviso ao importar modelos: {e}")
            
            # Cria todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas com sucesso no Supabase!")
            
            # Lista as tabelas criadas
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name NOT LIKE '%pgsodium%'
                AND table_name NOT LIKE '%vault%'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            if tables:
                print(f"📋 Tabelas encontradas: {tables}")
            else:
                print("⚠️ Nenhuma tabela encontrada - verifique seus modelos")
            
            # Commit das mudanças
            db.session.commit()
            print("✅ Migração concluída com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro detalhado: {e}")
            print(f"🔍 Tipo do erro: {type(e).__name__}")
            db.session.rollback()
            
        finally:
            db.session.close()

if __name__ == "__main__":
    init_database()
