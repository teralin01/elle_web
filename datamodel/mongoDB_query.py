import pymongo
import config

class MongoDB():
    """docstring for myclass."""
    def __init__(self,mydb_name):
        self.myclient = pymongo.MongoClient("mongodb://"+config.settings['db_admin_username']+":"+config.settings['db_admin_password']+"@localhost:27017/db_name?authSource=admin")
        #設mydb繼承myclient[mydb_Name]的屬性。
        self.mydb = self.myclient[mydb_name]
        #你的collection名稱

    def create_log_collection(self,collection, maxsize,maxnum):
        collist = self.mydb.list_collection_names()
        if collection not in collist:
            mycol = self.mydb.create_collection(collection, { "capped" : True, "size" : maxsize, max : maxnum } ) # size in bytes
        
    def insert_data(self, collection, data): #新增功能
        self.mycol = self.mydb[collection]
        self.mydata = data
        return self.mycol.insert_one(self.mydata)   #單筆插入資料指令

    def get_single_data(self, collection, myquery):  #獲得資料
        self.mycol = self.mydb[collection]
        self.myquery = myquery  #要搜尋的資料 空白全部搜尋，填值搜尋特定值。

        self.myfind = self.mycol.find_one(myquery)
        return self.myfind
    
    def get_data(self, collection, myquery = {}, noquery={"_id": 0}):  #獲得資料
        self.mycol = self.mydb[collection]
        self.myquery = myquery  #要搜尋的資料 空白全部搜尋，填值搜尋特定值。
        self.noquery = noquery  #要排除的資料
        self.myfind = self.mycol.find(myquery)
        # if self.myfind.retrieved == 0:
        #     return None
        # else:
        self.xx = list(self.myfind)
        return self.xx

    def delete_data(self, collection, mydelete):  
        self.mycol = self.mydb[collection]
        self.mydelete = mydelete
        return self.mycol.delete_one(self.mydelete)

    def update_one(self, collection, myquery, new_values):  
        self.mycol = self.mydb[collection]
        self.myquery = myquery
        self.new_values = new_values
        return self.mycol.update_one(self.myquery, self.new_values, upsert=False)
        
    def upsert(self, collection, myquery, new_values):  
        self.mycol = self.mydb[collection]
        self.myquery = myquery
        self.new_values = new_values
        return self.mycol.find_one_and_update(self.myquery, self.new_values, upsert=True)       
 