import hashlib
import multiprocessing
import os
import shutil
from datetime import datetime
from urllib.parse import unquote
from idlelib.iomenu import encoding

import pandas
import requests
import ssdeep
import tlsh
import torch
from click.core import batch
from flask import Flask, json, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
import pymysql
from magic import magic
from numpy.ma import shape
from torch.utils.data import DataLoader
from transformers import RobertaTokenizer, RobertaConfig, RobertaModel, AdamW

from Trainer import Trainer
from WebshellDetector import WebshellDetector
from openai import OpenAI
import dashscope
from dashscope import Generation

from model import BERTClassifier
from train_modify import load_pretrained_model
from util.config import conf
from util.datasets import PhpDataset
from util.report import WebShellAnalyzer
from werkzeug.utils import secure_filename

host = '127.0.0.1'
db_user = 'root'  # 用户名
db_password = 'root'  # 密码
database = 'flask'  # 数据库名

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return 'Hello Flask!!!'


@app.route('/axios')
def msg():
    return '需要传递给前端的数据'


@app.route('/login', methods={'POST'})
def login():
    # # 执行sql语句
    # curor.execute('select * from user')
    # # 获取数据
    # res = curor.fetchall()
    # #关闭数据库
    # db.close()
    # return str(res)
    # 创建数据库连接
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

@app.route('/register', methods={'POST'})
def register():
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

