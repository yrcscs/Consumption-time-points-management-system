from flask import Blueprint, jsonify, request
from flask_login import login_required
from ..models import Member, Stay
from app import db
from datetime import datetime, timezone
timer_bp = Blueprint('api', __name__)

@timer_bp.route('/get-timers', methods=['GET'])
@login_required
def get_timers():
    # 查询所有正在计时的会员
    active_stays = Stay.query.filter_by(end_time=None).all()
    
    # 构建响应数据
    timers = [
        {
            'member_id': stay.member_id,
            'room_id': stay.room_id,
            'start_time': stay.start_time.isoformat() if stay.start_time else None
        }
        for stay in active_stays
    ]
    
    return jsonify(timers), 200

@timer_bp.route('/start-timer/<int:room_id>/<int:member_id>', methods=['POST'])
@login_required
def start_timer(room_id, member_id):
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'message': 'Member not found'}), 404

    # 检查会员是否已经在计时
    existing_stay = Stay.query.filter(
        Stay.member_id == member_id,
        Stay.start_time != None,
        Stay.end_time == None
    ).first()
    if existing_stay:
        return jsonify({
            'message': 'Timer already started',
            'stay_id': existing_stay.id,
            'start_time': existing_stay.start_time.isoformat()
        }), 400

    # 获取手动指定的时间戳
    data = request.get_json()
    manual_start_time = data.get('start_time')
    if manual_start_time:
        # 传入的时间戳格式需要与 datetime.now(timezone.utc) 生成的格式相同
        start_time = datetime.fromisoformat(manual_start_time)
    else:
        start_time = datetime.now(timezone.utc)

    # 查找start_time和end_time都为空的记录
    pending_stay = Stay.query.filter(
        Stay.member_id == member_id,
        Stay.room_id == room_id,
        Stay.start_time == None,
        Stay.end_time == None
    ).first()
    if pending_stay:
        # 修改已有记录的start_time
        pending_stay.start_time = start_time
        db.session.commit()
        return jsonify({
            'message': 'Timer started',
            'stay_id': pending_stay.id,
            'start_time': pending_stay.start_time.isoformat()
        }), 200

    return jsonify({'message': 'No pending stay found'}), 404

@timer_bp.route('/stop-timer/<int:member_id>/<int:admin_id>', methods=['POST'])
@login_required
def stop_timer(member_id, admin_id):
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'message': 'Member not found'}), 404

    # 查找未结束的停留记录
    stay = Stay.query.filter_by(member_id=member_id, end_time=None).first()
    if not stay:
        return jsonify({'message': 'No active timer found'}), 400

    # 获取传入的消费总积分和手动指定的时间戳
    data = request.get_json()
    total_consumption_points = data.get('total_consumption_points')
    if total_consumption_points is None:
        return jsonify({'message': 'Total consumption points not provided'}), 400

    manual_end_time = data.get('end_time')
    if manual_end_time:
        # 传入的时间戳格式需要与 datetime.now(timezone.utc) 生成的格式相同
        end_time = datetime.fromisoformat(manual_end_time)
    else:
        end_time = datetime.now(timezone.utc)

    # 结束计时并计算积分
    stay.end_time = end_time
    stay.calculate_points()  # 计算因停留获得的积分 （正数）

    # 计算获得与消费的差值作为本次停留所获得的积分（可以是负数）
    net_points = stay.points - total_consumption_points

    # 更新积分
    stay.points = net_points
    member.points += net_points

    stay.admin_id = admin_id  # 记录操作员 ID
    db.session.commit()
    
    # 返回响应，包括 end_time 和 net_points
    return jsonify({
        'message': 'Timer stopped',
        'net_points': net_points,
        'end_time': stay.end_time.isoformat()  # 将 end_time 转换为 ISO 格式字符串
    }), 200