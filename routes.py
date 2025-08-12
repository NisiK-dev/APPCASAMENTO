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

    name = request.form.get('name', '').strip()

    

    if not name:

        return jsonify({'error': 'Nome é obrigatório'}), 400

    

    # Busca por nome (case-insensitive)

    guest = Guest.query.filter(Guest.name.ilike(f'%{name}%')).all()

    

    if not guest:

        return jsonify({'error': 'Convidado não encontrado'}), 404

    

    # Se o convidado pertence a um grupo, busca todos os membros do grupo

    if guest.group_id:

        group_guests = Guest.query.filter_by(group_id=guest.group_id).all()

        group_name = guest.group.name if guest.group else None

    else:

        group_guests = [guest]

        group_name = None

    

    guests_data = [{

        'id': g.id,

        'name': g.name,

        'phone': g.phone,

        'rsvp_status': g.rsvp_status

    } for g in group_guests]

    

    return jsonify({

        'guests': guests_data,

        'group_name': group_name

    })



@app.route('/confirm_rsvp', methods=['POST'])

def confirm_rsvp():

    """Confirmar presença dos convidados"""

    # Obter IDs dos convidados

    guest_ids = request.form.getlist('guest_ids')

    

    if not guest_ids:

        flash('Nenhum convidado selecionado!', 'danger')

        return redirect(url_for('rsvp'))

    

    confirmed_guests = []

    declined_guests = []

    

    # Processar cada convidado

    for guest_id in guest_ids:

        guest = Guest.query.get(guest_id)

        if guest:

            # Verificar o status escolhido

            rsvp_choice = request.form.get(f'rsvp_{guest_id}')

            

            if rsvp_choice in ['confirmado', 'nao_confirmado']:

                guest.rsvp_status = rsvp_choice

                if rsvp_choice == 'confirmado':

                    confirmed_guests.append(guest)

                else:

                    declined_guests.append(guest)

    

    db.session.commit()

    

    return render_template('rsvp_success.html', 

                            confirmed_guests=confirmed_guests,

                            declined_guests=declined_guests)



@app.route('/admin/groups')

def admin_groups():

    """Gerenciar grupos de convidados"""

    if 'admin_id' not in session:

        flash('Acesso negado!', 'danger')

        return redirect(url_for('admin_login'))

    

    groups = GuestGroup.query.all()

    return render_template('admin_groups.html', groups=groups)



@app.route('/admin/add_group', methods=['POST'])

def add_group():

    """Adicionar novo grupo"""

    if 'admin_id' not in session:

        flash('Acesso negado!', 'danger')

        return redirect(url_for('admin_login'))

    

    name = request.form.get('name')

    description = request.form.get('description')

    

    if not name:

        flash('Nome do grupo é obrigatório!', 'danger')

        return redirect(url_for('admin_groups'))

    

    group = GuestGroup(

        name=name,

        description=description

    )

    

    db.session.add(group)

    db.session.commit()

    

    flash(f'Grupo {name} criado com sucesso!', 'success')

    return redirect(url_for('admin_groups'))



@app.route('/admin/edit_group/<int:group_id>', methods=['POST'])

def edit_group(group_id):

    """Editar grupo"""

    if 'admin_id' not in session:

        flash('Acesso negado!', 'danger')

        return redirect(url_for('admin_login'))

    

    group = GuestGroup.query.get_or_404(group_id)

    

    group.name = request.form.get('name')

    group.description = request.form.get('description')

    

    db.session.commit()

    

    flash(f'Grupo {group.name} atualizado com sucesso!', 'success')

    return redirect(url_for('admin_groups'))



@app.route('/admin/delete_group/<int:group_id>', methods=['POST'])

def delete_group(group_id):

    """Deletar grupo"""

    if 'admin_id' not in session:

        flash('Acesso negado!', 'danger')

        return redirect(url_for('admin_login'))

    

    group = GuestGroup.query.get_or_404(group_id)

    name = group.name

    

    # Remove a associação dos convidados com o grupo

    for guest in group.guests:

        guest.group_id = None

    

    db.session.delete(group)

    db.session.commit()

    

    flash(f'Grupo {name} removido com sucesso!', 'success')

    return redirect(url_for('admin_groups'))



