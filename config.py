import os
class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Pain is inevitab1e & $uffering is optiona1'