import os


class ConfigDB:
    def __init__(self):
        # 值与 docker-compose.yml 里 backend 服务的 environment 对应
        self.host = os.getenv('DB_HOST', '127.0.0.1')
        self.db_user = os.getenv('DB_USER', 'root')
        self.db_password = os.getenv('DB_PASSWORD', 'root')
        self.database = os.getenv('DB_NAME', 'flask')


conf_db = ConfigDB()
