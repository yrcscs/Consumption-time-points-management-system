from . import db
from datetime import datetime, timezone
from flask_login import UserMixin
import math
from sqlalchemy.orm import relationship
import math


class MemberUpdateLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    update_time = db.Column(db.DateTime, default=datetime.utcnow)
    changes = db.Column(db.String, nullable=False)

    admin = db.relationship('User', backref=db.backref('logs', lazy=True))


    def __init__(self, member_id, admin_id, changes):
        self.member_id = member_id
        self.admin_id = admin_id
        self.changes = changes

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    coefficient = db.Column(db.Float, nullable=False, default=1)  # 积分系数
    status = db.Column(db.Boolean, nullable=False, default=True)  # 房间状态,表示可用性，删除房间即是将status设置为False

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    points = db.Column(db.Integer, nullable=False, default=0)
    add_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Consumption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    stay_record_id = db.Column(db.Integer, db.ForeignKey('stay.id'), nullable=False)  # 添加 stay_record_id 字段
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)  # 添加 member_id 字段
    quantity = db.Column(db.Integer)
    product = db.relationship('Product', backref='consumptions')  # 定义与 Product 的关系
    member = db.relationship('Member', backref='member_consumptions')  # 定义与 Member 的关系，避免冲突
    
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    points = db.Column(db.Integer, nullable=False, default=0)  # 用户的累计积分
    registration_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    stays = relationship('Stay', backref='member_stays', cascade='all, delete-orphan')  # 修改 backref 名称，避免冲突
    consumptions = relationship('Consumption', backref='member_consumptions', cascade='all, delete-orphan')  # 修改 backref 名称，避免冲突
    update_logs = db.relationship('MemberUpdateLog', backref='member', cascade='all, delete-orphan')

    def get_total_stay_duration(self):
        total_duration = 0
        for stay in self.stays:
            if stay.end_time:
                start_time = stay.start_time
                end_time = stay.end_time

                # 确保 start_time 和 end_time 都是带有时区信息的 datetime 对象
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)

                # 计算时间差并转换为分钟
                duration_minutes = (end_time - start_time).total_seconds() / 60
                total_duration += duration_minutes
        return total_duration

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)



class Stay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    points = db.Column(db.Integer, nullable=False, default=0)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # 新增字段
    member = db.relationship('Member', backref=db.backref('stay_records', lazy=True))  # 修改 backref 名称，避免冲突
    room = db.relationship('Room', backref=db.backref('stays', lazy=True))
    admin = db.relationship('User', backref=db.backref('stays_handled', lazy=True))  # 新增关系
    

    def calculate_points(self):
        """计算积分
        

        
        """
        # if self.end_time:
        #     # 确保 start_time 和 end_time 都是带有时区信息的 datetime 对象
        #     if self.start_time.tzinfo is None:
        #         self.start_time = self.start_time.replace(tzinfo=timezone.utc)
        #     if self.end_time.tzinfo is None:
        #         self.end_time = self.end_time.replace(tzinfo=timezone.utc)

        #     # 计算时间差并转换为分钟
        #     duration_minutes = (self.end_time - self.start_time).total_seconds() / 60

        #     if duration_minutes <= 0:
        #         duration_minutes = 0
        #     if duration_minutes%60 >50:
        #         duration_hours = math.modf(duration_minutes/60)[1] + 1
        #     else:
        #         duration_hours = math.modf(duration_minutes/60)[1]
        #     # 获取房间的积分系数（每小时积分值）
        #     room_coefficient = self.room.coefficient
        #     # 计算最终积分
        #     self.points = int(duration_hours * room_coefficient)



        """计算积分"""
        if self.end_time:
            # 确保 start_time 和 end_time 都是带有时区信息的 datetime 对象
            if self.start_time.tzinfo is None:
                self.start_time = self.start_time.replace(tzinfo=timezone.utc)
            if self.end_time.tzinfo is None:
                self.end_time = self.end_time.replace(tzinfo=timezone.utc)
            # 计算时间差并转换为分钟
            duration_minutes = (self.end_time - self.start_time).total_seconds() / 60
            # 计算15分钟的时间段数，向上取整
            duration_quarters = math.ceil(duration_minutes / 15)
            # 获取房间的积分系数（每小时积分值）
            room_coefficient = self.room.coefficient
            # 计算每15分钟的积分值
            points_per_quarter = math.ceil(room_coefficient / 4)
            # 计算最终积分
            self.points = int(duration_quarters * points_per_quarter)