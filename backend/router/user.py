from datetime import datetime
from flask import jsonify
import pymysql
import torch
from util.config_db import conf_db

host=conf_db.host
db_user=conf_db.db_user
db_password=conf_db.db_password
database=conf_db.database
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class User:
    @staticmethod
    def get_user_info(request):
        search_username = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 10))
        offset = (page - 1) * page_size

        # 连接数据库
        conn = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database
        )

        try:
            with conn.cursor() as cursor:
                if search_username:
                    # 模糊搜索总数
                    count_sql = "SELECT COUNT(*) FROM users WHERE username LIKE %s"
                    cursor.execute(count_sql, ('%' + search_username + '%',))
                    total = cursor.fetchone()[0]

                    # 模糊搜索分页结果
                    sql = """
                        SELECT id, username, role, status, phone, create_time, email
                        FROM users
                        WHERE username LIKE %s
                        ORDER BY status ASC
                        LIMIT %s OFFSET %s
                    """
                    cursor.execute(sql, ('%' + search_username + '%', page_size, offset))
                else:
                    # 无搜索条件时查询所有
                    cursor.execute("SELECT COUNT(*) FROM users")
                    total = cursor.fetchone()[0]

                    sql = """
                        SELECT id, username, role, status, phone, create_time, email
                        FROM users
                        ORDER BY status ASC
                        LIMIT %s OFFSET %s
                    """
                    cursor.execute(sql, (page_size, offset))

                result = cursor.fetchall()

            return jsonify({
                "list": result,
                "total": total
            })
        except Exception as e:
            print(e)
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    @staticmethod
    def add_user(request):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        status = data.get('status')
        phone = data.get('phone')
        email = data.get('email')

        if not all([username, password, role, phone]):
            return jsonify({'error': '参数不完整'}), 400

        conn = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database
        )
        
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO users (username, password, role, status, phone, create_time, email)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    username,
                    password,
                    role,
                    status,
                    phone,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    email
                ))
            conn.commit()
            return jsonify({'message': '添加成功'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()

    @staticmethod
    def update_user(request):
        user_id = request.args.get('id')
        data = request.get_json()

        username = data.get('username')
        role = data.get('role')
        status = data.get('status')
        phone = data.get('phone')
        email = data.get('email')

        if not user_id or not all([username, role, phone]):
            return jsonify({'error': '参数不完整'}), 400

        conn = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database
        )

        try:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE users
                    SET username=%s, role=%s, status=%s, phone=%s, email=%s
                    WHERE id=%s
                """
                cursor.execute(sql, (username, role, status, phone, email, user_id))
            conn.commit()
            return jsonify({'message': '更新成功'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()

    @staticmethod
    def delete_user(request):
        data = request.get_json()
        user_id = data.get('id')

        if not user_id:
            return jsonify({'error': '缺少用户ID'}), 400

        conn = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database
        )

        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM users WHERE id = %s"
                cursor.execute(sql, (user_id,))
            conn.commit()
            return jsonify({'message': '删除成功'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()

