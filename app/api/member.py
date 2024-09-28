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
member_bp = Blueprint('member', __name__)

@member_bp.route('/members', methods=['GET'])
@login_required
def get_members():
    members = Member.query.all()
    result = [{'id': member.id, 
               'name': member.name,
               'phone': member.phone,
               'points': member.points,
               'registration_time': member.registration_time,
               'total_stay_duration': member.get_total_stay_duration()} for member in members]
    return jsonify(result)

@member_bp.route('/members', methods=['POST'])
@login_required
def add_member():
    data = request.get_json() 
    new_member = Member(name=data['name'], phone=data['phone'])
    db.session.add(new_member)
    db.session.commit()
    return jsonify({'success': True, 'message': 'New member added','id':new_member.id}), 200

@member_bp.route('/members/<int:id>', methods=['PUT'])
@login_required
def update_member(id):
    data = request.get_json()
    member = Member.query.get(id)
    if not member:
        return jsonify({'message': 'Member not found'}), 404

    # 记录更改前的值
    original_name = member.name
    original_phone = member.phone
    original_points = member.points

    # 更新会员信息
    member.name = data['name']
    member.phone = data['phone']
    member.points = data['points']
    db.session.commit()

    # 记录更改日志
    changes = []
    if original_points != data['points']:
        changes.append(f"{original_points} -> {data['points']}")

    if changes:
        log_entry = MemberUpdateLog(
            member_id=id,
            admin_id=current_user.id,
            changes=", ".join(changes)
        )
        db.session.add(log_entry)
        db.session.commit()

    return jsonify({'message': 'Member updated'})

@member_bp.route('/members/<int:id>', methods=['DELETE'])
@login_required
def delete_member(id):
    member = Member.query.get(id)
    if not member:
        return jsonify({'message': 'Member not found'}), 404
    db.session.delete(member)
    db.session.commit()
    return jsonify({'message': 'Member deleted'})



@member_bp.route('/member/<int:member_id>/details', methods=['GET'])
@login_required
def get_member_details(member_id):
    # 查询会员的房间停留记录
    stay_records = Stay.query.filter_by(member_id=member_id).all()
    result = []
    for record in stay_records:
        if record.start_time is None or record.end_time is None:
            continue
        
        # 根据 room_id 查询 Room 表获取 room_name
        room = Room.query.get(record.room_id)
        room_name = room.name if room else 'Unknown'
        
        # 计算停留时长（小时）
        duration = record.end_time - record.start_time
        duration_hours = duration.total_seconds() / 3600
        
        # 计算积分
        #record.calculate_points()
        
        # 获取管理员信息
        admin_name = record.admin.username if record.admin else 'Unknown'
        
        result.append({
            'member_id': record.member_id,
            'room_id': record.room_id,
            'room_name': room_name,  # 添加 room_name 字段
            'start_time': (record.start_time + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': (record.end_time + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
            'duration_hours': round(duration_hours, 2),  # 停留时长（小时）
            'points': record.points,  # 此次停留获得的积分
            'admin_name': admin_name  # 添加 admin_name 字段
        })
    
    # 按 end_time 降序排序
    result = sorted(result, key=lambda x: x['end_time'], reverse=True)
    
    return jsonify(result)

@member_bp.route('/member/<int:member_id>/room/<int:room_id>/products', methods=['GET'])
@login_required
def get_member_room_products(member_id, room_id):
    start_time_str = request.args.get('start_time')
    end_time_str = request.args.get('end_time')

    if not start_time_str or not end_time_str:
        return jsonify({'message': 'Missing parameters'}), 400

    try:
        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        # 减去 8 小时
        start_time -= timedelta(hours=8)
        end_time -= timedelta(hours=8)

    except ValueError:
        return jsonify({'message': 'Invalid date format'}), 400

    # 获取所有符合 member_id 和 room_id 条件的 stay_records
    all_stay_records = Stay.query.filter_by(member_id=member_id, room_id=room_id).all()

    # 遍历记录，筛选出符合时间条件的记录
    stay_records = []
    for record in all_stay_records:
        # 去掉 record.start_time 和 record.end_time 的秒以下部分
        record_start_time = record.start_time.replace(microsecond=0)
        record_end_time = record.end_time.replace(microsecond=0)
        
        if record_start_time >= start_time and record_end_time <= end_time:
            stay_records.append(record)

    result = []
    for record in stay_records:
        if record.start_time is None:
            continue
        
        consumptions = Consumption.query.filter_by(stay_record_id=record.id).all()
        product_list = [{'name': consumption.product.name, 
                         'points': consumption.product.points, 
                         'quantity': consumption.quantity} for consumption in consumptions]
        
        result.append({
            'room_id': record.room_id,
            'start_time': record.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': record.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'products': product_list
        })
    return jsonify(result)



## 获取未在指定房间中的会员列表
@member_bp.route('/available_members', methods=['GET'])
@login_required
def get_available_members():
    # 获取所有会员
    # 获取所有会员
    all_members = Member.query.all()
    members_data = []

    for member in all_members:
        # 检查会员是否已经在其他房间中
        existing_stays = Stay.query.filter_by(member_id=member.id).all()
        is_available = True

        for stay in existing_stays:
            if stay.start_time is None or stay.end_time is None:
                is_available = False
                break

        if is_available:
            members_data.append({
                'id': member.id,
                'name': member.name,
                'phone': member.phone,
                'status': 'available'
            })
        else:
            members_data.append({
                'id': member.id,
                'name': member.name,
                'phone': member.phone,
                'status': 'occupied'
            })

    return jsonify(members_data), 200



@member_bp.route('/members/<int:member_id>/update-logs', methods=['GET'])
@login_required
def get_member_update_logs(member_id):
    # 获取 UTC+8 时区
    tz = pytz.timezone('Asia/Shanghai')
    logs = MemberUpdateLog.query.filter_by(member_id=member_id).join(User, MemberUpdateLog.admin_id == User.id).all()
    if not logs:
        return jsonify({'message': 'No update logs found for this member'}), 404

    log_list = []
    for log in logs:
        update_time_utc8 = log.update_time.replace(tzinfo=pytz.utc).astimezone(tz)
        log_list.append({
            'id': log.id,
            'member_id': log.member_id,
            'admin_id': log.admin_id,
            'admin_username': log.admin.username,
            'update_time': update_time_utc8.strftime('%Y-%m-%d %H:%M:%S'),
            'changes': log.changes
        })

    return jsonify(log_list), 200