@app.route('/admin/venue')

def admin_venue():

    """Gerenciar informações do local"""

    if 'admin_id' not in session:

        flash('Acesso negado!', 'danger')

        return redirect(url_for('admin_login'))

    

    venue = VenueInfo.query.first()

    return render_template('admin_venue.html', venue=venue)



@app.route('/admin/update_venue', methods=['POST'])

def update_venue():

    """Gerenciar informações do local (POST)"""

    if 'admin_id' not in session:

        flash('Acesso negado!', 'danger')

        return redirect(url_for('admin_login'))



    venue = VenueInfo.query.first()

    if venue is None:

        venue = VenueInfo()

        db.session.add(venue)



    # Mapeamento de meses para evitar dependência de locale

    meses_map = {

        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,

        'julho': 7, 'agosto': 8, 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'

    }



    try:

        venue.name = request.form.get('name')

        venue.address = request.form.get('address')

        venue.map_link = request.form.get('map_link')

        venue.description = request.form.get('description')

        

        # Campos de data e hora

        date_str = request.form.get('date')

        time_str = request.form.get('time')

        event_datetime_str = request.form.get('event_datetime')

        

        # Conversão de data sem depender do locale

        if date_str:

            partes = date_str.lower().replace(' de ', ' ').split()

            if len(partes) == 3:

                dia = int(partes[0])

                mes_nome = partes[1]

                ano = int(partes[2])

                mes = meses_map.get(mes_nome)

                if mes:

                    venue.date = date(ano, mes, dia)

                else:

                    raise ValueError("Nome do mês inválido.")

            else:

                raise ValueError("Formato de data inválido.")

        else:

            venue.date = None

        

        if time_str:

            time_str_clean = time_str.replace(" da manhã", "").replace(" da noite", "").strip()

            venue.time = datetime.strptime(time_str_clean, "%H:%M").time()

        else:

            venue.time = None

        

        if event_datetime_str:

            venue.event_datetime = datetime.fromisoformat(event_datetime_str)

        else:

            venue.event_datetime = None

            

        db.session.commit()

        flash("Local do evento atualizado com sucesso!", "success")

    

    except ValueError as e:

        db.session.rollback()

        logging.error(f"Erro de formato de data/hora: {e}")

        flash("Erro: verifique os formatos de Data (Ex: 19 de Outubro de 2025) e Hora (Ex: 18:30).", "danger")

    except Exception as e:

        db.session.rollback()

        logging.error(f"Erro ao salvar informações do local: {e}")

        flash(f"Erro ao salvar as informações. Tente novamente. Detalhes: {str(e)}", "danger")



    return redirect(url_for('admin_venue'))

    

@app.route('/admin/gifts')

def admin_gifts():

    """Gerenciar lista de presentes"""

    if 'admin_id' not in session:

        flash('Acesso negado!', 'danger')

        return redirect(url_for('admin_login'))

    

    gifts = GiftRegistry.query.all()

    return render_template('admin_gifts.html', gifts=gifts)



@app.route('/admin/add_gift', methods=['POST'])

def add_gift():

    """Adicionar presente"""

    if 'admin_id' not in session:

        flash('Acesso negado!', 'danger')

        return redirect(url_for('admin_login'))

    

    item_name = request.form.get('item_name')

    description = request.form.get('description')

    price = request.form.get('price')

    image_url = request.form.get('image_url')

    pix_key = request.form.get('pix_key')

    pix_link = request.form.get('pix_link')

    credit_card_link = request.form.get('credit_card_link')

    

    if not item_name:

        flash('Nome do presente é obrigatório!', 'danger')

        return redirect(url_for('admin_gifts'))

    

    # Lidar com upload de imagem

    image_filename = None

    if 'image' in request.files:

        file = request.files['image']

        if file and file.filename != '':

            file_ext = os.path.splitext(secure_filename(file.filename))[1].lower()

            if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:

                image_filename = f"{uuid.uuid4().hex}{file_ext}"

                file_path = os.path.join('static/uploads/gifts', image_filename)

                

                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                file.save(file_path)

    

    gift = GiftRegistry(

        item_name=item_name,

        description=description,

        price=price,

        image_url=image_url,

        pix_key=pix_key,

        pix_link=pix_link,

        credit_card_link=credit_card_link,

        image_filename=image_filename

    )

    

    db.session.add(gift)

    db.session.commit()

    

    flash(f'Presente {item_name} adicionado com sucesso!', 'success')

    return redirect(url_for('admin_gifts'))