def calculate_sha256(file_path):
    """计算文件的 SHA-256 哈希值"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        chunk = f.read(8192)  # 先读取一块
        while chunk:
            sha256.update(chunk)
            chunk = f.read(8192)  # 继续读取
    return sha256.hexdigest()

@app.route('/account/mine', methods=['GET'])
def get_account_mine():
    username = request.args.get('username')  # 从URL参数中获取用户名
    if not username:
        return jsonify({'success': False, 'message': '缺少用户名'}), 400

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

@app.route('/account/update', methods=['POST'])
def update_user_info():
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


@app.route('/avatar/<filename>')
def get_avatar(filename):
    avatar_folder = 'avatars'  # 头像文件夹路径
    return send_from_directory(avatar_folder, filename)

@app.route('/upload', methods=['POST'])
def upload_file():

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
    file_hash = calculate_sha256(temp_file_path)
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
    is_webshell, probability = detector.predict(json_str=response.text)
    tag = 1 if is_webshell else 0
    print(file.filename + '检测结果 '+ str(tag) + " 概率："+str(probability)+"%")
    print(request.form.get('username'))
    print(request.form.get('time'))
    # print(file_type)

    # 将记录存储到数据库中
    db = pymysql.connect(
        host=host,
        user=db_user,
        password=db_password,
        database=database
    )
    cursor = db.cursor()
    # print(123)
    # cursor.execute('INSERT INTO upload (filename, sha256, sha1, md5, tlst, ssdeep, file_type, file_size , time, username, is_webshell) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);',
    #                (file.filename, file_hash, sha1_hash, md5_hash,tlst_hash, ssdeep_hash, file_type, file_size, request.form.get('time'), request.form.get('username'), tag))
    # cursor.fetchone()

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

    # file_info = {"filename": file.filename,
    #              "sha256": file_hash,
    #              "sha1": sha1_hash,
    #              "md5": md5_hash,
    #              "tlst": tlst_hash,
    #              "ssdeep": ssdeep_hash,
    #              "file_type": file_type,
    #              "file_size": file_size,
    #              "detect_time": request.form.get('time'),
    #              "create_time": creation_time,
    #              "modify_time": modification_time,
    #              }
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

@app.route('/upload/avatar', methods=['POST'])
def upload_avatar():
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
    file_hash = calculate_sha256(temp_file_path)

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


def generate_report(file_path, file_info):

    # with open("webshell分析报告模板.md", 'r', encoding='utf-8') as f:
    #     report_content = f.read()

    # deepseek
    # client = OpenAI(api_key="sk-808711db755549319969f761fb472443", base_url="https://api.deepseek.com")
    # # 调用api分析
    # response = client.chat.completions.create(
    #     model="deepseek-chat",
    #     messages=[
    #         {"role": "system", "content": "你需要分析提供的webshell文件，填写报告模板。文件信息如下：{}。模板内容如下：{}。".format(file_info, report_content)},
    #         {"role": "user", "content": file_content},
    #     ],
    #     stream=False
    # )
    # print(response.choices[0].message.content)
    # with open("./report/{}.md".format(file_info["filename"]), 'a', encoding='utf-8') as f:
    #     f.write(response.choices[0].message.content)

    # qw
    # dashscope.api_key = "sk-db49a68955a54095af3b11ced9d3fe25"
    # response = Generation.call(
    #     model="qwen-plus",
    #     messages=[
    #             {"role": "system", "content": "你需要分析提供的webshell文件，填写报告模板。文件信息如下：{}。模板内容如下：{}。".format(file_info, report_content)},
    #             {"role": "user", "content": file_content},
    #         ]
    # )
    # # print(response.output.text)
    # with open("./report/{}.md".format(file_info["sha256"]), 'w', encoding='utf-8') as f:
    #     f.write(response.output.text)
    analyzer = WebShellAnalyzer(file_path, file_info)
    report_text = analyzer.analyze()
    report_file = analyzer.save_report(report_text)
    pass

@app.route('/history', methods=['GET'])
def get_history():
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

@app.route('/feedback', methods=['GET'])
def feedback():
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
        # cursor.execute('INSERT INTO feedback (upload_id, time) VALUES (%s, %s);',
        #             (upload_id, time_now))
        # cursor.fetchone()
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

@app.route('/feedback/history', methods=['GET'])
def feedback_history():
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

@app.route('/train', methods=['POST'])
def train():
    # 接收前端传来的数据
    data = request.get_json()

    # 提取 epoch 和 modelParams
    epoch = data.get("epoch")
    model_params = data.get("modelParams")
    optimizer_params = model_params.get("optimizer")
    dataset_name = model_params.get("datasetName")
    model_name = model_params.get("modelName")  # 获取模型名称
    
    # 检查模型名称是否重复
    try:
        connection = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # 查询数据库中是否已存在相同模型名称
            sql = "SELECT COUNT(*) as count FROM model_train WHERE model_name = %s"
            cursor.execute(sql, (model_name,))
            result = cursor.fetchone()
            
            if result['count'] > 0:
                return jsonify({
                    "status": "Error",
                    "message": "Model name already exists in database"
                }), 400
                
    except Exception as e:
        return jsonify({
            "status": "Error",
            "message": f"Database error: {str(e)}"
        }), 500
    finally:
        if connection:
            connection.close()

    # 使用传来的 modelParams 更新配置
    conf.set(
        seq_len=model_params.get("seqLen", conf.seq_len),
        batch_size=model_params.get("batchSize", conf.batch_size),
        num_batch=model_params.get("batchNum", conf.num_batch),
        lr=model_params.get("learningRate", conf.lr),
        # weight_decay=model_params.get("weightDecay", conf.weight_decay),
        num_epochs=model_params.get("epochs", conf.num_epochs)
    )

    # 加载数据集
    train_dataset_path = f"phpProcessor/dataset/{dataset_name}.csv"
    # test_dataset_path = "phpProcessor/files/sequence/test/test.csv"
    # train_dataset = PhpDataset(train_dataset_path)
    # test_dataset = PhpDataset(test_dataset_path)

    # train_loader = DataLoader(train_dataset, batch_size=conf.batch_size, shuffle=True, num_workers=4, pin_memory=True)
    # test_loader = DataLoader(test_dataset, batch_size=conf.batch_size, shuffle=False, num_workers=4, pin_memory=True)

    
    # 初始化模型
    model = BERTClassifier().to(device)

    # 预训练权重
    pretrain_path = "model/pre_train0_no_fc.pth"
    if os.path.exists(pretrain_path):
        model.load_state_dict(torch.load(pretrain_path, map_location=device))
        print(f"Loaded pretrained weights from {pretrain_path}")

    # 优化器 & 调度器
    if optimizer_params == 'adam':
        optimizer = torch.optim.Adam(model.parameters(), lr=conf.lr, betas=(0.9, 0.999))
    elif optimizer_params == 'sgd':
        optimizer = torch.optim.SGD(model.parameters(), lr=conf.lr, momentum=0.9)
    elif optimizer_params == 'rmsprop':
        optimizer = torch.optim.RMSprop(model.parameters(), lr=conf.lr, alpha=0.99)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", patience=2)

    # 训练管理器
    trainer = Trainer(model=model,train_dataset_path= train_dataset_path, optimizer=optimizer, scheduler=scheduler)

    # 加载已有训练进度
    checkpoint_path = f"./model/tmp/checkpoint_epoch_{epoch-1}.pth"
    trainer.load_checkpoint(checkpoint_path)

    # 训练 1 轮
    acc, loss = trainer.train_one_epoch()

    if not acc:
        return jsonify({
            "status": "Training stopped."
        })

    print('acc:', acc, 'loss:', loss)

    # 返回当前训练状态
    return jsonify({
        "status": "Training completed for this epoch.",
        "epoch": trainer.epoch,
        "acc": acc,
        "loss": loss
    })

@app.route("/train/stop", methods=["POST"])
def stop_training():
    # 设置标志位，表示训练应中止
    with open('stop_flag.txt', "a") as f:
        f.write("STOP")
    return jsonify({"message": "中止请求已发送"})

@app.route('/train/save', methods=['POST'])
def save_model():
    # 获取参数
    data = request.get_json()
    username = data.get('username')
    model_params = data.get('modelParams')
    selected_epoch = data.get('selectedEpoch')
    accuracy = data.get('accuracy')
    loss = data.get('loss')
    training_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 保存模型
    model = BERTClassifier().to(device)
    checkpoint_path = f"./model/tmp/checkpoint_epoch_{selected_epoch}.pth"
    save_path = f"./model/train/{model_params.get('modelName')}.pth"
    if os.path.exists(checkpoint_path):
        checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    torch.save(model.state_dict(), save_path)
    print('模型保存成功!')
    shutil.rmtree('./model/tmp')  # 删除目录及其所有内容
    os.makedirs('./model/tmp')     # 重新创建空目录

    # 打印调试信息
    # print("Received modelParams:")
    # for key, value in model_params.items():
    #     print(f"  {key}: {value}")
    # print(f"Selected Epoch: {selected_epoch}")
    # print(f"Accuracy: {accuracy}")
    # print(f"Loss: {loss}")

    try:
        conn = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database
        )
        cursor = conn.cursor()

        sql = """
            INSERT INTO model_train (
                model_name, username, dataset_name, learning_rate, sequence_length,
                num_batches, batch_size, epochs, selected_epoch, optimizer,
                accuracy, loss, training_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (
            model_params.get('modelName'),
            username,
            model_params.get('datasetName'),
            model_params.get('learningRate'),
            model_params.get('sequenceLength'),
            model_params.get('numBatches'),
            model_params.get('batchSize'),
            model_params.get('epochs'),
            selected_epoch,
            model_params.get('optimizer'),
            accuracy,
            loss,
            training_time
        ))

        conn.commit()
        return jsonify({"message": "Model parameters saved to database successfully."})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to save model parameters."}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/train/history', methods=['GET'])
