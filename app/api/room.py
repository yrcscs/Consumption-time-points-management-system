from flask import Blueprint, jsonify, request
from flask_login import login_required
from ..models import Room, Member, Stay, Consumption
from app import db
from datetime import datetime, timezone
room_bp = Blueprint('room', __name__)

# Rooms room


@room_bp.route('/rooms', methods=['GET'])
@login_required
def get_rooms():
    rooms = Room.query.filter_by(status=True).all()  # 只查询状态为可用的房间
    result = []
    for room in rooms:
        room_data = {
            'id': room.id,
            'name': room.name,
            'coefficient': room.coefficient
        }
        result.append(room_data)
    return jsonify(result),200

@room_bp.route('/rooms', methods=['POST'])
@login_required
def add_room():
    data = request.get_json()
    new_room = Room(
        name=data['name'],
        coefficient=data['coefficient']
    )
    db.session.add(new_room)
    db.session.commit()
    return jsonify({'message': 'New room added', 'id': new_room.id}), 200

@room_bp.route('/rooms/<int:id>', methods=['PUT'])
@login_required
def update_room(id):
    data = request.get_json()
    room = Room.query.get(id)
    if not room:
        return jsonify({'message': 'Room not found'}), 404
    room.name = data['name']
    room.coefficient = data['coefficient']  # 添加对 coefficient 字段的处理
    db.session.commit()
    return jsonify({'message': 'Room updated'}),200

@room_bp.route('/rooms/<int:id>', methods=['DELETE'])
@login_required
def delete_room(id):
    room = Room.query.get(id)
    if not room:
        return jsonify({'message': 'Room not found'}), 404
    
    room.status = False  # 将房间状态设置为不可用
    db.session.commit()
    return jsonify({'message': 'Room marked as inactive'})


## 添加会员到房间
@room_bp.route('/rooms/<int:room_id>/members', methods=['POST'])
@login_required
def add_members_to_room(room_id):
    data = request.get_json()
    member_ids = data.get('member_ids', [])
    start_timing = data.get('start_timing', False)

    room = Room.query.get(room_id)
    if not room:
        return jsonify({'message': 'Room not found'}), 404

    for member_id in member_ids:
        member = Member.query.get(member_id)
        if not member:
            return jsonify({'message': f'Member with ID {member_id} not found'}), 404

        # 检查会员是否已经在房间中
        existing_stay = Stay.query.filter_by(member_id=member_id, room_id=room_id, end_time=None).first()
        if existing_stay:
            continue  # 如果会员已经在房间中，跳过

        # 创建新的停留记录
        new_stay = Stay(
            member_id=member_id,
            room_id=room_id,
            start_time=datetime.now(timezone.utc) if start_timing else None
        )
        db.session.add(new_stay)

    db.session.commit()
    return jsonify({'message': 'Members added to room','stay_id':new_stay.id}), 201


## 从房间中移除会员
@room_bp.route('/rooms/<int:room_id>/members/<int:member_id>', methods=['DELETE'])
@login_required
def remove_member_from_room(room_id, member_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({'message': 'Room not found'}), 404

    member = Member.query.get(member_id)
    if not member:
        return jsonify({'message': f'Member with ID {member_id} not found'}), 404

    # 查找会员在房间中的停留记录，且 start_time 为空
    stay = Stay.query.filter_by(member_id=member_id, room_id=room_id, start_time=None).first()
    if not stay:
        return jsonify({'message': 'No matching stay record found'}), 404

    # 删除相关的 Consumption 记录
    Consumption.query.filter_by(stay_record_id=stay.id).delete()

    # 删除停留记录
    db.session.delete(stay)
    db.session.commit()

    return jsonify({'message': 'Member removed from room'}), 200



@room_bp.route('/rooms/<int:room_id>/members', methods=['GET'])
@login_required
def get_room_members(room_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({'message': 'Room not found'}), 404

    # 查询当前仍在房间中的会员信息
    stays = Stay.query.filter_by(room_id=room_id, end_time=None).all()

    result = [{'id': stay.member.id, 
               'name': stay.member.name, 
               'phone': stay.member.phone, 
               'points': stay.member.points,
               'is_timing': stay.start_time is not None,  # 判断是否已经开始计时
               'start_time': stay.start_time.isoformat() if stay.start_time else None  # 返回开始时间
               } for stay in stays]
    return jsonify(result)

@room_bp.route('/rooms/<int:room_id>/members/<int:member_id>/stay', methods=['GET'])
@login_required
def get_member_stay_in_room(room_id, member_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({'message': 'Room not found'}), 404

    stay = Stay.query.filter_by(room_id=room_id, member_id=member_id, end_time=None).first()
    if not stay:
        return jsonify({'message': 'Stay record not found'}), 404

    result = {
        'id': stay.id,
        'member_id': stay.member.id,
        'name': stay.member.name,
        'phone': stay.member.phone,
        'points': stay.member.points,
        'is_timing': stay.start_time is not None,  # 判断是否已经开始计时
        'start_time': stay.start_time.isoformat() if stay.start_time else None  # 返回开始时间
    }
    return jsonify(result)


