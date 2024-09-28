import unittest
import logging
from flask import Flask
from app import create_app, db
from app.models import Room, Member, Stay, User
from datetime import datetime, timezone

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, filename='test_log.log', filemode='w', format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s')
logger = logging.getLogger(__name__)

class RoomTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            # 获取主机名和端口
            host = '127.0.0.1'
            port = self.app.config.get('PORT', 5000)
            
            # 注册测试用户
            register_url = f'http://{host}:{port}/api/register'
            logger.debug(f"Register URL: {register_url}")
            self.client.post('/api/register', json=dict(
                username='testuser',
                password='testpassword'
            ))
            
            # 登录测试用户
            login_url = f'http://{host}:{port}/api/login'
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

    def test_get_rooms(self):
        with self.app.app_context():
            # 添加测试数据
            room = Room(name='Test Room', coefficient=1.0, status=True)
            db.session.add(room)
            db.session.commit()

        # 发送 GET 请求
        response = self.client.get('/api/rooms')
        logger.debug(f"Response status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Room')

    def test_add_room(self):
        # 发送 POST 请求
        response = self.client.post('/api/rooms', json={
            'name': 'New Room',
            'coefficient': 1.5
        })
        logger.debug(f"Response status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], 'New room added')

    def test_update_room(self):
        with self.app.app_context():
            # 添加测试数据
            room = Room(name='Old Room', coefficient=1.0, status=True)
            db.session.add(room)
            db.session.commit()
                        # 重新查询 Room 实例，确保它绑定到当前的会话
            room = Room.query.get(room.id)

        # 发送 PUT 请求
        response = self.client.put(f'/api/rooms/{room.id}', json={
            'name': 'Updated Room',
            'coefficient': 2.0
        })
        logger.debug(f"Response status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], 'Room updated')

    def test_delete_room(self):
        with self.app.app_context():
            # 添加测试数据
            room = Room(name='Test Room', coefficient=1.0, status=True)
            db.session.add(room)
            db.session.commit()
            room = Room.query.get(room.id)

        # 发送 DELETE 请求
        response = self.client.delete(f'/api/rooms/{room.id}')
        logger.debug(f"Response status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], 'Room marked as inactive')

    def test_add_members_to_room(self):
        with self.app.app_context():
            # 添加测试数据
            room = Room(name='Test Room', coefficient=1.0, status=True)
            member = Member(name='Test Member', phone='1234567890')
            db.session.add(room)
            db.session.add(member)
            db.session.commit()
            room = Room.query.get(room.id)
            member = Member.query.get(member.id)

        # 发送 POST 请求
        response = self.client.post(f'/api/rooms/{room.id}/members', json={
            'member_ids': [member.id],
            'start_timing': True
        })
        logger.debug(f"Response status code: {response.status_code}")
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data['message'], 'Members added to room')

    def test_remove_member_from_room(self):
        with self.app.app_context():
            # 添加测试数据
            room = Room(name='Test Room', coefficient=1.0, status=True)
            member = Member(name='Test Member', phone='1234567890')
            db.session.add(room)
            db.session.add(member)
            db.session.commit()
            stay = Stay(member_id=member.id, room_id=room.id, start_time=None)
            db.session.add(stay)
            db.session.commit()
            room = Room.query.get(room.id)
            member = Member.query.get(member.id)
            stay = Stay.query.get(stay.id)

        # 发送 DELETE 请求
        response = self.client.delete(f'/api/rooms/{room.id}/members/{member.id}')
        logger.debug(f"Response status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], 'Member removed from room')

    def test_get_room_members(self):
        with self.app.app_context():
            # 添加测试数据
            room = Room(name='Test Room', coefficient=1.0, status=True)
            member = Member(name='Test Member', phone='1234567890')
            stay = Stay(member_id=member.id, room_id=room.id, start_time=datetime.now(timezone.utc))
            db.session.add(room)
            db.session.add(member)
            db.session.add(stay)
            db.session.commit()
            room = Room.query.get(room.id)
            member = Member.query.get(member.id)
            stay = Stay.query.get(stay.id)

        # 发送 GET 请求
        response = self.client.get(f'/api/rooms/{room.id}/members')
        logger.debug(f"Response status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Member')

    def test_get_member_stay_in_room(self):
        with self.app.app_context():
            # 添加测试数据
            room = Room(name='Test Room', coefficient=1.0, status=True)
            member = Member(name='Test Member', phone='1234567890')
            stay = Stay(member_id=member.id, room_id=room.id, start_time=datetime.now(timezone.utc))
            db.session.add(room)
            db.session.add(member)
            db.session.add(stay)
            db.session.commit()

        # 发送 GET 请求
        response = self.client.get(f'/api/rooms/{room.id}/members/{member.id}/stay')
        logger.debug(f"Response status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['name'], 'Test Member')

if __name__ == '__main__':
    unittest.main()