def get_train_history():
    username = request.args.get("username")
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
        # query = 'SELECT filename, sha256, sha1, md5, tlst, ssdeep, file_type, file_size, time, username, is_webshell FROM upload WHERE username = %s ORDER BY time DESC LIMIT %s OFFSET %s;'
        query = '''SELECT 
                    model_name, 
                    dataset_name, 
                    learning_rate, 
                    sequence_length,
                    num_batches, 
                    batch_size, 
                    epochs, 
                    selected_epoch, 
                    optimizer,
                    accuracy, 
                    loss, 
                    training_time
                FROM model_train WHERE username = %s
                ORDER BY training_time DESC LIMIT %s OFFSET %s;
                '''
        cursor.execute(query, (username, page_size, offset))
        results = cursor.fetchall()  # 获取查询结果

        # 计算总数（用于前端分页）
        count_query = 'SELECT COUNT(*) FROM model_train WHERE username = %s;'
        cursor.execute(count_query, (username, ))
        total_count = cursor.fetchone()[0]  # 获取总记录数

        # 关闭数据库连接
        cursor.close()
        connection.close()

        # **调整返回结构，匹配前端代码**
        return jsonify({
            'list': results,
            'total': total_count,
        })

    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/dataset/delete', methods=['POST'])
def delete_dataset():
    data = request.get_json()  # 获取前端发送的 JSON 数据
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    # 获取需要删除的数据集名称
    name = data.get("name")
    if not name:
        return jsonify({"error": "Dataset name is required"}), 400

    db = pymysql.connect(
        host=host,
        user=db_user,
        password=db_password,
        database=database
    )

    # 删除数据库中的相关数据
    cursor = db.cursor()
    cursor.execute('DELETE FROM dataset WHERE name = %s;', (name,))
    db.commit()

    # 删除文件系统中的数据集文件
    dataset_file = f'phpProcessor/dataset/{name}.csv'
    if os.path.exists(dataset_file):
        os.remove(dataset_file)
    
    cursor.close()
    db.close()

    return jsonify({"message": "Dataset deleted successfully"}), 200

