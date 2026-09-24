from datetime import datetime
import os
import shutil
from flask import jsonify
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

class Train:
    @staticmethod
    def train(request):
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

    @staticmethod
    def stop_training():
        # 设置标志位，表示训练应中止
        with open('stop_flag.txt', "a") as f:
            f.write("STOP")
        return jsonify({"message": "中止请求已发送"})

    @staticmethod
    def save_model(request):
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
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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

    @staticmethod
    def get_train_history(request):
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

