from flask import Blueprint, abort, render_template,request
from .models import Room, Member, Consumption
from flask_login import login_required
from datetime import datetime
from flask import Flask, render_template, session
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    rooms = Room.query.all()
    members = Member.query.all()
    consumptions = Consumption.query.all()
    if 'username' in session:
        username = session['username']
    else:
        username = '管理员2'  # 默认用户名
    return render_template('dashboard.html',username=username)

@dashboard_bp.route('/controlpanel')
@login_required
def controlpanel():
    rooms = Room.query.all()
    members = Member.query.all()
    consumptions = Consumption.query.all()
    return render_template('controlpanel.html',userid=session['userid'],username=session['username'])

@dashboard_bp.route('/roommanage')
@login_required
def roommanage():
    rooms = Room.query.all()
    members = Member.query.all()
    consumptions = Consumption.query.all()
    return render_template('roommanage.html')


@dashboard_bp.route('/productsmanage')
@login_required
def productsmanage():
    rooms = Room.query.all()
    members = Member.query.all()
    consumptions = Consumption.query.all()
    return render_template('productsmanage.html')



@dashboard_bp.route('/memberdetail/<int:member_id>')
@login_required
def member_detail(member_id):
    member = Member.query.get(member_id)
    if not member:
        abort(404)
        # 将member对象转换为字典
    member_dict = {
        'id': member.id,
        'name': member.name,
        'phone': member.phone,
        'points': member.points
    }
    
    return render_template('memberdetail.html', member=member_dict)

# 访问某个房间中某个会员的消费详情（Consumption）
@dashboard_bp.route('/shoppingdetail/<int:room_id>/<int:member_id>')
@login_required
def shopping_detail(member_id):

    
    return render_template('shoppingdetail.html')