@app.route('/dataset/create', methods=['POST'])
def create_dataset():
    data = request.get_json()  # 获取前端发送的 JSON 数据
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    # 解析数据
    username = data.get("user")
    name = data.get("name")
    dataset_type = data.get("type")
    base_dataset = data.get("baseDataset")
    black_num = data.get("blackNum")
    white_num = data.get("whiteNum")
    # print(black_num, white_num)


    # 检查数据库名称是否重复
    try:
        connection = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # 查询数据库中是否已存在相同数据库名称
            sql = "SELECT COUNT(*) as count FROM dataset WHERE name = %s"
            cursor.execute(sql, (name,))
            result = cursor.fetchone()
            
            if result['count'] > 0:
                # print(123)
                return jsonify({
                    "status": "Error",
                    "message": "Dataset name already exists in database"
                }), 400
                
    except Exception as e:
        return jsonify({
            "status": "Error",
            "message": f"Database error: {str(e)}"
        }), 500
    finally:
        if connection:
            connection.close()


    db = pymysql.connect(
        host=host,
        user=db_user,
        password=db_password,
        database=database
    )
    if base_dataset is None:
        # 空白数据集
        with open(f'phpProcessor/dataset/{name}.csv', 'a', encoding='utf-8') as f:
            f.write('tokenSequence,stringSequence,tags,label\n')
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO dataset (name, white_num, black_num) VALUES (%s, %s, %s);', (name, '0', '0'))
        db.commit()
        # cursor.fetchone()
        # pass
    else:
        shutil.copy(f'phpProcessor/dataset/{base_dataset}.csv', f'phpProcessor/dataset/{name}.csv')

        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO dataset (name, white_num, black_num) VALUES (%s, %s, %s);',(name, white_num, black_num))
        db.commit()
        # cursor.fetchone()
        # 关闭数据库连接
        cursor.close()
        db.close()
    return jsonify({"message": "success"}), 200

@app.route('/dataset/getName', methods=['GET'])
def get_dataset_name():
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = connection.cursor()

        dataset_query = 'SELECT name, white_num, black_num FROM dataset;'
        cursor.execute(dataset_query)
        dataset = cursor.fetchall()

        # 关闭数据库连接
        cursor.close()
        connection.close()
        # **调整返回结构，匹配前端代码**
        # print(jsonify(dataset))
        return jsonify(dataset)

    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/dataset/upload', methods=['POST'])
