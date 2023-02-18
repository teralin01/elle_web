import pymysql

class MysqlQuery():
    def __init__(self,host,user,passwd,dbName):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.dbName = dbName
    def connect(self):
        self.db = pymysql.connect(self.host,self.user,self.passwd,self.dbName)
        self.cursor = self.db.cursor()
    def close(self):
        self.corsor.close()
        self.db.close() 
    def get_one(self,sql):
        res = None
        try:
            self.connect()
            self.cursor.execute(sql)
            res = self.corsor.fetchone()
            self.close()
        except:
            print("query database fail")        
            
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
            self.db.commit()
            self.close()
        except:
            print("sql query fail")
            self.db.rollback()
        return count
                
        
                    