@app.route('/admin/edit_gift/<int:gift_id>', methods=['POST'])

def edit_gift(gift_id):

    """Editar presente"""

    if 'admin_id' not in session:

        flash('Acesso negado!', 'danger')

        return redirect(url_for('admin_login'))

    

    gift = GiftRegistry.query.get_or_404(gift_id)

    

    gift.item_name = request.form.get('item_name')

    gift.description = request.form.get('description')

    gift.price = request.form.get('price')

    gift.image_url = request.form.get('image_url')

    gift.pix_key = request.form.get('pix_key')

    gift.pix_link = request.form.get('pix_link')

    gift.credit_card_link = request.form.get('credit_card_link')

    gift.is_active = bool(request.form.get('is_active'))

    

    db.session.commit()

    

    flash(f'Presente {gift.item_name} atualizado com sucesso!', 'success')

    return redirect(url_for('admin_gifts'))



@app.route('/admin/delete_gift/<int:gift_id>', methods=['POST'])

def delete_gift(gift_id):

    """Deletar presente"""

    if 'admin_id' not in session:

        flash('Acesso negado!', 'danger')

        return redirect(url_for('admin_login'))

    

    gift = GiftRegistry.query.get_or_404(gift_id)

    name = gift.item_name

    

    db.session.delete(gift)

    db.session.commit()

    

    flash(f'Presente {name} removido com sucesso!', 'success')

    return redirect(url_for('admin_gifts'))



@app.route('/gifts')

def gifts():

    """Página pública da lista de presentes"""

    gifts = GiftRegistry.query.filter_by(is_active=True).all()

    return render_template('gifts.html', gifts=gifts)



@app.route('/api/event-datetime')

def api_event_datetime():

    """API para obter a data do evento para contagem regressiva"""

    venue = VenueInfo.query.first()

    if venue and venue.event_datetime:

        return jsonify({

            'datetime': venue.event_datetime.isoformat(),

            'success': True

        })

    else:

        return jsonify({

            'datetime': '2025-10-19T08:30:00',

            'success': True

        })



@app.route('/admin/settings', methods=['GET', 'POST'])

def admin_settings():

    """Página de configurações do administrador"""

    if 'admin_id' not in session:

        flash('Acesso negado! Faça login primeiro.', 'danger')

        return redirect(url_for('admin_login'))

    

    if request.method == 'POST':

        current_password = request.form.get('current_password')

        new_password = request.form.get('new_password')

        confirm_password = request.form.get('confirm_password')

        

        if not all([current_password, new_password, confirm_password]):

            flash('Todos os campos são obrigatórios!', 'danger')

            return render_template('admin_settings.html')

        

        admin = Admin.query.get(session['admin_id'])

        if not check_password_hash(admin.password_hash, current_password):

            flash('Senha atual incorreta!', 'danger')

            return render_template('admin_settings.html')

        

        if new_password != confirm_password:

            flash('As novas senhas não coincidem!', 'danger')

            return render_template('admin_settings.html')

        

        if len(new_password) < 6:

            flash('A nova senha deve ter pelo menos 6 caracteres!', 'danger')

            return render_template('admin_settings.html')

        

        admin.password_hash = generate_password_hash(new_password)

        db.session.commit()

        

        flash('Senha alterada com sucesso!', 'success')

        return redirect(url_for('admin_dashboard'))

        

    return render_template('admin_settings.html')



@app.route('/admin/whatsapp')

