from flask import render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, db
from models import Admin, Guest, GuestGroup, VenueInfo, GiftRegistry
import logging

@app.route('/')
def index():
    venue = VenueInfo.query.first()
    gifts = GiftRegistry.query.filter_by(is_active=True).all()
    return render_template('index.html', venue=venue, gifts=gifts)

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
    groups = GuestGroup.query.all()
    
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
    
    return render_template('admin_dashboard.html', guests=guests, groups=groups, stats=stats)

@app.route('/admin/add_guest', methods=['POST'])
def add_guest():
    if not session.get('admin_logged_in'):
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin_login'))
    
    name = request.form['name'].strip()
    phone = request.form.get('phone', '').strip()
    group_id = request.form.get('group_id')
    
    if name:
        # Check if guest already exists
        existing_guest = Guest.query.filter_by(name=name).first()
        if existing_guest:
            flash('Este convidado já está na lista!', 'error')
        else:
            guest = Guest(name=name, phone=phone if phone else None)
            if group_id and group_id != '':
                guest.group_id = int(group_id)
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
    new_phone = request.form.get('phone', '').strip()
    group_id = request.form.get('group_id')
    
    if new_name:
        # Check if another guest already has this name
        existing_guest = Guest.query.filter(Guest.name == new_name, Guest.id != guest_id).first()
        if existing_guest:
            flash('Já existe um convidado com este nome!', 'error')
        else:
            guest.name = new_name
            guest.phone = new_phone if new_phone else None
            guest.group_id = int(group_id) if group_id and group_id != '' else None
            db.session.commit()
            flash('Convidado atualizado com sucesso!', 'success')
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
        
        if not name:
            flash('Por favor, digite seu nome completo.', 'error')
            return render_template('rsvp.html')
        
        # Find guest by name (case-insensitive)
        guest = Guest.query.filter(Guest.name.ilike(name)).first()
        
        if not guest:
            flash('Nome não encontrado na lista de convidados. Verifique a grafia e tente novamente.', 'error')
            return render_template('rsvp.html')
        
        # Get all guests in the same group
        group_guests = []
        if guest.group:
            group_guests = Guest.query.filter_by(group_id=guest.group.id).all()
        else:
            group_guests = [guest]
        
        # Update RSVP status for selected guests
        for g in group_guests:
            guest_id = str(g.id)
            if guest_id in request.form:
                rsvp_response = request.form[guest_id]
                g.rsvp_status = rsvp_response
                logging.info(f"Guest {g.name} RSVP updated to {rsvp_response}")
        
        db.session.commit()
        
        return render_template('rsvp_success.html', guests=group_guests, main_guest=guest)
    
    return render_template('rsvp.html')

@app.route('/search_guest', methods=['POST'])
def search_guest():
    name = request.form['name'].strip()
    
    if not name:
        return jsonify({'error': 'Nome não pode estar vazio'})
    
    # Find guest by name (case-insensitive)
    guest = Guest.query.filter(Guest.name.ilike(name)).first()
    
    if not guest:
        return jsonify({'error': 'Nome não encontrado na lista de convidados'})
    
    # Get all guests in the same group
    group_guests = []
    if guest.group:
        group_guests = Guest.query.filter_by(group_id=guest.group.id).all()
    else:
        group_guests = [guest]
    
    # Return guest data
    guest_data = []
    for g in group_guests:
        guest_data.append({
            'id': g.id,
            'name': g.name,
            'rsvp_status': g.rsvp_status
        })
    
    return jsonify({
        'success': True,
        'guests': guest_data,
        'group_name': guest.group.name if guest.group else None
    })

# Admin routes for group management
@app.route('/admin/groups')
def admin_groups():
    if not session.get('admin_logged_in'):
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin_login'))
    
    groups = GuestGroup.query.all()
    return render_template('admin_groups.html', groups=groups)

@app.route('/admin/add_group', methods=['POST'])
def add_group():
    if not session.get('admin_logged_in'):
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin_login'))
    
    name = request.form['name'].strip()
    description = request.form.get('description', '').strip()
    
    if name:
        existing_group = GuestGroup.query.filter_by(name=name).first()
        if existing_group:
            flash('Já existe um grupo com este nome!', 'error')
        else:
            group = GuestGroup(name=name, description=description if description else None)
            db.session.add(group)
            db.session.commit()
            flash('Grupo adicionado com sucesso!', 'success')
    else:
        flash('Nome do grupo não pode estar vazio!', 'error')
    
    return redirect(url_for('admin_groups'))

