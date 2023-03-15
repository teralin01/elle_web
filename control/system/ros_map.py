import config

class RosMap:
    def __init__(self):
        pass
    def UploadMapLayer(uploadpath,mapdata):
        print (uploadpath)
        if "keepout" not in uploadpath and "speed_filter" not in uploadpath:
            return {"result":False,"info":"file name is illegal"}

        fname = uploadpath+".png"
        outpath = config.settings['mappath']

        try:
            output_file = open( outpath + fname, 'wb')
        except IOError:
            print("open file error")
            return {"result":False,"info":"open file error"}
        finally:    
            try:
                output_file.write(mapdata['body'])
                output_file.close()
            except IOError:
                print("write file error")
                return {"result":False,"info":"write file error"}
            
        return {"result":True,"info": fname+" is uploaded"}

    def UploadMapStatic(mapdata):
        fname = mapdata['filename']
        
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
                output_file.write(mapdata['body'])
                output_file.close()
            except IOError:
                print("write file error")
                return {"result":False,"info":"write file error"}
            
        return {"result":True,"info": fname+" is uploaded"}    