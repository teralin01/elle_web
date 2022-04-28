import tornado.web
from MySqlQuery import MysqlQuery

class ORM(tornado.web.RequestHandler):
    def save(self, sql):
        self.application.db.insert(sql)
    def delete(self):
        pass
    def update(self):
        pass
    def all(self):
        pass