from flask import jsonify
import pymysql
from util.config_db import conf_db

host=conf_db.host
db_user=conf_db.db_user
db_password=conf_db.db_password
database=conf_db.database


class Account:
    @staticmethod
    def get_account_mine(request):
        username = request.args.get('username')  # 从URL参数中获取用户名
        if not username:
            return jsonify({'success': False, 'message': '缺少用户名'}), 400
        
        # print(host)

        # 数据库连接
        db = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database
        )
        try:
            cursor = db.cursor(pymysql.cursors.DictCursor)  # 返回字典格式
            cursor.execute("SELECT username, role, phone, email, avatar, description FROM users WHERE username=%s;", (username,))
            user = cursor.fetchone()

            if not user:
                return jsonify({'success': False, 'message': '用户不存在'}), 404
            
            # print(user)
            
            # usname, role, phone, email, avatar = user
            roles = ['', '管理员', '训练员', '普通用户']
            role = roles[user['role']]

            return jsonify({
                'success': True,
                'data': {
                    'username': user['username'],
                    'role': role,
                    'avatar': user['avatar'],
                    'email': user['email'],
                    'phone': user['phone'],
                    'description': user['description']
                }
            })
        finally:
            cursor.close()
            db.close()

    @staticmethod
    def update_user_info(request):
        data = request.get_json()
        username = data.get('username')

        if not username:
            return jsonify({'success': False, 'message': '缺少用户名'})

        # 可选字段
        avatar = data.get('avatar')
        email = data.get('email')
        phone = data.get('phone')
        description = data.get('description')

        db = pymysql.connect(host=host, user=db_user, password=db_password, database=database)
        try:
            cursor = db.cursor()
            sql = """
            UPDATE users 
            SET avatar=%s, email=%s, phone=%s, description=%s 
            WHERE username=%s
            """
            cursor.execute(sql, (avatar, email, phone, description, username))
            db.commit()

            return jsonify({'success': True})
        finally:
            cursor.close()
            db.close()
