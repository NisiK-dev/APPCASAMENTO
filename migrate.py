import os
import sys

# Adiciona o diretório atual ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
            
            # Importa modelos
            try:
                import models
                print("✅ Modelos importados com sucesso!")
            except ImportError as e:
                print(f"⚠️ Aviso: Não foi possível importar models.py: {e}")
            
            # Verifica se as tabelas já existem
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name NOT LIKE 'pg_%'
                AND table_name NOT LIKE 'sql_%'
                ORDER BY table_name
            """))
            
            existing_tables = [row[0] for row in result.fetchall()]
            
            if existing_tables:
                print(f"📋 Tabelas já existentes: {existing_tables}")
                print("ℹ️  Pulando criação de tabelas (já existem)")
            else:
                # Só cria se não existir nenhuma tabela
                print("🔄 Criando tabelas...")
                db.create_all()
                print("✅ Tabelas criadas com sucesso!")
            
            # Lista todas as tabelas finais
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name NOT LIKE 'pg_%'
                AND table_name NOT LIKE 'sql_%'
                ORDER BY table_name
            """))
            
            final_tables = [row[0] for row in result.fetchall()]
            print(f"📋 Tabelas no banco: {final_tables}")
            
            # Commit das mudanças
            db.session.commit()
            print("✅ Migração concluída com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro detalhado: {e}")
            print(f"🔍 Tipo do erro: {type(e).__name__}")
            try:
                db.session.rollback()
            except:
                pass
            
        finally:
            try:
                db.session.close()
            except:
                pass

if __name__ == "__main__":
    init_database()