def admin_whatsapp():

    """Página para envio de mensagens WhatsApp"""

    if 'admin_id' not in session:

        flash('Acesso negado!', 'danger')

        return redirect(url_for('admin_login'))

    

    guests = Guest.query.filter(Guest.phone.isnot(None)).all()

    groups = GuestGroup.query.all()

    venue = VenueInfo.query.first()

    

    return render_template('admin_whatsapp.html', guests=guests, groups=groups, venue=venue)



@app.route('/admin/send_whatsapp', methods=['POST'])

def send_whatsapp():

    """Enviar mensagem WhatsApp"""

    if 'admin_id' not in session:

        flash('Acesso negado!', 'danger')

        return redirect(url_for('admin_login'))

    

    data = request.get_json()

    

    recipient_type = data.get('recipient_type')

    message = data.get('message')

    message_type = data.get('message_type', 'custom')

    

    if not message:

        return jsonify({'error': 'Mensagem é obrigatória'}), 400

    

    phone_numbers = []

    

    if recipient_type == 'individual':

        guest_id = data.get('guest_id')

        guest = Guest.query.get(guest_id)

        if guest and guest.phone:

            phone_numbers.append(guest.phone)

    

    elif recipient_type == 'group':

        group_id = data.get('group_id')

        group = GuestGroup.query.get(group_id)

        if group:

            phone_numbers = [g.phone for g in group.guests if g.phone]

    

    elif recipient_type == 'all':

        guests = Guest.query.filter(Guest.phone.isnot(None)).all()

        phone_numbers = [g.phone for g in guests]

    

    elif recipient_type == 'status':

        status = data.get('status')

        guests = Guest.query.filter(Guest.rsvp_status == status, Guest.phone.isnot(None)).all()

        phone_numbers = [g.phone for g in guests]

    

    if not phone_numbers:

        return jsonify({'error': 'Nenhum número de telefone encontrado'}), 400

    

    if message_type != 'custom':

        venue = VenueInfo.query.first()

        if venue:

            message = get_wedding_message(message_type,

                                         date=venue.date,

                                         time=venue.time,

                                         venue=venue.name,

                                         address=venue.address,

                                         rsvp_link=request.url_root + 'rsvp',

                                         gift_link=request.url_root + 'gifts')

    

    results = send_bulk_whatsapp_messages(phone_numbers, message)

    

    return jsonify({

        'success': True,

        'results': results

    })



@app.route('/admin/group_guests/<int:group_id>')

def get_group_guests(group_id):

    """API para obter os convidados de um grupo específico."""

    if 'admin_id' not in session:

        return jsonify({'error': 'Acesso negado'}), 403

    

    group = GuestGroup.query.get_or_404(group_id)

    guests_data = [{

        'id': guest.id,

        'name': guest.name,

        'phone': guest.phone,

        'rsvp_status': guest.rsvp_status,

        'group_name': group.name

    } for guest in group.guests]

    

    return jsonify({'guests': guests_data})



@app.errorhandler(404)

def not_found(error):

    return render_template('404.html'), 404



@app.errorhandler(500)

def internal_error(error):

    db.session.rollback()

    return render_template('500.html'), 500



@app.before_request

def create_admin():

    """Criar admin se não existir"""

    try:

        if not Admin.query.first():

            admin = Admin(

                username='admin',

                password_hash=generate_password_hash('admin123')

            )

            db.session.add(admin)

            db.session.commit()

            print("✅ Admin criado automaticamente")

    except Exception as e:

        print(f"Erro ao criar admin: {e}")



@app.route('/healthz')

def healthz():

    """

    Verifica a saúde básica do aplicativo e a conexão com o banco de dados (Supabase).

    O objetivo principal é responder 200 OK para manter o serviço ativo e

    verificar a conectividade crítica.

    """

    try:

        db.session.execute(text("SELECT 1")).scalar()

        

        if not os.environ.get("DATABASE_URL"):

            raise ValueError("DATABASE_URL environment variable is missing.")



        return jsonify({

            "status": "ok",

            "message": "Application is healthy and database is connected."

        }), 200



    except Exception as e:

        current_app.logger.error(f"Health check failed: {e}")

        return jsonify({

            "status": "error",

            "message": f"Application unhealthy or critical component failed: {str(e)}"

        }), 500
