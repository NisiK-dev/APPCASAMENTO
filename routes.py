from flask import render_template, request, jsonify, session, redirect, url_for, flash, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from app import app
from models import db, AdminUser, Admin, Guest, GuestGroup, GiftRegistry, VenueInfo
from send_whatsapp import send_bulk_whatsapp_messages, get_wedding_message

import logging
from sqlalchemy import text, func
from datetime import datetime, date
import os
import uuid
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload

import locale
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
except locale.Error:
    logging.warning("Locale 'pt_BR.utf8' not available in routes.py")


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
        gifts = GiftRegistry.query.filter_by(is_active=True).order_by(GiftRegistry.id.desc()).limit(3).all()
        
        return render_template('index.html', venue=venue, gifts=gifts)
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao acessar dados na rota principal: {e}")
        return render_template('index.html', venue=None, gifts=[])


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            admin = Admin.query.filter_by(username=username).first()
            if admin and check_password_hash(admin.password_hash, password):
                session['admin_id'] = admin.id
                session['admin_username'] = admin.username
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Usuário ou senha inválidos!', 'danger')
        except Exception as e:
            flash(f'Erro interno: {str(e)}', 'danger')
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('index'))


@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('Acesso negado! Faça login primeiro.', 'danger')
        return redirect(url_for('admin_login'))
    
    total_guests = Guest.query.count()
    confirmed_guests = Guest.query.filter_by(rsvp_status='confirmado').count()
    pending_guests = Guest.query.filter_by(rsvp_status='pendente').count()
    declined_guests = Guest.query.filter_by(rsvp_status='nao_confirmado').count()
    
    total_groups = GuestGroup.query.count()
    total_gifts = GiftRegistry.query.count()
    
    return render_template('admin_dashboard.html', 
                            total_guests=total_guests,
                            confirmed_guests=confirmed_guests,
                            pending_guests=pending_guests,
                            declined_guests=declined_guests,
                            total_groups=total_groups,
                            total_gifts=total_gifts)


@app.route('/admin/guests')
def admin_guests():
    if 'admin_id' not in session:
        flash('Acesso negado! Faça login primeiro.', 'danger')
        return redirect(url_for('admin_login'))
    
    guests = Guest.query.all()
    groups = GuestGroup.query.all()
    
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
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    name = request.form.get('name')
    phone = request.form.get('phone')
    group_id = request.form.get('group_id')
    
    if not name:
        flash('Nome é obrigatório!', 'danger')
        return redirect(url_for('admin_guests'))
    
    group_id = int(group_id) if group_id and group_id != '' else None
    
    new_guest = Guest(
        name=name,
        phone=phone,
        group_id=group_id
    )
    
    db.session.add(new_guest)
    db.session.commit()
    
    flash(f'Convidado {name} adicionado com sucesso!', 'success')
    return redirect(url_for('admin_guests'))


@app.route('/admin/edit_guest/<int:guest_id>', methods=['POST'])
def edit_guest(guest_id):
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    guest_to_edit = Guest.query.get_or_404(guest_id)
    guest_to_edit.name = request.form.get('name')
    guest_to_edit.phone = request.form.get('phone')
    group_id = request.form.get('group_id')
    guest_to_edit.group_id = int(group_id) if group_id and group_id != '' else None
    db.session.commit()
    
    flash(f'Convidado {guest_to_edit.name} atualizado com sucesso!', 'success')
    return redirect(url_for('admin_guests'))


@app.route('/admin/delete_guest/<int:guest_id>', methods=['POST'])
def delete_guest(guest_id):
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    guest_to_delete = Guest.query.get_or_404(guest_id)
    name = guest_to_delete.name
    
    db.session.delete(guest_to_delete)
    db.session.commit()
    
    flash(f'Convidado {name} removido com sucesso!', 'success')
    return redirect(url_for('admin_guests'))


@app.route('/rsvp')
def rsvp():
    return render_template('rsvp.html')


@app.route('/search_guest', methods=['POST'])
def search_guest():
    name = request.form.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Nome é obrigatório'}), 400

    guests_list = Guest.query.filter(func.lower(Guest.name).like(f"%{name.lower()}%")).all()
    if not guests_list:
        return jsonify({'error': 'Convidado não encontrado'}), 404

    unique_group_ids = {g.group_id for g in guests_list if g.group_id}

    if len(unique_group_ids) == 1:
        guest_reference = guests_list[0]
        group_guests = Guest.query.filter_by(group_id=guest_reference.group_id).all()
        group_name = guest_reference.group.name if guest_reference.group else None
    else:
        group_guests = guests_list
        group_name = None

    guests_data = [{
        'id': g.id,
        'name': g.name,
        'phone': g.phone,
        'rsvp_status': g.rsvp_status
    } for g in group_guests]

    return jsonify({'guests': guests_data, 'group_name': group_name})


@app.route('/confirm_rsvp', methods=['POST'])
def confirm_rsvp():
    guest_ids = request.form.getlist('guest_ids')
    if not guest_ids:
        flash('Nenhum convidado selecionado!', 'danger')
        return redirect(url_for('rsvp'))
    
    confirmed_guests = []
    declined_guests = []
    for guest_id in guest_ids:
        guest_obj = Guest.query.get(guest_id)
        if guest_obj:
            rsvp_choice = request.form.get(f'rsvp_{guest_id}')
            if rsvp_choice in ['confirmado', 'nao_confirmado']:
                guest_obj.rsvp_status = rsvp_choice
                if rsvp_choice == 'confirmado':
                    confirmed_guests.append(guest_obj)
                else:
                    declined_guests.append(guest_obj)
    db.session.commit()
    
    return render_template('rsvp_success.html', confirmed_guests=confirmed_guests, declined_guests=declined_guests)


@app.route('/search_guest', methods=['POST'])
def search_guest():
    name = request.form.get('name', '').strip()
    if not name or len(name) < 3:
        return jsonify({"guests": []})

    guests = Guest.query.filter(Guest.name.ilike(f"%{name}%")).all()

    results = []
    for g in guests:
        results.append({
            "id": g.id,
            "name": g.name,
            "rsvp_status": g.rsvp_status,
            "group_name": g.group.name if g.group else None
        })

    return jsonify({"guests": results})

# Pegar grupo do convidado selecionado
@app.route('/get_guest_group/<int:guest_id>')
def get_guest_group(guest_id):
    guest = Guest.query.get_or_404(guest_id)

    if guest.group_id:
        group = GuestGroup.query.get(guest.group_id)
        guests = group.guests if group else [guest]
    else:
        guests = [guest]

    guests_data = [
        {
            "id": g.id,
            "name": g.name,
            "rsvp_status": g.rsvp_status
        } for g in guests
    ]

    return jsonify({
        "selected_guest_name": guest.name,
        "guests": guests_data
    })

# Confirmar RSVP
@app.route('/confirm_rsvp', methods=['POST'])
def confirm_rsvp():
    guest_ids = request.form.getlist('guest_ids')
    if not guest_ids:
        flash("Nenhum convidado selecionado.", "danger")
        return redirect(url_for('rsvp'))

    for guest_id in guest_ids:
        guest = Guest.query.get(int(guest_id))
        if guest:
            status = request.form.get(f"rsvp_{guest.id}")
            if status in ['confirmado', 'nao_confirmado']:
                guest.rsvp_status = status
                db.session.add(guest)

    db.session.commit()
    flash("Confirmação registrada com sucesso!", "success")
    return redirect(url_for('rsvp'))
