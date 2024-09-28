import unittest
import logging
from flask import Flask
from app import create_app, db
from app.models import Room, Member, Product, Stay, Consumption, User
from datetime import datetime, timezone, timedelta
from parameterized import parameterized

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, filename='test_log.log', filemode='w', format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s')
logger = logging.getLogger(__name__)

class BusinessFlowTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            # 注册管理员用户
            self.client.post('/api/register', json=dict(
                username='admin',
                password='adminpassword'
            ))
            # 登录管理员用户
            response = self.client.post('/api/login', json=dict(
                username='admin',
                password='adminpassword'
            ))
            self.assertEqual(response.status_code, 200)
            self.token = response.get_json().get('userid')

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    @parameterized.expand([
        # 格式: (room_name, room_coefficient, product_name, product_points, member_name, member_phone, total_consumption_points, start_offset, end_offset, expected_points)
        ("Room 1", 1, "Product 1", 100, "Member 1", "1234567890", 100, 0, 3600, -99),  # 60分钟，增长积分=1.5*1=1.5，消费积分=100，获得积分=-99
        ("Room 2", 2, "Product 2", 200, "Member 2", "0987654321", 200, 0, 7200, -196),  # 120分钟，增长积分=2.0*2=4.0，消费积分=200，获得积分=-196
        ("Room 3", 1, "Product 3", 150, "Member 3", "1122334455", 150, 0, 1800, -150),  # 30分钟，增长积分=0，消费积分=150，获得积分=-150
        ("Room 4", 1, "Product 4", 100, "Member 4", "2233445566", 100, 0, 5400, -99),  # 90分钟，增长积分=1*1=1，消费积分=100，获得积分=-99
        ("Room 5", 2, "Product 5", 200, "Member 5", "3344556677", 200, 0, 4500, -198),  # 75分钟，增长积分=2.0*1=2.0，消费积分=200，获得积分=-198
        ("Room 6", 1, "Product 6", 150, "Member 6", "4455667788", 150, 0, 3000, -150),  # 50分钟，增长积分=0，消费积分=150，获得积分=-150
        ("Room 7", 3, "Product 7", 2, "Member 7", "5566778899", 2, 0, 3600, 1), # 60分钟，增长积分=3*1=3，消费积分=2，获得积分=1
        ("Room 8", 2, "Product 8", 200, "Member 8", "6677889900", 200, 0, 10260, -194),# 171分钟，增长积分=2.0*3=6.0，消费积分=200，获得积分=-196
    ])
    def test_business_flow(self, 
                           room_name, 
                           room_coefficient, 
                           product_name, 
                           product_points, 
                           member_name, 
                           member_phone, 
                           total_consumption_points, 
                           start_offset, 
                           end_offset, 
                           expected_points):
        headers = {'Authorization': f'Bearer {self.token}'}

        # 添加房间
        response = self.client.post('/api/rooms', json={
            'name': room_name,
            'coefficient': room_coefficient
        }, headers=headers)
        self.assertEqual(response.status_code, 200)
        room_id = response.get_json()['id']

        # # 添加产品
        # response = self.client.post('/api/products', json={
        #     'name': product_name,
        #     'points': product_points
        # }, headers=headers)
        # self.assertEqual(response.status_code, 200)
        # product_id = response.get_json()['id']

        # 添加会员
        response = self.client.post('/api/members', json={
            'name': member_name,
            'phone': member_phone
        }, headers=headers)
        self.assertEqual(response.status_code, 200)
        member_id = response.get_json()['id']

        # 将会员添加到房间
        response = self.client.post(f'/api/rooms/{room_id}/members', json={
            'member_ids': [member_id],
            'start_timing': False
        }, headers=headers)
        self.assertEqual(response.status_code, 201)
        stay_id = response.get_json()['stay_id']

        # 获取当前时间
        current_time = datetime.now(timezone.utc)

        # 计算开始和结束时间
        start_time = current_time + timedelta(seconds=start_offset)
        end_time = current_time + timedelta(seconds=end_offset)

        # 开始计时
        response = self.client.post(f'/api/start-timer/{room_id}/{member_id}', json={
            'start_time': start_time.isoformat()
        }, headers=headers)
        self.assertEqual(response.status_code, 200)

        # 停止计时
        response = self.client.post(f'/api/stop-timer/{member_id}/{self.token}', json={
            'total_consumption_points': total_consumption_points,
            'end_time': end_time.isoformat()
        }, headers=headers)
        self.assertEqual(response.status_code, 200)
        points_earned = response.get_json().get('net_points')
        self.assertEqual(points_earned, expected_points)

        # 获取会员信息
        response = self.client.get('/api/members', headers=headers)
        self.assertEqual(response.status_code, 200)
        members_info = response.get_json()
        self.assertTrue(any(member['name'] == member_name and member['phone'] == member_phone for member in members_info))


if __name__ == '__main__':
    unittest.main()