def upload_sample():
    # 接收 sampleType 参数
    sample_type = request.form.get('sampleType')
    dataset_name = request.form.get('dataset')
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'error': '没有文件上传'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    # 保存文件
    # file_path = f'./uploads/{file.filename}'
    # file.save(file_path)
    # print({
    #     'message': '文件上传成功',
    #     'sampleType': sample_type,
    #     'filePath': file_path
    # })
    dataset_filepath = f'phpProcessor/dataset/{dataset_name}.csv'
    response = requests.post('http://localhost:9090/api/parser', data=file.read())
    # print(response.text)
    append_data_with_label(dataset_filepath, response.text, sample_type)

    # 连接数据库
    connection = pymysql.connect(
        host=host,
        user=db_user,
        password=db_password,
        database=database,
    )
    cursor = connection.cursor()
    black_num, white_num = count_labels(dataset_filepath)
    update_query = 'UPDATE dataset SET white_num = %s, black_num = %s WHERE name = %s;'
    cursor.execute(update_query, (white_num, black_num, dataset_name))
    connection.commit()

    # 关闭数据库连接
    cursor.close()
    connection.close()

    # 返回成功响应
    return jsonify({
        'success': True,
        # 'filePath': file_path
    }), 200

def append_data_with_label(csv_file, json_data, label):
    # 解析 JSON 字符串
    try:
        new_data = json.loads(json_data)
    except json.JSONDecodeError:
        print("无效的 JSON 数据")
        return

    # 将 JSON 数据转换为 DataFrame
    df_new = pandas.DataFrame([new_data])

    # 添加 label 列
    df_new['label'] = label

    # 追加数据，确保列头只在第一次写入时添加
    df_new.to_csv(csv_file, mode='a', header=False, index=False)
    print(f"数据追加成功，label='{label}'")

def count_labels(csv_file):
    # 读取 CSV 文件
    df = pandas.read_csv(csv_file)

    # 确保 'label' 列存在
    if 'label' not in df.columns:
        print("CSV 文件中没有 'label' 列")
        return

    # 统计 'webshell' 和 'normal' 的数量
    webshell_count = (df['label'] == 'webshell').sum()
    normal_count = (df['label'] == 'normal').sum()
    return webshell_count, normal_count

DATASET_DIR = "phpProcessor/dataset"
@app.route('/dataset/download', methods=['GET'])
def download_dataset():
    dataset_name = request.args.get('dataset')
    if not dataset_name:
        return jsonify({"error": "Missing dataset parameter"}), 400

    # 拼接文件路径
    file_path = os.path.join(DATASET_DIR, f"{dataset_name}.csv")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        return jsonify({"error": "Dataset not found"}), 404

    # 以文件下载形式返回
    return send_file(
        file_path,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"{dataset_name}.csv"
    )

@app.route('/model/download', methods=['GET'])
def download_model():
    modelName = request.args.get('modelName')
    if not modelName:
        return jsonify({"error": "Missing modelName parameter"}), 400

    filepath = f"./model/train/{modelName}.pth"

    if not os.path.exists(filepath):
        return jsonify({"error": "Model not found"}), 404

    return send_file(
        filepath,
        as_attachment=True,
        download_name=f"{modelName}.pth",
        mimetype='application/octet-stream'
    )

