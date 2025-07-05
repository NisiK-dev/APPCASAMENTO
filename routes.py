from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, db
from models import Admin, Guest
import logging

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_logged_in'] = True
            session['admin_id'] = admin.id
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Usuário ou senha incorretos!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Acesso negado. Faça login para continuar.', 'error')
        return redirect(url_for('admin_login'))
    
    guests = Guest.query.all()
    
    # Count statistics
    total_guests = len(guests)
    confirmed = len([g for g in guests if g.rsvp_status == 'confirmado'])
    declined = len([g for g in guests if g.rsvp_status == 'nao_confirmado'])
    pending = len([g for g in guests if g.rsvp_status == 'pendente'])
    
    stats = {
        'total': total_guests,
        'confirmed': confirmed,
        'declined': declined,
        'pending': pending
    }
    
    return render_template('admin_dashboard.html', guests=guests, stats=stats)

@app.route('/admin/add_guest', methods=['POST'])
def add_guest():
    if not session.get('admin_logged_in'):
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin_login'))
    
    name = request.form['name'].strip()
    if name:
        # Check if guest already exists
        existing_guest = Guest.query.filter_by(name=name).first()
        if existing_guest:
            flash('Este convidado já está na lista!', 'error')
        else:
            guest = Guest(name=name)
            db.session.add(guest)
            db.session.commit()
            flash('Convidado adicionado com sucesso!', 'success')
    else:
        flash('Nome não pode estar vazio!', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_guest/<int:guest_id>', methods=['POST'])
def edit_guest(guest_id):
    if not session.get('admin_logged_in'):
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin_login'))
    
    guest = Guest.query.get_or_404(guest_id)
    new_name = request.form['name'].strip()
    
    if new_name:
        # Check if another guest already has this name
        existing_guest = Guest.query.filter(Guest.name == new_name, Guest.id != guest_id).first()
        if existing_guest:
            flash('Já existe um convidado com este nome!', 'error')
        else:
            guest.name = new_name
            db.session.commit()
            flash('Nome do convidado atualizado com sucesso!', 'success')
    else:
        flash('Nome não pode estar vazio!', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_guest/<int:guest_id>', methods=['POST'])
def delete_guest(guest_id):
    if not session.get('admin_logged_in'):
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin_login'))
    
    guest = Guest.query.get_or_404(guest_id)
    db.session.delete(guest)
    db.session.commit()
    flash('Convidado removido com sucesso!', 'success')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/rsvp', methods=['GET', 'POST'])
def rsvp():
    if request.method == 'POST':
        name = request.form['name'].strip()
        rsvp_response = request.form['rsvp_response']
        
        if not name:
            flash('Por favor, digite seu nome completo.', 'error')
            return render_template('rsvp.html')
        
        # Find guest by name (case-insensitive)
        guest = Guest.query.filter(Guest.name.ilike(name)).first()
        
        if not guest:
            flash('Nome não encontrado na lista de convidados. Verifique a grafia e tente novamente.', 'error')
            return render_template('rsvp.html')
        
        # Update RSVP status
        guest.rsvp_status = rsvp_response
        db.session.commit()
        
        logging.info(f"Guest {guest.name} RSVP updated to {rsvp_response}")
        
        return render_template('rsvp_success.html', guest=guest)
    
    return render_template('rsvp.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
