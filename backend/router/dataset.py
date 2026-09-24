import json
import os
import shutil
from flask import jsonify, send_file
import pandas
import pymysql
import requests
import torch
from util.config_db import conf_db

host=conf_db.host
db_user=conf_db.db_user
db_password=conf_db.db_password
database=conf_db.database
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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

class Dataset:
    @staticmethod
    def delete_dataset(request):
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

    @staticmethod
    def create_dataset(request):
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
                'INSERT INTO dataset (name, white_num, black_num, username) VALUES (%s, %s, %s, %s);', (name, '0', '0', username))
            db.commit()
            # pass
        else:
            shutil.copy(f'phpProcessor/dataset/{base_dataset}.csv', f'phpProcessor/dataset/{name}.csv')

            cursor = db.cursor()
            cursor.execute(
                'INSERT INTO dataset (name, white_num, black_num, username) VALUES (%s, %s, %s, %s);',(name, white_num, black_num, username))
            db.commit()
            # 关闭数据库连接
            cursor.close()
            db.close()
        return jsonify({"message": "success"}), 200

    @staticmethod
    def get_dataset_name(request):
        # print("2222222222222222222222222222222222222222223232",host)
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

    @staticmethod
    def upload_sample(request):
        # 接收 sampleType 参数
        sample_type = request.form.get('sampleType')
        dataset_name = request.form.get('dataset')
        username = request.form.get('username')
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'error': '没有文件上传'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
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
        # print("34343434343",black_num, white_num, dataset_name, username)
        update_query = 'UPDATE dataset SET white_num = %s, black_num = %s WHERE name = %s;'
        cursor.execute(update_query, (white_num, black_num, dataset_name))
        # print(f"受影响的行数: {cursor.rowcount}")
        connection.commit()

        # 关闭数据库连接
        cursor.close()
        connection.close()

        # 返回成功响应
        return jsonify({
            'success': True,
            # 'filePath': file_path
        }), 200

    @staticmethod
    def download_dataset(request):
        dataset_name = request.args.get('dataset')
        if not dataset_name:
            return jsonify({"error": "Missing dataset parameter"}), 400

        # 拼接文件路径
        file_path = os.path.join("phpProcessor/dataset", f"{dataset_name}.csv")

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

