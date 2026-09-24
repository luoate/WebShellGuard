class ConfigDB:
    def __init__(self):
        self.host = '127.0.0.1'
        self.db_user = 'root'  # 用户名
        self.db_password = 'root'  # 密码
        self.database = 'flask'  # 数据库名
conf_db = ConfigDB()