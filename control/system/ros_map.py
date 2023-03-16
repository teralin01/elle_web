import config

class RosMap:
    def __init__(self):
        pass
    def upload_map_layer(self,uploadpath,mapdata):
        print (uploadpath)
        if "keepout" not in uploadpath and "speed_filter" not in uploadpath:
            return {"result":False,"info":"file name is illegal"}

        fname = uploadpath+".png"
        outpath = config.settings['mappath']
        return_str = ""
        try:
            output_file = open( outpath + fname, 'wb')
        except IOError:
            print("open file error")
            return_str = {"result":False,"info":"open file error"}
        finally:
            try:
                output_file.write(mapdata['body'])
                output_file.close()
                return_str = {"result":True,"info": fname+" is uploaded"}
            except IOError:
                print("write file error")
                return_str = {"result":False,"info":"write file error"}

            finally:
                return return_str

    def upload_map_static(self,map_data):
        fname = map_data['filename']

        if "png" not in fname:
            return {"result":False,"info":"file extension is illegal"}        

        outpath = config.settings['mappath']

        try:
            output_file = open( outpath + fname, 'wb')
        except IOError:
            print("open file error")
            return {"result":False,"info":"open file error"}
        finally:
            try:
                output_file.write(map_data['body'])
                output_file.close()
            except IOError:
                print("write file error")
                return {"result":False,"info":"write file error"}

        return {"result":True,"info": fname+" is uploaded"}    