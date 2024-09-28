from flask import Blueprint, render_template, request, redirect, url_for, flash,session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from .models import User
from . import db
index_bp = Blueprint('index', __name__)
@index_bp.route('/index')
def index():
    return render_template('index.html')



