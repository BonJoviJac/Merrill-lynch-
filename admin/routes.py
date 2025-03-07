from flask import Blueprint

admin = Blueprint('admin', __name__)

@admin.route('/dashboard')
def dashboard():
    return "Admin Dashboard"
