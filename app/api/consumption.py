from flask import Blueprint, jsonify, request
from flask_login import login_required
from ..models import Consumption, Stay, Product
from app import db
from sqlalchemy.exc import SQLAlchemyError
consumption_bp = Blueprint('consumption', __name__)

# Consumptions consumption
@consumption_bp.route('/getconsumptions', methods=['POST'])
@login_required
def get_consumptions():
    data = request.get_json()
    stay_record_id = data.get('stay_record_id')
    
    if stay_record_id:
        consumptions = Consumption.query.filter_by(stay_record_id=stay_record_id).all()
    else:
        consumptions = Consumption.query.all()
    
    total_points = 0  # 初始化总积分
    result = []
    
    for consumption in consumptions:
        stay_record = Stay.query.get(consumption.stay_record_id)
        product_points = consumption.product.points  # 获取商品的积分
        consumption_points = consumption.quantity * product_points  # 计算该消费记录的积分
        total_points += consumption_points  # 累加到总积分
        
        result.append({
            'id': consumption.id,
            'product_id': consumption.product_id,
            'product_name': consumption.product.name,
            'quantity': consumption.quantity,
            'stay_record_id': consumption.stay_record_id,
            'room_id': stay_record.room_id,  # 从 stay_record 获取 room_id
            'member_id': stay_record.member_id,  # 从 stay_record 获取 member_id
            'consumption_points': consumption_points  # 添加该消费记录的积分
        })
    
    return jsonify({'consumptions': result, 'total_points': total_points})

@consumption_bp.route('/consumptions', methods=['POST'])
@login_required
def add_consumptions():
    data = request.get_json()
    products = data.get('products', [])
    stay_record_id = data.get('stay_record_id')

    # 根据 stay_record_id 查询 member_id
    stay_record = Stay.query.get(stay_record_id)
    if not stay_record:
        return {"error": "Stay record not found"}, 404

    member_id = stay_record.member_id

    for product in products:
        product_id = product['product_id']
        quantity = product['quantity']

        # 查找是否已经存在相同的消费记录
        existing_consumption = Consumption.query.filter_by(
            stay_record_id=stay_record_id,
            product_id=product_id
        ).first()

        if existing_consumption:
            # 更新现有消费记录的数量
            existing_consumption.quantity = quantity
        else:
            # 创建新的消费记录
            new_consumption = Consumption(
                product_id=product_id,
                stay_record_id=stay_record_id,
                member_id=member_id,
                quantity=quantity
            )
            db.session.add(new_consumption)

    db.session.commit()
    return {"message": "Consumptions added successfully"}, 201

@consumption_bp.route('/consumptions/<int:id>', methods=['PUT'])
@login_required
def update_consumption(id):
    data = request.get_json()
    consumption = Consumption.query.get(id)
    if not consumption:
        return jsonify({'message': 'Consumption not found'}), 404
    consumption.name = data['name']
    consumption.member_id = data['member_id']
    consumption.product_id = data['product_id']
    consumption.cost = data['cost']
    db.session.commit()
    return jsonify({'message': 'Consumption updated'})

@consumption_bp.route('/consumptions/<int:id>', methods=['DELETE'])
@login_required
def delete_consumption(id):
    consumption = Consumption.query.get(id)
    if not consumption:
        return jsonify({'message': 'Consumption not found'}), 404
    db.session.delete(consumption)
    db.session.commit()
    return jsonify({'message': 'Consumption deleted'})