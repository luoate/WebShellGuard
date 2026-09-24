import hashlib
import json
import os

import pymysql
from util.config_db import conf_db

host=conf_db.host
db_user=conf_db.db_user
db_password=conf_db.db_password
database=conf_db.database

class Auth:
    @staticmethod
    def login(request):
        db = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database
        )
        try:
            if request.data:
                res = request.data.decode('utf-8')
                data = json.loads(res)
                username = data['username']
                password = data['password']
                # 获取游标对象
                cursor = db.cursor()

                # 执行查询
                cursor.execute('SELECT username, role, status, avatar FROM users WHERE username=%s AND password=%s', (username, password))
                user = cursor.fetchone()

                return_message = {
                    'success': False,
                    'data': {
                        'avatar': "",
                        'username': '',
                        'nickname': "",
                        'roles': '',
                        'permissions': '',
                        'accessToken': "",
                        'refreshToken': "",
                        'expires': ""
                    }
                }

                roles = ['', 'admin', 'trainer', 'user']

                # 如果用户存在，则返回成功消息
                if user:
                    uname, role, status, avatar = user
                    role = roles[role]
                    # print(role)
                    if status == 0:
                        return return_message
                    # role = 'admin' if username == 'admin' else 'common'
                    return_message = {
                        'success': True,
                        'data': {
                            'avatar': f"http://localhost:11451/avatar/{avatar}",
                            'username': uname,
                            'nickname': uname,
                            'roles': [role],
                            'permissions': ["*:*:*"],
                            'accessToken': "eyJhbGciOiJIUzUxMiJ9.admin",
                            'refreshToken': "eyJhbGciOiJIUzUxMiJ9.adminRefresh",
                            'expires': "2030/10/30 00:00:00"
                        }
                    }
        finally:
            # 确保游标和数据库连接被关闭
            if cursor:
                cursor.close()
            if db:
                db.close()

        return return_message

    @staticmethod
    def register(request):
        db = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database
        )
        try:
            if request.data:
                res = request.data.decode('utf-8')
                data = json.loads(res)
                # print(data)
                username = data['username']
                password = data['password']
                # print(username, password)
                cursor = db.cursor()
                return_message = {
                    'success': False,
                    'data': {
                        'avatar': "",
                        'username': '',
                        'nickname': "",
                        'roles': '',
                        'permissions': '',
                        'accessToken': "",
                        'refreshToken': "",
                        'expires': ""
                    }
                }
                try:
                    cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s);', (username, password))
                    db.commit()
                    result = cursor.fetchone
                    # print(result)
                    if result:
                        # 注册下成功
                        # print('注册成功')
                        role = 'admin' if username == 'admin' else 'common'
                        # 登录成功
                        # return_message['success'] = True
                        return_message = {
                            'success': True,
                            'data': {
                                'avatar': "https://avatars.githubusercontent.com/u/44761321",
                                'username': username,
                                'nickname': "小铭",
                                'roles': [role],
                                'permissions': ["*:*:*"],
                                'accessToken': "eyJhbGciOiJIUzUxMiJ9.admin",
                                'refreshToken': "eyJhbGciOiJIUzUxMiJ9.adminRefresh",
                                'expires': "2030/10/30 00:00:00"
                            }
                        }
                    else:
                        print('注册失败11')
                except pymysql.IntegrityError as e:
                    print("ERROR: " + str(e))
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

        return return_message
    
