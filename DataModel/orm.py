import tornado.web
from mongoDBQuery import MongoDB

dbinstance = MongoDB("elle")
account = "admin"
query = {"username": account}
#ret = dbinstance.get_single_data("account",query)
ret = dbinstance.get_single_data("account",query)
#ret = dbinstance.get_data("account",{})

print (ret)



# class ORM(tornado.web.RequestHandler):
#     def save(self, sql):
#         self.application.db.insert(sql)
#     def delete(self):
#         pass
#     def update(self):
#         pass
#     def all(self):
#         pass