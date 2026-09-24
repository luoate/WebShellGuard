from datetime import datetime
import os
import shutil
from urllib.parse import unquote
from flask import jsonify, send_file
import pymysql
import torch
from Trainer import Trainer
from model import BERTClassifier
from util.config_db import conf_db
from util.config import conf

host=conf_db.host
db_user=conf_db.db_user
db_password=conf_db.db_password
database=conf_db.database
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def model_evaluate_save_history(modelName, trainDatasetName, testDatasetName, accuracy, loss, inferenceSpeed, throughput, recall, precision, testTime, username, f1):
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
                recall, `precision_score`, f1, throughput, test_time
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
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
            f1,
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

class Model:
    @staticmethod
    def download_model(request):
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

    @staticmethod
    def delete_model(request):
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
        
    @staticmethod
    def update_model(request):
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

    @staticmethod
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

    @staticmethod
    def model_evaluate(request):
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
        acc, avg_loss, recall, precision, f1, throughput, inference_speed = trainer.validate()    
        timeNow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        model_evaluate_save_history(modelName, trainDatasetName, testDatasetName, acc, avg_loss, inference_speed, throughput, recall, precision, timeNow, username, f1)

        result = {
            "status": "success",
            "data": {
                "accuracy": acc,
                "loss": avg_loss,
                "recall": recall,
                "precision": precision,
                "f1": f1,
                "throughput": throughput,
                "inference_speed": inference_speed,
                "time": timeNow
            }
        }

        return jsonify(result), 200

    @staticmethod
    def model_evaluate_history(request):
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
                        f1,
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
        
    @staticmethod
    def delete_evaluate(request):
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

    @staticmethod
    def model_depoly(request, detector):
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

