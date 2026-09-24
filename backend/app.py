from flask_cors import CORS
from flask import Flask, jsonify, make_response, request, send_from_directory
import pymysql

from WebshellDetector import WebshellDetector

from router.account import Account
from router.auth import Auth
from router.dataset import Dataset
from router.model import Model
from router.train import Train
from router.upload import Upload
from router.user import User
from util.config_db import conf_db


app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return 'Hello Flask!!!'


@app.route('/axios')
def msg():
    return '需要传递给前端的数据'


# auth
@app.route('/login', methods={'POST'})
def login():
    return Auth.login(request)
@app.route('/register', methods={'POST'})
def register():
    return Auth.register(request)

# account
@app.route('/account/mine', methods=['GET'])
def get_account_mine():
    return Account.get_account_mine(request)
@app.route('/account/update', methods=['POST'])
def update_user_info():
    return Account.update_user_info(request)
@app.route('/avatar/<filename>')
def get_avatar(filename):
    avatar_folder = 'avatars'  # 头像文件夹路径
    return send_from_directory(avatar_folder, filename)

# upload
@app.route('/upload', methods=['POST'])
def upload_file():
    return Upload.upload_file(request, detector)
@app.route('/upload/avatar', methods=['POST'])
def upload_avatar():
    return Upload.upload_avatar(request)
@app.route('/history', methods=['GET'])
def get_history():
    return Upload.get_history(request)
@app.route('/feedback', methods=['GET'])
def feedback():
    return Upload.feedback(request)
@app.route('/feedback/history', methods=['GET'])
def feedback_history():
    return Upload.feedback_history(request)
@app.route('/list/add', methods=['POST'])
def add_list():
    return Upload.add_list(request)
@app.route('/list/info', methods=['GET'])
def get_list_info():
    return Upload.get_list_info(request)
@app.route('/list/delete', methods=['POST'])
def delete_list_entry():
    return Upload.delete_list_entry(request)
@app.route('/list/update', methods=['POST'])
def update_list_entry():
    return Upload.update_list_entry(request)

# train
@app.route('/train', methods=['POST'])
def train():
    return Train.train(request)
@app.route("/train/stop", methods=["POST"])
def stop_training():
    return Train.stop_training(request)
@app.route('/train/save', methods=['POST'])
def save_model():
    return Train.save_model(request)
@app.route('/train/history', methods=['GET'])
def get_train_history():
    return Train.get_train_history(request)

# dataset
@app.route('/dataset/delete', methods=['POST'])
def delete_dataset():
    return Dataset.delete_dataset(request)
@app.route('/dataset/create', methods=['POST'])
def create_dataset():
    return Dataset.create_dataset(request)
@app.route('/dataset/getName', methods=['GET'])
def get_dataset_name():
    return Dataset.get_dataset_name(request)
@app.route('/dataset/upload', methods=['POST'])
def upload_sample():
    return Dataset.upload_sample(request)
@app.route('/dataset/download', methods=['GET'])
def download_dataset():
    return Dataset.download_dataset(request)

# model
@app.route('/model/download', methods=['GET'])
def download_model():
    return Model.download_model(request)
@app.route('/model/delete', methods=['GET'])
def delete_model():
    return Model.delete_model(request)
@app.route('/model/update', methods=['GET'])
def update_model():
    return Model.update_model(request)
@app.route('/model/getName', methods=['GET'])
def get_model_name():
    return Model.get_model_name()
@app.route('/model/evaluate', methods=['POST'])
def model_evaluate():
    return Model.model_evaluate(request)
@app.route('/model/evaluate/history', methods=['GET'])
def model_evaluate_history():
    return Model.model_evaluate_history(request)
@app.route('/model/evaluate/delete', methods=['GET'])
def delete_evaluate():
    return Model.delete_model(request)
@app.route('/model/deploy', methods=['GET'])
def model_depoly():
    return Model.model_depoly(request, detector)

# user
@app.route('/user/info', methods=['GET'])
def get_user_info():
    return User.get_user_info(request)
@app.route('/user/add', methods=['POST'])
def add_user():
    return User.add_user(request)
@app.route('/user/update', methods=['POST'])
def update_user():
    return User.update_user(request)
@app.route('/user/delete', methods=['POST'])
def delete_user():
    return User.delete_user(request)

if __name__ == "__main__":
    # local_path = "./codebert"
    # tokenizer = RobertaTokenizer.from_pretrained("./codebert")
    # codebert_model = RobertaModel.from_pretrained(local_path)
    # print("成功从本地加载codebert模型！")
    detector = WebshellDetector()
    # app.run(debug=True, port=11451, use_reloader=False)
    app.run(debug=True, port=11451)