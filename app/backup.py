from flask import Blueprint, render_template, request, redirect, url_for, flash,send_file
from flask_login import login_required
from .models import Product, Member,Room,Consumption
from datetime import datetime
from . import db
import math
import shutil
import os
backups_bp = Blueprint('backups', __name__)

@backups_bp.route('/backup', methods=['GET'])
@login_required
def backup():
    return render_template('backup.html')