@app.route('/model/delete', methods=['GET'])
def delete_model():
    modelName = unquote(request.args.get('modelName'))
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = connection.cursor()

        # 执行删除操作
        delete_query = 'DELETE FROM model_train WHERE model_name = %s;'
        rows_affected = cursor.execute(delete_query, (modelName, ))

        connection.commit()  # 提交事务

        # 关闭数据库连接
        cursor.close()
        connection.close()

        mode_path = f"./model/train/{modelName}.pth"

        if os.path.exists(mode_path):
            os.remove(mode_path)
        else:
            print("模型文件不存在")

        # 返回删除结果
        return jsonify({
            'success': True,
            'deleted': rows_affected,
            'message': f'{rows_affected} record(s) deleted.'
        })

    except Exception as e:
        print(str(e))
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/model/update', methods=['GET'])
def update_model():
    modelName = unquote(request.args.get('modelName'))
    newModelName = unquote(request.args.get('newModelName'))
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = connection.cursor()

        # 执行更新操作
        query = 'UPDATE model_train SET model_name = %s WHERE model_name = %s;'
        rows_affected = cursor.execute(query, (newModelName, modelName))

        connection.commit()  # 提交事务

        # 关闭数据库连接
        cursor.close()
        connection.close()

        mode_path = f"./model/train/{modelName}.pth"
        new_mode_path = f"./model/train/{newModelName}.pth"

        if os.path.exists(mode_path):
            os.rename(mode_path, new_mode_path)
        else:
            print("模型文件不存在")

        # 返回更结果
        return jsonify({
            'success': True,
            'updated': rows_affected,
            'message': f'{rows_affected} record(s) updated.'
        })

    except Exception as e:
        print(str(e))
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/model/getName', methods=['GET'])
def get_model_name():
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = connection.cursor()

        dataset_query = '''SELECT model_name, dataset_name, learning_rate, 
                sequence_length, num_batches, batch_size, epochs, selected_epoch, 
                optimizer, training_time FROM model_train;'''
        cursor.execute(dataset_query)
        dataset = cursor.fetchall()

        # 关闭数据库连接
        cursor.close()
        connection.close()
        # **调整返回结构，匹配前端代码**
        # print(jsonify(dataset))
        return jsonify(dataset)

    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/model/evaluate', methods=['POST'])
def model_evaluate():
    # 获取参数
    model_name = request.args.get('model')
    dataset_name = request.args.get('dataset')
    
    data = request.get_json()
    modelName = data.get('modelName')
    username = data.get('username')
    trainDatasetName = data.get('trainDatasetName')
    testDatasetName = data.get('testDatasetName')
    
    # print(testDatasetName, dataset_name)

    # 数据库连接配置
    connection = pymysql.connect(
        host=host,
        user=db_user,
        password=db_password,
        database=database,
        cursorclass=pymysql.cursors.DictCursor  # 这样返回的是字典形式
    )
    try:
        with connection.cursor() as cursor:
            # 查询语句
            sql = """
            SELECT `id`, `model_name`, `dataset_name`, `learning_rate`, `sequence_length`, 
                `num_batches`, `batch_size`, `epochs`, `selected_epoch`, 
                `optimizer`, `accuracy`, `loss` 
            FROM `model_train` 
            WHERE `model_name` = %s AND username = %s
            LIMIT 1;
            """
            cursor.execute(sql, (model_name, username))
            result = cursor.fetchone()

            if result:
                # 将结果赋值给变量
                id = result['id']
                model_name = result['model_name']
                learning_rate = result['learning_rate']
                sequence_length = result['sequence_length']
                num_batches = result['num_batches']
                batch_size = result['batch_size']
                epochs = result['epochs']
                selected_epoch = result['selected_epoch']
                optimizer = result['optimizer']
                accuracy = result['accuracy']
                loss = result['loss']

                # print("读取成功：", result)
            else:
                print("未找到对应的模型记录。")
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed."}), 500            
    finally:
        connection.close()

    # 更新配置
    conf.set(
        seq_len=sequence_length,
        batch_size=batch_size,
        num_batch=num_batches,
        lr=learning_rate,
        num_epochs=epochs
    )

    # 模型测试
    test_dataset_path = f"phpProcessor/dataset/{dataset_name}.csv"
    model_path = f"model/train/{model_name}.pth"
    # model_path = f"model/train_loss0.0346_acc_0.9875.pth"
    
    model = BERTClassifier() # 初始化模型
    # 加载预训练权重
    # pretrain_pos_path = 'model/pre_train0.pth'
    # model = load_pretrained_model(
    #     model=model,
    #     checkpoint_path=pretrain_pos_path,
    #     exclude_layers=['fc']  # 排除全连接层
    # )
    model.load_state_dict(torch.load(model_path))


    # tokenizer = RobertaTokenizer.from_pretrained('./codebert')
    # detector = WebshellDetector(model_path=model_path)
    # detector.predict_from_csv(test_dataset_path)

    trainer = Trainer(model=model,test_dataset_path=test_dataset_path)
    print(model_path, test_dataset_path)
    acc, avg_loss, recall, precision, throughput, inference_speed = trainer.validate()    
    timeNow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    model_evaluate_save_history(modelName, trainDatasetName, testDatasetName, acc, avg_loss, inference_speed, throughput, recall, precision, timeNow, username)

    result = {
        "status": "success",
        "data": {
            "accuracy": acc,
            "loss": avg_loss,
            "recall": recall,
            "precision": precision,
            "throughput": throughput,
            "inference_speed": inference_speed,
            "time": timeNow
        }
    }

    return jsonify(result), 200

