from faker import Faker
from app import db
from app.models import Room, Product, Consumption, Member, User, Stay
from werkzeug.security import generate_password_hash
from datetime import datetime,timezone
import random

fake = Faker()

def generate_test_data():
    # 创建房间数据
    rooms = []
    room_data = {'思香亭':20,'云静苑':30,'云翠苑':40,'云秋阁':50,'艺云阁':60,'馨云楼':40,'翠馨居':30,'仙踪林':20,'怡云居':10,'梦云轩':5}
    for name, coefficient in room_data.items():
        room = Room(
            name=name,
            coefficient=coefficient
        )
        db.session.add(room)
        rooms.append(room)

    # 创建产品数据
    products = []
    products_data = {'可乐':2, '雪碧':3, '芬达':4, '矿泉水':1, '红牛':5, '脉动':3, '果粒橙':4, '冰红茶':3, '绿茶':2, '奶茶':4}
    for name, points in products_data.items():

        product = Product(
            name=name,
            points=points,
            add_date=fake.date_time_this_decade(tzinfo=timezone.utc)
        )
        db.session.add(product)
        products.append(product)

    # 创建会员数据
    members = []
    for _ in range(10):
        member = Member(
            name=fake.name(),
            phone=fake.phone_number(),
            points=fake.random_int(min=0, max=1000),  # 随机生成累计积分
            registration_time=datetime.now(timezone.utc)  # 设置注册时间为当前时间
        )
        db.session.add(member)
        members.append(member)

    db.session.commit()  # 提交以确保消费数据和停留数据可以引用已存在的会员和房间

    # 创建停留数据
    stays = []
    for _ in range(10):
        start_time = fake.date_time_this_decade(tzinfo=timezone.utc)
        end_time = fake.date_time_between(start_date=start_time, end_date="now", tzinfo=timezone.utc)
        member_id = random.choice(members).id
        room_id = random.choice(rooms).id

        stay = Stay(
            member_id=member_id,
            room_id=room_id,
            start_time=start_time,
            end_time=end_time,
            points=0  # 初始积分为0
        )
        db.session.add(stay)
        stays.append(stay)

    db.session.commit()  # 提交以确保 stay_record_id 有效

    # 创建消费数据
    for _ in range(10):
        consumption = Consumption(
            product_id=random.choice(products).id,
            stay_record_id=random.choice(stays).id,  # 引用已存在的 stay_record_id
            quantity=fake.random_int(min=1, max=10)  # 添加 quantity 字段
        )
        db.session.add(consumption)

    db.session.commit()  

    # 创建用户数据
    user = User(
        username="yuancong",
        password=generate_password_hash('123')
    )
    db.session.add(user)

    db.session.commit()

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        generate_test_data()
        print("测试数据生成完毕")