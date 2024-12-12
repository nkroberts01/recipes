class DatabaseConfig:
    HOST = 'localhost'
    DATABASE = 'recipes'
    USER = 'nkroberts'
    PASSWORD = 's7j23lhyv6s'
    PORT = '5432'

    @classmethod
    def get_connection_string(cls):
        return f"postgresql://{cls.USER}:{cls.PASSWORD}@{cls.HOST}:{cls.PORT}/{cls.DATABASE}"