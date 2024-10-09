
from flask import Blueprint, jsonify, request
from flask_login import login_required
from datetime import datetime
import os
import shutil
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
backup_bp = Blueprint('backup', __name__)



def backup_database(backup_dir, backup_type, max_backups=5):
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.sqlite'
        backup_path = os.path.join(backup_dir, backup_type, backup_filename)
        archive_dir = os.path.join(backup_dir, backup_type, 'archive')
        db_path = 'lib/app/instance/app.db'

        # 创建备份目录（如果不存在）
        os.makedirs(os.path.join(backup_dir, backup_type), exist_ok=True)
        os.makedirs(archive_dir, exist_ok=True)

        # 获取现有备份文件列表
        existing_backups = sorted(
            [f for f in os.listdir(os.path.join(backup_dir, backup_type)) if f.startswith('backup_') and f.endswith('.sqlite')],
            key=lambda x: os.path.getmtime(os.path.join(backup_dir, backup_type, x))
        )

        # 移动最旧的备份文件到归档文件夹以保持备份文件数量在 max_backups 以内
        while len(existing_backups) >= int(max_backups):
            oldest_backup = existing_backups.pop(0)
            shutil.move(os.path.join(backup_dir, backup_type, oldest_backup), os.path.join(archive_dir, oldest_backup))
        
        # 复制数据库文件
        with open(db_path, 'rb') as db_file:
            with open(backup_path, 'wb') as backup_file:
                backup_file.write(db_file.read())
        
        return backup_filename
    except Exception as e:
        raise e

@backup_bp.route('/backup', methods=['POST'])
@login_required
def manual_backup():
    try:
        data = request.json
        drive = data.get('drive')
        custom_path = data.get('customPath')
        interval = data.get('interval') # 单位分钟
        backup_time = data.get('backupTime') # 定时备份时间，格式为 "HH:MM"
        max_interval_backups = data.get('maxIntervalBackups', 5) # 默认最大间隔备份数量为 5
        max_time_backups = data.get('maxTimeBackups', 5) # 默认最大定时备份数量为 5

        if not drive and not custom_path:
            return jsonify({'error': '未指定盘符或自定义路径'}), 400
        if not interval and not backup_time:
            return jsonify({'error': '未指定备份间隔或定时备份时间'}), 400

        # 设置备份路径
        if custom_path:
            # 检查路径的有效性
            if not os.path.exists(custom_path):
                drive_letter = os.path.splitdrive(custom_path)[0]
                if not os.path.exists(drive_letter):
                    return jsonify({'error': f'盘符 {drive_letter} 不存在'}), 400
                os.makedirs(custom_path, exist_ok=True)
            backup_dir = custom_path
        else:
            backup_dir = os.path.join(f'{drive}:\\Backups')

        # 设置自动备份任务
        scheduler.remove_all_jobs()

        if backup_time:
            # 设置定时备份任务
            hour, minute = map(int, backup_time.split(':'))
            scheduler.add_job(lambda: backup_database(backup_dir, 'time', max_time_backups), 'cron', hour=hour, minute=minute)
        if interval:
            # 设置间隔备份任务
            scheduler.add_job(lambda: backup_database(backup_dir, 'interval', max_interval_backups), 'interval', minutes=int(interval))

        if not scheduler.running:
            scheduler.start()

        # 立即进行一次备份
        if backup_time:
            backup_filename = backup_database(backup_dir, 'time', max_time_backups)
        else:
            backup_filename = backup_database(backup_dir, 'interval', max_interval_backups)

        return jsonify({'backup_filename': backup_filename}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/backups', methods=['GET'])
@login_required
def get_backups():
    try:
        drive = request.args.get('drive')
        if not drive:
            return jsonify({'error': '未指定盘符'}), 400

        backup_dir = os.path.join(f'{drive}:\\Backups')
        backups = []
        for backup_type in ['interval', 'time']:
            type_dir = os.path.join(backup_dir, backup_type)
            if os.path.exists(type_dir):
                backups.extend([
                    {
                        'filename': f,
                        'type': backup_type,
                        'path': os.path.join(type_dir, f)
                    }
                    for f in os.listdir(type_dir)
                    if f.startswith('backup_') and f.endswith('.sqlite')
                ])

        backups.sort(key=lambda x: os.path.getmtime(x['path']), reverse=True)
        return jsonify({'backups': backups}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

CONFIG_FILE = 'config.json'
import json

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, 'r') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)

@backup_bp.route('/get_backup_settings', methods=['GET'])
def get_backup_settings():
    config = load_config()
    return jsonify(config)

@backup_bp.route('/save_backup_settings', methods=['POST'])
def save_backup_settings():
    data = request.json
    config = load_config()

    backup_drive = data.get('backupDrive', config.get('backupDrive'))
    custom_path = data.get('customPath', config.get('customPath'))

    if backup_drive == 'custom' and custom_path:
        # 检查路径的合法性
        drive_letter = custom_path.split(':')[0]
        is_valid_path = re.match(r'^[a-zA-Z]:\\', custom_path) and re.match(r'^[a-zA-Z]$', drive_letter)
        if not is_valid_path:
            return jsonify({'error': '路径不合法，请检查格式'}), 400
        config['customPath'] = custom_path
        config['backupDrive'] = None  # 清除盘符设置
    else:
        config['backupDrive'] = backup_drive
        config['customPath'] = None  # 清除自定义路径设置

    config['backupInterval'] = data.get('backupInterval', config.get('backupInterval'))
    config['backupTime'] = data.get('backupTime', config.get('backupTime'))
    config['maxIntervalBackups'] = data.get('maxIntervalBackups', config.get('maxIntervalBackups'))
    config['maxTimeBackups'] = data.get('maxTimeBackups', config.get('maxTimeBackups'))

    save_config(config)

    return jsonify({'success': True})



@backup_bp.route('/restore', methods=['POST'])
@login_required
def restore_database():
    try:
        data = request.json
        drive = data.get('drive')
        filename = data.get('filename')
        if not drive:
            return jsonify({'error': '未指定盘符'}), 400
        if not filename:
            return jsonify({'error': '未指定备份文件'}), 400

        # 假设你使用的是 SQLite 数据库
        db_path = 'lib/app/instance/app.db'
        backup_dir = os.path.join(f'{drive}:\\Backups')  # 备份文件存储目录

        # 查找备份文件所在的子目录
        backup_path = None
        for backup_type in ['interval', 'time']:
            type_dir = os.path.join(backup_dir, backup_type)
            potential_path = os.path.join(type_dir, filename)
            if os.path.exists(potential_path):
                backup_path = potential_path
                break

        if not backup_path:
            return jsonify({'error': '备份文件未找到'}), 404

        # 将备份文件复制到数据库路径
        with open(backup_path, 'rb') as backup_file:
            with open(db_path, 'wb') as db_file:
                db_file.write(backup_file.read())

        # 获取备份文件的日期和时间
        try:
            backup_timestamp = filename.split('_')[1] + '_' + filename.split('_')[2].split('.')[0]
            backup_datetime = datetime.strptime(backup_timestamp, '%Y%m%d_%H%M%S')
        except ValueError as e:
            return jsonify({'error': f'Invalid backup file timestamp format: {filename}'}), 500

        return jsonify({'message': 'Database restored successfully', 'backup_datetime': backup_datetime.strftime('%Y-%m-%d %H:%M:%S')}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500