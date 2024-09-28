from flask import Blueprint, render_template
from flask_login import login_required
members_bp = Blueprint('members', __name__)

@members_bp.route('/members')
@login_required
def members():
    # 显示会员信息
    return render_template('member.html')