@app.route('/admin/edit_group/<int:group_id>', methods=['POST'])
def edit_group(group_id):
    if not session.get('admin_logged_in'):
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin_login'))
    
    group = GuestGroup.query.get_or_404(group_id)
    new_name = request.form['name'].strip()
    new_description = request.form.get('description', '').strip()
    
    if new_name:
        existing_group = GuestGroup.query.filter(GuestGroup.name == new_name, GuestGroup.id != group_id).first()
        if existing_group:
            flash('Já existe um grupo com este nome!', 'error')
        else:
            group.name = new_name
            group.description = new_description if new_description else None
            db.session.commit()
            flash('Grupo atualizado com sucesso!', 'success')
    else:
        flash('Nome do grupo não pode estar vazio!', 'error')
    
    return redirect(url_for('admin_groups'))

@app.route('/admin/delete_group/<int:group_id>', methods=['POST'])
def delete_group(group_id):
    if not session.get('admin_logged_in'):
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin_login'))
    
    group = GuestGroup.query.get_or_404(group_id)
    
    # Check if group has guests
    if group.guests:
        flash('Não é possível excluir um grupo que possui convidados!', 'error')
    else:
        db.session.delete(group)
        db.session.commit()
        flash('Grupo removido com sucesso!', 'success')
    
    return redirect(url_for('admin_groups'))

# Admin routes for venue management
@app.route('/admin/venue')
def admin_venue():
    if not session.get('admin_logged_in'):
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin_login'))
    
    venue = VenueInfo.query.first()
    return render_template('admin_venue.html', venue=venue)

@app.route('/admin/update_venue', methods=['POST'])
def update_venue():
    if not session.get('admin_logged_in'):
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin_login'))
    
    venue = VenueInfo.query.first()
    if not venue:
        venue = VenueInfo()
        db.session.add(venue)
    
    venue.name = request.form['name'].strip()
    venue.address = request.form['address'].strip()
    venue.map_link = request.form.get('map_link', '').strip()
    venue.description = request.form.get('description', '').strip()
    venue.date = request.form['date'].strip()
    venue.time = request.form['time'].strip()
    
    db.session.commit()
    flash('Informações do local atualizadas com sucesso!', 'success')
    
    return redirect(url_for('admin_venue'))

# Admin routes for gift registry
@app.route('/admin/gifts')
def admin_gifts():
    if not session.get('admin_logged_in'):
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin_login'))
    
    gifts = GiftRegistry.query.all()
    return render_template('admin_gifts.html', gifts=gifts)

@app.route('/admin/add_gift', methods=['POST'])
def add_gift():
    if not session.get('admin_logged_in'):
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin_login'))
    
    item_name = request.form['item_name'].strip()
    description = request.form.get('description', '').strip()
    price = request.form.get('price', '').strip()
    store_link = request.form.get('store_link', '').strip()
    
    if item_name:
        gift = GiftRegistry(
            item_name=item_name,
            description=description if description else None,
            price=price if price else None,
            store_link=store_link if store_link else None
        )
        db.session.add(gift)
        db.session.commit()
        flash('Presente adicionado com sucesso!', 'success')
    else:
        flash('Nome do presente não pode estar vazio!', 'error')
    
    return redirect(url_for('admin_gifts'))

@app.route('/admin/edit_gift/<int:gift_id>', methods=['POST'])
def edit_gift(gift_id):
    if not session.get('admin_logged_in'):
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin_login'))
    
    gift = GiftRegistry.query.get_or_404(gift_id)
    
    gift.item_name = request.form['item_name'].strip()
    gift.description = request.form.get('description', '').strip()
    gift.price = request.form.get('price', '').strip()
    gift.store_link = request.form.get('store_link', '').strip()
    gift.is_active = 'is_active' in request.form
    
    db.session.commit()
    flash('Presente atualizado com sucesso!', 'success')
    
    return redirect(url_for('admin_gifts'))

@app.route('/admin/delete_gift/<int:gift_id>', methods=['POST'])
def delete_gift(gift_id):
    if not session.get('admin_logged_in'):
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin_login'))
    
    gift = GiftRegistry.query.get_or_404(gift_id)
    db.session.delete(gift)
    db.session.commit()
    flash('Presente removido com sucesso!', 'success')
    
    return redirect(url_for('admin_gifts'))

# Public routes for gifts
@app.route('/presentes')
def gifts():
    gifts = GiftRegistry.query.filter_by(is_active=True).all()
    return render_template('gifts.html', gifts=gifts)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
