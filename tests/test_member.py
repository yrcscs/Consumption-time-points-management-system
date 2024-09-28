import unittest
from flask import Flask
from app import create_app, db
from app.models import User, Member, Stay, MemberUpdateLog
from datetime import datetime, timezone, timedelta
import pytz

class MemberTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_get_member_update_logs(self):
        with self.app.app_context():
            # 添加测试数据
            member = Member(id=1, name='Test Member')
            admin = User(id=1, username='admin')
            log = MemberUpdateLog(
                member_id=1,
                admin_id=1,
                update_time=datetime.now(timezone.utc),
                changes='Initial creation'
            )
            db.session.add(member)
            db.session.add(admin)
            db.session.add(log)
            db.session.commit()

        # 发送 GET 请求
        response = self.client.get('/api/members/1/update-logs')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['member_id'], 1)
        self.assertEqual(data[0]['admin_username'], 'admin')
        self.assertEqual(data[0]['changes'], 'Initial creation')

    def test_get_available_members(self):
        with self.app.app_context():
            # 添加测试数据
            member1 = Member(id=1, name='Available Member', phone='1234567890')
            member2 = Member(id=2, name='Occupied Member', phone='0987654321')
            stay = Stay(member_id=2, room_id=101, start_time=datetime.now(timezone.utc))
            db.session.add(member1)
            db.session.add(member2)
            db.session.add(stay)
            db.session.commit()

        # 发送 GET 请求
        response = self.client.get('/api/available_members')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['status'], 'available')
        self.assertEqual(data[1]['status'], 'occupied')

if __name__ == '__main__':
    unittest.main()