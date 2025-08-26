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


@app.route('/search_guest', methods=['POST'])
def search_guest():
    """Busca convidado por nome e retorna o grupo ou os indivíduos."""
    name = request.form.get('name', '').strip()

    if not name:
        return jsonify({'error': 'Nome é obrigatório'}), 400

    # Normalizar busca para evitar problemas de case/acento
    guests_list = Guest.query.filter(func.lower(Guest.name).like(f"%{name.lower()}%")).all()

    if not guests_list:
        return jsonify({'error': 'Convidado não encontrado'}), 404

    # Agrupar pelo group_id
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

    return jsonify({
        'guests': guests_data,
        'group_name': group_name
    })


@app.route('/search_guest_individual', methods=['POST'])
def search_guest_individual():
    """Busca convidados individuais por nome para seleção específica"""
    name = request.form.get('name', '').strip()

    if not name or len(name) < 2:  # reduzido de 4 para 2 caracteres
        return jsonify({'error': 'Digite pelo menos 2 letras'}), 400

    guests_list = Guest.query.filter(func.lower(Guest.name).like(f"%{name.lower()}%")).all()

    if not guests_list:
        return jsonify({'error': 'Nenhum convidado encontrado'}), 404

    guests_data = [{
        'id': g.id,
        'name': g.name,
        'phone': g.phone,
        'rsvp_status': g.rsvp_status,
        'group_id': g.group_id,
        'group_name': g.group.name if g.group else None
    } for g in guests_list]

    return jsonify({
        'guests': guests_data,
        'total_found': len(guests_data)
    })
