from app import create_app
from models.user import User

app = create_app()
with app.app_context():
    user = User.get_by_email("admin@admin.com")
    if user:
        User.reset_password(user.id, "senha123")
        print("Updated password of admin@admin.com to 'senha123'")
    else:
        print("User admin@admin.com not found!")
