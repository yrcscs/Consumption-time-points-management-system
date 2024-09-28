from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from config import config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__,
                instance_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance'),
                static_folder=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static'),
                template_folder=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates')
                )
    
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'index.index'
    from .index import index_bp
    #from .login import login_bp
    from .members import members_bp
    from .dashboard import dashboard_bp
    from.backup import backups_bp
   


    from .api.admin import admin_bp
    from .api.member import member_bp
    from .api.product import product_bp
    from .api.room import room_bp
    from .api.consumption import consumption_bp  
    from .api.timer import timer_bp
    from .api.backup import backup_bp
 

    # view
    app.register_blueprint(index_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(backups_bp)

    # api
    app.register_blueprint(admin_bp,url_prefix='/api')
    app.register_blueprint(member_bp,url_prefix='/api')
    app.register_blueprint(product_bp, url_prefix='/api')
    app.register_blueprint(room_bp, url_prefix='/api')
    app.register_blueprint(consumption_bp, url_prefix='/api')
    app.register_blueprint(timer_bp, url_prefix='/api')
    app.register_blueprint(backup_bp, url_prefix='/api')


    @app.route('/')
    def index():
        return redirect(url_for('index.index'))
    

    with app.app_context():
        db.create_all()

    return app  # 修正缩进


@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))  # 添加返回值
