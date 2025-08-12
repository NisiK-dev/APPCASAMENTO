from flask import render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from app import app
# Importante: Certifique-se de que GiftRegistry está sendo importado corretamente
from models import db, AdminUser, Admin, Guest, GuestGroup, GiftRegistry, VenueInfo
from send_whatsapp import send_bulk_whatsapp_messages, get_wedding_message

import logging
from sqlalchemy import text # Necessário para o healthz e qualquer raw SQL
from datetime import datetime, date, time
import os
from flask import current_app
import uuid
from werkzeug.utils import secure_filename

import locale
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
except locale.Error:
    logging.warning("Locale 'pt_BR.utf8' not available in routes.py, date parsing for month names might fail.")


@app.template_filter('format_date_br')
def format_date_br(value):
    meses_map = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
        7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    if not value:
        return ""
    
    dia = value.day
    mes = meses_map.get(value.month)
    ano = value.year
    
    if mes:
        return f"{dia} de {mes} de {ano}"
    else:
        return value.strftime('%Y-%m-%d') if isinstance(value, date) else ""


@app.route('/')
def index():
    try:
        venue = VenueInfo.query.first()
        
        # PASSO 1: AQUI ESTÁ A MUDANÇA PRINCIPAL PARA LIMITAR OS PRESENTES
        # Antes: gifts = GiftRegistry.query.filter_by(is_active=True).all()
        # Agora: Usamos .limit(N) para buscar apenas N presentes.
        # Também é uma boa prática ordenar para garantir quais itens serão exibidos.
        gifts = GiftRegistry.query.filter_by(is_active=True).order_by(GiftRegistry.id.desc()).limit(3).all()
        
        # Passa tanto 'venue' quanto 'gifts' para o template
        return render_template('index.html', venue=venue, gifts=gifts)
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao acessar dados na rota principal: {e}")
        return render_template('index.html', venue=None, gifts=[])
    finally:
        db.session.close()


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login do administrador"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"🔍 Tentativa de login: {username}")
        
        try:
            admin = Admin.query.filter_by(username=username).first()
            print(f"🔍 Admin encontrado: {admin}")
            
            if admin and check_password_hash(admin.password_hash, password):
                session['admin_id'] = admin.id
                session['admin_username'] = admin.username
                print(f"✅ Login bem-sucedido para: {username}")
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                print(f"❌ Credenciais inválidas para: {username}")
                flash('Usuário ou senha inválidos!', 'danger')
                
        except Exception as e:
            print(f"❌ Erro no login: {e}")
            flash(f'Erro interno: {str(e)}', 'danger')
            
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Logout do administrador"""
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    """Dashboard do administrador"""
    if 'admin_id' not in session:
        flash('Acesso negado! Faça login primeiro.', 'danger')
        return redirect(url_for('admin_login'))
    
    # Estatísticas
    total_guests = Guest.query.count()
    confirmed_guests = Guest.query.filter_by(rsvp_status='confirmado').count()
    pending_guests = Guest.query.filter_by(rsvp_status='pendente').count()
    declined_guests = Guest.query.filter_by(rsvp_status='nao_confirmado').count()
    
    total_groups = GuestGroup.query.count()
    total_gifts = GiftRegistry.query.count() # Usando GiftRegistry
    
    return render_template('admin_dashboard.html', 
                            total_guests=total_guests,
                            confirmed_guests=confirmed_guests,
                            pending_guests=pending_guests,
                            declined_guests=declined_guests,
                            total_groups=total_groups,
                            total_gifts=total_gifts)

@app.route('/admin/guests')
def admin_guests():
    """Gerenciar lista de convidados"""
    if 'admin_id' not in session:
        flash('Acesso negado! Faça login primeiro.', 'danger')
        return redirect(url_for('admin_login'))
    
    guests = Guest.query.all()
    groups = GuestGroup.query.all()
    
    # Estatísticas
    total_guests = len(guests)
    confirmed_guests = len([g for g in guests if g.rsvp_status == 'confirmado'])
    declined_guests = len([g for g in guests if g.rsvp_status == 'nao_confirmado'])
    pending_guests = len([g for g in guests if g.rsvp_status == 'pendente'])
    
    return render_template('admin_guests.html', 
                            guests=guests, 
                            groups=groups,
                            total_guests=total_guests,
                            confirmed_guests=confirmed_guests,
                            declined_guests=declined_guests,
                            pending_guests=pending_guests)

@app.route('/admin/add_guest', methods=['POST'])
def add_guest():
    """Adicionar novo convidado"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    name = request.form.get('name')
    phone = request.form.get('phone')
    group_id = request.form.get('group_id')
    
    if not name:
        flash('Nome é obrigatório!', 'danger')
        return redirect(url_for('admin_guests'))
    
    # Converte group_id para int ou None
    group_id = int(group_id) if group_id and group_id != '' else None
    
    guest = Guest(
        name=name,
        phone=phone,
        group_id=group_id
    )
    
    db.session.add(guest)
    db.session.commit()
    
    flash(f'Convidado {name} adicionado com sucesso!', 'success')
    return redirect(url_for('admin_guests'))

@app.route('/admin/edit_guest/<int:guest_id>', methods=['POST'])
def edit_guest(guest_id):
    """Editar convidado"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    guest = Guest.query.get_or_404(guest_id)
    
    guest.name = request.form.get('name')
    guest.phone = request.form.get('phone')
    group_id = request.form.get('group_id')
    guest.group_id = int(group_id) if group_id and group_id != '' else None
    
    db.session.commit()
    
    flash(f'Convidado {guest.name} atualizado com sucesso!', 'success')
    return redirect(url_for('admin_guests'))

@app.route('/admin/delete_guest/<int:guest_id>', methods=['POST'])
def delete_guest(guest_id):
    """Deletar convidado"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    guest = Guest.query.get_or_404(guest_id)
    name = guest.name
    
    db.session.delete(guest)
    db.session.commit()
    
    flash(f'Convidado {name} removido com sucesso!', 'success')
    return redirect(url_for('admin_guests'))

@app.route('/rsvp')
def rsvp():
    """Página de confirmação de presença"""
    return render_template('rsvp.html')

@app.route('/search_guest', methods=['POST'])
def search_guest():
    """Buscar convidado por nome (API)"""
    name = request
