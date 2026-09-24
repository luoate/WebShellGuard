from datetime import datetime
import hashlib
import multiprocessing
import os
from flask import jsonify
import pymysql
import requests
import ssdeep
from util.config_db import conf_db
import tlsh
from magic import magic
from werkzeug.utils import secure_filename

from util.report import WebShellAnalyzer
host=conf_db.host
db_user=conf_db.db_user
db_password=conf_db.db_password
database=conf_db.database

def calculate_sha256_file_path(file_path):
    """计算文件的 SHA-256 哈希值"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        chunk = f.read(8192)  # 先读取一块
        while chunk:
            sha256.update(chunk)
            chunk = f.read(8192)  # 继续读取
    return sha256.hexdigest()

def calculate_sha256_file_obj(file_obj):
    """计算文件的 SHA-256 值"""
    sha256 = hashlib.sha256()
    for chunk in iter(lambda: file_obj.read(4096), b''):
        sha256.update(chunk)
    file_obj.seek(0)  # 重置游标
    return sha256.hexdigest()

def generate_report(file_path, file_info):
    analyzer = WebShellAnalyzer(file_path, file_info)
    report_text = analyzer.analyze()
    report_file = analyzer.save_report(report_text)

class Upload:
    @staticmethod
    def upload_file(request, detector):
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'})

        file = request.files['file']
        # print(file)
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'})
        elif file.filename == 'blob':
            time_format = "%Y/%m/%d %H:%M:%S"
            # 解析成datetime对象
            dt = datetime.strptime(request.form.get('time'), time_format)
            # 转成时间戳（秒级）
            timestamp = str(int(dt.timestamp()*1000))
            file.filename = timestamp + '.php'
        temp_file_path  = os.path.join('./upload/', file.filename)
        # 保存文件
        file.save(temp_file_path)
        file_hash = calculate_sha256_file_path(temp_file_path)
        # 使用哈希值作为新的文件名
        file_path = os.path.join('./upload/', file_hash)
        md5_hash = None
        sha1_hash = None
        try:        
            os.rename(temp_file_path, file_path)
        except:
            # 删除文件
            os.remove(temp_file_path)
        md5_hash = hashlib.md5()
        sha1_hash = hashlib.sha1()
        with open(file_path, 'rb') as f:
            content_byte = f.read()
            # content = content_byte.decode('utf-8', errors='ignore')
            md5_hash.update(content_byte)
            sha1_hash.update(content_byte)
            # print(content)
        md5_hash = md5_hash.hexdigest()
        sha1_hash = sha1_hash.hexdigest()
        try:
            file_type = magic.Magic().from_file(file_path)
        except:
            file_type = 'None'
        tlst_hash = tlsh.hash(content_byte)
        ssdeep_hash = ssdeep.hash(content_byte)
        file_size = os.path.getsize(file_path)
        # 获取文件的创建时间和修改时间
        creation_time = os.path.getctime(file_path)
        modification_time = os.path.getmtime(file_path)
        # 将时间戳转换为可读格式
        creation_time = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
        modification_time = datetime.fromtimestamp(modification_time).strftime('%Y-%m-%d %H:%M:%S')
        # print(creation_time, modification_time)
        # 发送POST请求
        response = requests.post('http://localhost:9090/api/parser', data=content_byte)
        # print(f"Response Content: {response.text}")
        # detector = WebshellDetector()

        # 将记录存储到数据库中
        db = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database
        )
        cursor = db.cursor()
        # 先检查是否在黑白名单中
        try:
            # 执行查询
            sql = "SELECT is_webshell FROM black_white_list WHERE sha256 = %s"
            cursor.execute(sql, (file_hash,))
            result = cursor.fetchone()

            if result:
                tag = result[0]
                # print('在名单中',tag)
                # return jsonify({'exists': True, 'is_webshell': is_webshell})
            else:
                # return jsonify({'exists': False})
                is_webshell, probability = detector.predict(json_str=response.text)
                tag = 1 if is_webshell else 0

        finally:
            cursor.close()
            db.close()


        # is_webshell, probability = detector.predict(json_str=response.text)
        # tag = 1 if is_webshell else 0
        # print(file.filename + '检测结果 '+ str(tag) + " 概率："+str(probability)+"%")
        # print(request.form.get('username'))
        # print(request.form.get('time'))
        # print(file_type)

       
        db = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database
        )
        cursor = db.cursor()
        try:
            cursor.execute('INSERT INTO upload (filename, sha256, sha1, md5, tlst, ssdeep, file_type, file_size , time, username, is_webshell) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);',
                    (file.filename, file_hash, sha1_hash, md5_hash,tlst_hash, ssdeep_hash, file_type, file_size, request.form.get('time'), request.form.get('username'), tag))
            db.commit()
            # print("插入成功")
        except Exception as e:
            db.rollback()
            return jsonify({'success': False, 'message': '插入失败'})
        # 关闭数据库连接
        cursor.close()
        db.close()
        file_info = {"文件名": file.filename,
                    "SHA-256": file_hash,
                    "SHA-1": sha1_hash,
                    "MD5": md5_hash,
                    "TLST": tlst_hash,
                    "SSDEEP": ssdeep_hash,
                    "文件类型": file_type,
                    "文件大小(Byte)": file_size,
                    "检测时间": request.form.get('time'),
                    "文件创建时间": creation_time,
                    "文件修改时间": modification_time,
                    }

        if tag == 1:
            # 创建生成报告进程
            process = multiprocessing.Process(target=generate_report, args=(file_path,file_info))
            # 启动进程
            process.start()

        # print(re)
        return jsonify({
        "success": True,
        "data": [
            {"hash": file_hash, "tag": '恶意' if tag == 1 else '安全'}
        ]})

    @staticmethod
    def upload_avatar(request):
        username = request.form.get('username')  # 获取用户名
        if not username:
            return jsonify({'success': False, 'message': '缺少用户名'})

        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'})
        
        file = request.files['file']
        original_filename = secure_filename(file.filename)
        ext = os.path.splitext(original_filename)[1]  # 获取后缀名，比如 '.png'
        ext = ext if ext else '.jpg'
        # print(ext)
        # print("4444",file.filename)

        # 暂存路径
        temp_file_path = os.path.join('./avatars/', original_filename)
        file.save(temp_file_path)

        # 计算 hash
        file_hash = calculate_sha256_file_path(temp_file_path)

        # 构造新的文件路径（带原始后缀）
        new_filename = file_hash + ext
        new_file_path = os.path.join('./avatars/', new_filename)

        try:
            os.rename(temp_file_path, new_file_path)
        except:
            os.remove(temp_file_path)

        
        # 将记录存储到数据库中
        db = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database
        )
        cursor = db.cursor()

        try:
            cursor.execute('UPDATE users SET avatar = %s WHERE username = %s;', (new_filename, username))
            db.commit()
            # print("插入成功")
        except Exception as e:
            db.rollback()
            # print("插入失败:", e)
            return jsonify({'success': False, 'message': '插入失败'})
        # 关闭数据库连接
        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "data": [
                {"hash": file_hash, "filename": new_filename}
            ]
        })

    @staticmethod
    def get_history(request):
        try:
            # 连接数据库
            connection = pymysql.connect(
                host=host,
                user=db_user,
                password=db_password,
                database=database
            )
            cursor = connection.cursor()

            # 获取查询参数
            username = request.args.get('user')
            page = int(request.args.get('page', 1))  # 默认第 1 页
            page_size = int(request.args.get('pageSize', 10))  # 默认每页 10 条

            # 计算偏移量
            offset = (page - 1) * page_size

            # 执行分页查询
            query = 'SELECT filename, sha256, sha1, md5, tlst, ssdeep, file_type, file_size, time, username, is_webshell, id FROM upload WHERE username = %s ORDER BY time DESC LIMIT %s OFFSET %s;'
            cursor.execute(query, (username, page_size, offset)) 
            results = cursor.fetchall()  # 获取查询结果

            # 计算总数（用于前端分页）
            count_query = 'SELECT COUNT(*) FROM upload WHERE username = %s;'
            cursor.execute(count_query, (username,))
            total_count = cursor.fetchone()[0]  # 获取总记录数
            webshell_count_query = 'SELECT COUNT(*) FROM upload WHERE username = %s AND is_webshell = 1;'
            cursor.execute(webshell_count_query, (username,))
            webshell_count = cursor.fetchone()[0]
            # print(webshell_count)
            normal_count = total_count - webshell_count

            # 关闭数据库连接
            cursor.close()
            connection.close()

            report_content = None
            # 处理文件内容
            modified_results = []
            for item in results:
                filename, hash_value, sha1_hash, md5_hash, tlst_hash, ssdeep_hash, file_type, file_size, time, user, tag, id = item
                file_path = './upload/' + hash_value  # 假设 hash 作为文件名
                content = None
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as file:
                        content_byte = file.read()
                        content = content_byte.decode('utf-8', errors='ignore')
                report_path = "./report/{}_report.md".format(hash_value)
                # if tag == 1:
                if os.path.exists(report_path):
                    with open(report_path, 'r', encoding='utf-8') as f:
                        report_content = f.read()
                # print(report_content)
                tag = '恶意' if tag == 1 else '安全'
                modified_results.append([filename, hash_value, time, user, tag, content, file_type, tlst_hash, ssdeep_hash, md5_hash, sha1_hash, str(file_size), report_content, id])

            # **调整返回结构，匹配前端代码**
            return jsonify({
                'list': modified_results,
                'total': total_count,
                'webshell': webshell_count,
                'normal': normal_count
            })

        except Exception as e:
            print(str(e))
            return jsonify({'error': str(e)}), 500

    @staticmethod
    def feedback(request):
        try:
            upload_id = request.args.get("uploadID")
            time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 将记录存储到数据库中
            db = pymysql.connect(
                host=host,
                user=db_user,
                password=db_password,
                database=database
            )
            cursor = db.cursor()
            try:
                cursor.execute('INSERT INTO feedback (upload_id, time) VALUES (%s, %s);',
                        (upload_id, time_now))
                db.commit()
                # print("插入成功")
            except Exception as e:
                db.rollback()
                print("插入失败:", e)
            # 关闭数据库连接
            cursor.close()
            db.close()

            # print(re)
            return jsonify({"success": True})
        except Exception as e:
            print(str(e))
            return jsonify({'error': str(e)}), 500

    @staticmethod
    def feedback_history(request):
        try:
            # 连接数据库
            connection = pymysql.connect(
                host=host,
                user=db_user,
                password=db_password,
                database=database
            )
            cursor = connection.cursor()

            # 获取查询参数
            page = int(request.args.get('page', 1))  # 默认第 1 页
            page_size = int(request.args.get('pageSize', 10))  # 默认每页 10 条

            # 计算偏移量
            offset = (page - 1) * page_size

            # 执行分页查询
            query = '''SELECT upload.*, feedback.time AS feedback_time
                        FROM feedback
                        INNER JOIN upload ON feedback.upload_id = upload.id
                        ORDER BY feedback_time DESC LIMIT %s OFFSET %s;'''
            cursor.execute(query, ( page_size, offset))
            results = cursor.fetchall()  # 获取查询结果

            # 计算总数（用于前端分页）
            count_query = 'SELECT COUNT(*) FROM feedback;'
            cursor.execute(count_query)
            total_count = cursor.fetchone()[0]  # 获取总记录数


            # 关闭数据库连接
            cursor.close()
            connection.close()

            report_content = None
            # 处理文件内容
            modified_results = []
            for item in results:
                id, filename, hash_value, sha1_hash, md5_hash, tlst_hash, ssdeep_hash, file_type, file_size, time, user, tag, feedback_time = item
                file_path = './upload/' + hash_value  # 假设 hash 作为文件名
                content = None
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as file:
                        content_byte = file.read()
                        content = content_byte.decode('utf-8', errors='ignore')
                report_path = "./report/{}.md".format(hash_value)
                # if tag == 1:
                if os.path.exists(report_path):
                    with open(report_path, 'r', encoding='utf-8') as f:
                        report_content = f.read()
                # print(report_content)
                tag = '恶意' if tag == 1 else '安全'
                modified_results.append([filename, hash_value, time, user, tag, content, file_type, tlst_hash, ssdeep_hash, md5_hash, sha1_hash, str(file_size), report_content, id, feedback_time])

            # **调整返回结构，匹配前端代码**
            return jsonify({
                'list': modified_results,
                'total': total_count
            })

        except Exception as e:
            print(str(e))
            return jsonify({'error': str(e)}), 500

    @staticmethod
    def add_list(request):
        # 获取表单字段
        type = request.form.get('type')
        username = request.form.get('user')
        
        # 获取文件对象
        uploaded_file = request.files.get('file')
        # print(type, username, uploaded_file)

        if uploaded_file:
            filename = uploaded_file.filename
            file_size = len(uploaded_file.read())  # 获取大小，单位：字节
            uploaded_file.seek(0)  # 重要：重置游标，否则之后读取为空
            # 计算 SHA-256
            file_hash = calculate_sha256_file_obj(uploaded_file)
            
            # 可选：读取文件内容
            # content = uploaded_file.read().decode('utf-8')  # 如果是文本文件
            
            # 连接数据库并插入信息
            connection = pymysql.connect(
                host=host,
                user=db_user,
                password=db_password,
                database=database
            )
            is_webshell = 1 if type == 'black' else 0
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # print(current_time)
            try:
                with connection.cursor() as cursor:
                    sql = """
                        INSERT INTO black_white_list (filename, sha256, username, file_size, is_webshell, time)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (filename, file_hash, username, file_size, is_webshell, current_time))
                    connection.commit()
            finally:
                connection.close()
            
            return jsonify({'message': '新增条目成功'}), 200
        else:
            return jsonify({'error': '未上传文件'}), 400
        
    @staticmethod
    def get_list_info(request):
        # 获取查询参数
        # list_type = request.args.get('type')
        search = request.args.get('search')
        # print(search)
        page = int(request.args.get('page', 1))  # 默认为第一页
        page_size = int(request.args.get('pageSize', 10))  # 默认为每页10条
        
        # 连接数据库
        connection = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database
        )
        
        try:
            with connection.cursor() as cursor:
                # 查询过滤条件
                where_conditions = []
                # if list_type:
                #     where_conditions.append(f"is_webshell = {1 if list_type == 'black' else 0}")
                if search:
                    where_conditions.append(f"(filename LIKE %s OR sha256 LIKE %s)")
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1"
                
                # 获取总条数
                count_sql = f"SELECT COUNT(*) FROM black_white_list WHERE {where_clause}"
                params = (
                    '%' + search + '%',  # 对应 filename LIKE
                    # '%' + search + '%',  # 对应 username LIKE
                    '%' + search + '%',  # 对应 sha256 LIKE
                ) if search else ()

                # 执行查询
                cursor.execute(count_sql, params)
                total = cursor.fetchone()[0]
                
                # 获取当前页数据
                data_sql = f"""
                    SELECT id, filename, sha256, file_size, is_webshell, username, time
                    FROM black_white_list
                    WHERE {where_clause}
                    LIMIT %s OFFSET %s
                """
                cursor.execute(data_sql, 
                            ('%' + search + '%', '%' + search + '%', page_size, (page - 1) * page_size) if search else (page_size, (page - 1) * page_size))
                rows = cursor.fetchall()

               

                # 处理结果并返回
                result = [{
                    'id': row[0],
                    'fileName': row[1],
                    'hash': row[2],
                    'fileSize': row[3],
                    'type': 'black' if row[4] == 1 else 'white',
                    'user': row[5],
                    'createTime': row[6]
                } for row in rows]
                print(result)
                return jsonify({
                    'list': result,
                    'total': total
                }), 200

        finally:
            connection.close()

    @staticmethod
    def delete_list_entry(request):
        # 获取前端发送的 ID 参数（通常为 JSON 格式）
        data = request.get_json()
        entry_id = data.get('id')

        if not entry_id:
            return jsonify({'error': '缺少 ID 参数'}), 400

        # 连接数据库
        connection = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database
        )

        try:
            with connection.cursor() as cursor:
                # 执行删除操作
                sql = "DELETE FROM black_white_list WHERE id = %s"
                rows_affected = cursor.execute(sql, (entry_id,))
                connection.commit()

                if rows_affected == 0:
                    return jsonify({'error': '未找到对应的记录'}), 404
                else:
                    return jsonify({'message': '删除成功'}), 200

        finally:
            connection.close()

    @staticmethod
    def update_list_entry(request):
        entry_id = request.args.get('id')  # 从 URL 中取 id
        file_name = request.form.get('fileName')
        sha256_hash = request.form.get('hash')
        file_size = request.form.get('fileSize')
        is_webshell = request.form.get('type')  # type 对应 is_webshell 字段
        is_webshell = 1 if is_webshell == 'black' else 0

        if not entry_id:
            return jsonify({'error': 'Missing id parameter'}), 400
        
        conn = None
        cursor = None
        try:
            conn = pymysql.connect(
                host=host,
                user=db_user,
                password=db_password,
                database=database
            )

            cursor = conn.cursor()

            sql = """
                UPDATE black_white_list
                SET filename=%s, sha256=%s, file_size=%s, is_webshell=%s
                WHERE id=%s
            """
            cursor.execute(sql, (file_name, sha256_hash, file_size, is_webshell, entry_id))
            conn.commit()

            return jsonify({'success': True, 'message': 'Entry updated successfully'})

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

        finally:
            cursor.close()
            conn.close()