def model_evaluate_save_history(modelName, trainDatasetName, testDatasetName, accuracy, loss, inferenceSpeed, throughput, recall, precision, testTime, username):
    try:
        conn = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database
        )
        cursor = conn.cursor()

        sql = """
            INSERT INTO model_evaluate (
                model_name, train_dataset_name, test_dataset_name, username,
                accuracy, loss, inference_speed,
                recall, `precision_score`, throughput, test_time
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s
            )
            """
        cursor.execute(sql, (
            modelName,
            trainDatasetName,
            testDatasetName,
            username, 
            accuracy,
            loss,
            inferenceSpeed,
            recall,
            precision,
            throughput,
            testTime,
        ))

        conn.commit()
        # return jsonify({"message": "Successfully."})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed."}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/model/evaluate/history', methods=['GET'])
def model_evaluate_history():
    username = request.args.get("username")
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
        query = '''SELECT 
                    model_name,
                    train_dataset_name,
                    test_dataset_name,
                    accuracy,
                    loss,
                    inference_speed,
                    recall,
                    precision_score,
                    throughput,
                    test_time,
                    id
                FROM model_evaluate WHERE username = %s
                ORDER BY test_time DESC LIMIT %s OFFSET %s;;
                '''
        cursor.execute(query, (username, page_size, offset))
        results = cursor.fetchall()  # 获取查询结果
        # print(results)

        # 计算总数（用于前端分页）
        count_query = 'SELECT COUNT(*) FROM model_evaluate WHERE username = %s;'
        cursor.execute(count_query, (username, ))
        total_count = cursor.fetchone()[0]  # 获取总记录数

        # 关闭数据库连接
        cursor.close()
        connection.close()

        # **调整返回结构，匹配前端代码**
        return jsonify({
            'list': results,
            'total': total_count,
        })

    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 500
    
@app.route('/model/evaluate/delete', methods=['GET'])
def delete_evaluate():
    id = unquote(request.args.get('id'))
    # print('testTime',testTime)
    # print(unquote(testTime))
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = connection.cursor()

        # 执行删除操作
        delete_query = 'DELETE FROM model_evaluate WHERE id = %s;'
        rows_affected = cursor.execute(delete_query, (id, ))

        connection.commit()  # 提交事务

        # 关闭数据库连接
        cursor.close()
        connection.close()

        # 返回删除结果
        return jsonify({
            'success': True,
            'deleted': rows_affected,
            'message': f'{rows_affected} record(s) deleted.'
        })

    except Exception as e:
        print(str(e))
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/model/deploy', methods=['GET'])
def model_depoly():
    model = unquote(request.args.get('model'))
    try:
        detector.load_model(f'./model/train/{model}.pth')

        # 返回结果
        return jsonify({
            'success': True,
            'message': f'{model} is deployed.'
        })

    except Exception as e:
        print(str(e))
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/user/info', methods=['GET'])
def get_user_info():
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

@app.route('/user/add', methods=['POST'])
def add_user():
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

@app.route('/user/update', methods=['POST'])
def update_user():
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

@app.route('/user/delete', methods=['POST'])
def delete_user():
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


if __name__ == "__main__":
    # local_path = "./codebert"
    # tokenizer = RobertaTokenizer.from_pretrained("./codebert")
    # codebert_model = RobertaModel.from_pretrained(local_path)
    # print("成功从本地加载codebert模型！")
    detector = WebshellDetector()
    # app.run(debug=True, port=11451, use_reloader=False)
    app.run(debug=True, port=11451)