import unittest
import logging
from flask import Flask
from app import create_app, db
from app.models import Member, Stay, User
from datetime import datetime, timezone

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, filename='test_log.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TimerTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            # 获取主机名和端口
            host = '127.0.0.1'
            port = self.app.config.get('PORT', 5000)
            
            # 注册测试用户
            register_url = f'http://{host}:{port}/register'
            logger.debug(f"Register URL: {register_url}")
            self.client.post('/api/register', json=dict(
                username='testuser',
                password='testpassword'
            ))
            
            # 登录测试用户
            login_url = f'http://{host}:{port}/login'
            logger.debug(f"Login URL: {login_url}")
            response = self.client.post('/api/login', json=dict(
                username='testuser',
                password='testpassword'
            ))
            logger.debug(f"Response status code: {response.status_code}")
            self.assertEqual(response.status_code, 200)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_get_timers(self):
        with self.app.app_context():
            # 添加测试数据
            member = Member(id=1, name='Test Member', phone='1234567890')
            stay = Stay(member_id=1, room_id=101, start_time=datetime.now(timezone.utc))
            db.session.add(member)
            db.session.add(stay)
            db.session.commit()

        # 获取主机名和端口
        host = 'localhost'
        port = self.app.config.get('PORT', 5000)
        url = f'http://{host}:{port}/api/get-timers'
        logger.debug(f"Testing URL: {url}")

        # 发送 GET 请求
        response = self.client.get('/api/get-timers')
        logger.debug(f"Get Timer Response status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['member_id'], 1)
        self.assertEqual(data[0]['room_id'], 101)

    def test_start_timer(self):
        with self.app.app_context():
            # 添加测试数据
            member = Member(id=1, name='Test Member', phone='1234567890')
            db.session.add(member)
            db.session.commit()

        # 获取主机名和端口
        host = 'localhost'
        port = self.app.config.get('PORT', 5000)
        url = f'http://{host}:{port}/api/start-timer/101/1'
        logger.debug(f"Testing URL: {url}")

        # 发送 POST 请求
        response = self.client.post('/api/start-timer/101/1')
        logger.debug(f"Start Timer Response status code: {response.status_code}")
        logger.debug(f"Start Timer Response Message: {response.get_json()}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], 'Timer started')
        self.assertIsNotNone(data['stay_id'])

    def test_stop_timer(self):
        with self.app.app_context():
            # 添加测试数据
            member = Member(id=1, name='Test Member', phone='1234567890', points=100)
            stay = Stay(member_id=1, room_id=101, start_time=datetime.now(timezone.utc))
            db.session.add(member)
            db.session.add(stay)
            db.session.commit()

        # 获取主机名和端口
        host = 'localhost'
        port = self.app.config.get('PORT', 5000)
        url = f'http://{host}:{port}/api/stop-timer/1/1'
        logger.debug(f"Testing URL: {url}")

        # 发送 POST 请求
        response = self.client.post('/api/stop-timer/1/1', json={'total_consumption_points': 50})
        logger.debug(f"Response status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], 'Timer stopped')
        self.assertEqual(data['net_points'], member.points - 50)
        self.assertIn('end_time', data)

if __name__ == '__main__':
    unittest.main()