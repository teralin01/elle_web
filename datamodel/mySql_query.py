import pymysql
import logging

class MysqlQuery():
    def __init__(self,host,user,passwd,db_name):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.db_name = db_name
    def connect(self):
        self.database = pymysql.connect(self.host,self.user,self.passwd,self.db_name)
        self.cursor = self.database.cursor()
    def close(self):
        self.cursor.close()
        self.database.close()
    def get_one(self,sql):
        res = None
        try:
            self.connect()
            self.cursor.execute(sql)
            res = self.cursor.fetchone()
            self.close()
        except:
            logging.debug("query database fail")        

    def get_all(self,sql):
        res = ()
        try:
            self.connect()
            self.cursor.execute(sql)
            res = self.cursor.fetchall()
            self.close()
        except:
            print("query fail")
        return res

    def get_all_obj(self,sql, *args):
        resList = []
        fieldsList = []
        if(len(args) > 0 ):
            for item in args:
                fieldsList.append(item)
        else:
            fieldsSql = ""
            fields = self.get_all(fieldsSql)
            for item in fields:
                fieldsList.append(item[0])
        res = self.get_all(sql)
        for item in res:
            obj = {}
            count = 0
            for x in item:
                obj[fieldsList[count]] = x
                count += 1
            resList.append(obj)        
        return resList

    def insert(self,sql):
        return self.__edit(sql)
    def update(self,sql):
        return self.__edit(sql)
    def delete(self,sql):
        return self.__edit(sql)
    def __edit(self,sql):
        count = 0 
        try:
            self.connect()
            count = self.cursor.execute(sql)
            self.database.commit()
            self.close()
        except:
            print("sql query fail")
            self.database.rollback()
        return count
