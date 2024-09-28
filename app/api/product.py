from flask import Blueprint, jsonify, request,send_file
from flask_login import login_required,current_user
from ..models import User, Room, Member, Product, Consumption,Stay,MemberUpdateLog
from app import db
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone,timedelta
import pytz
from sqlalchemy.exc import SQLAlchemyError
import os
import shutil
from apscheduler.schedulers.background import BackgroundScheduler
product_bp = Blueprint('product', __name__)

# Products product
@product_bp.route('/products', methods=['GET'])
@login_required
def get_products():
    products = Product.query.all()
    result = [{'id': product.id, 'name': product.name, 'points': product.points} for product in products]
    return jsonify(result)

@product_bp.route('/products', methods=['POST'])
@login_required
def add_product():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
        
        required_fields = ['name', 'points']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        new_product = Product(name=data['name'], points=data['points'])
        db.session.add(new_product)
        db.session.commit()
        return jsonify({'message': 'New product added','id':new_product.id}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/products/<int:id>', methods=['PUT'])
@login_required
def update_product(id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    product = Product.query.get(id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    product.name = data.get('name', product.name)
    product.points = data.get('points', product.points)

    try:
        db.session.commit()
        return jsonify({'message': 'Product updated'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/products/<int:id>', methods=['DELETE'])
@login_required
def delete_product(id):
    try:
        product = Product.query.get(id)
        if not product:
            return jsonify({'message': 'Product not found'}), 404
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500