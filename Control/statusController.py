from tornado.web import RequestHandler
import json
import psutil


class HWInfoHandler (RequestHandler):
    def get(self,*args,**kwargs):
        memStatus =  psutil.virtual_memory() 
        cpuPersent = psutil.cpu_percent()
        cpuTemperature = psutil.sensors_temperatures()['coretemp'][0][1]
        Info = { "memTotal":memStatus.total,"memUsed":memStatus.used,"CPU_Persent":cpuPersent,"CPU_Temp":cpuTemperature }
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'GET')
        self.set_header('Access-Control-Allow-Headers','*')
        self.write( json.dumps(Info))


# class AmrInfo:
#     @staticmethod
#     def GetGpuInfo():
#         gpulist = []
#         # GPUtil.showUtilization()
 
#         # 获取多个GPU的信息，存在列表里
#         Gpus = GPUtil.getGPUs()
        
#         for gpu in Gpus:
#             # print('gpu.id:', gpu.id)
#             # print('GPU总量：', gpu.memoryTotal)
#             # print('GPU使用量：', gpu.memoryUsed)
#             # print('gpu使用占比:', gpu.memoryUtil * 100)
#             # 按GPU逐个添加信息
 
#             gpu_memoryTotal = round((gpu.memoryTotal) /1024)
#             gpu.memoryUsed = round((gpu.memoryUsed) /1024,2)
#             gpu_memoryUtil = round((gpu.memoryUtil) * 100 ,2)
#             gpulist.append([gpu.id, gpu_memoryTotal, gpu.memoryUsed, gpu_memoryUtil]) #GPU序号，GPU总量，GPU使用量，gpu使用占比
#         #print("GPU信息(G):GPU序号,GPU总量,GPU使用量,gpu使用占比")
#         return gpulist
 
 
#     @staticmethod
#     def GetCpuInfo():
#         cpu_count = psutil.cpu_count(logical=False)  #1代表单核CPU，2代表双核CPU
#         xc_count = psutil.cpu_count()                #线程数，如双核四线程
#         cpu_slv = round((psutil.cpu_percent(1)), 2)  # cpu使用率
#         list = [cpu_count,xc_count,cpu_slv] # 核数，线程数，cpu使用率
#         #print("CPU信息(G)：核数，线程数,CPU使用率")
#         return list
 
 
#     # 获取内存信息
#     @staticmethod
#     def GetMemoryInfo():
#         memory = psutil.virtual_memory()
#         total_nc = round((float(memory.total) / 1024 / 1024 / 1024), 2)  # 总内存
#         used_nc = round((float(memory.used) / 1024 / 1024 / 1024), 2)  # 已用内存
#         free_nc = round((float(memory.free) / 1024 / 1024 / 1024), 2)  # 空闲内存
#         syl_nc = round((float(memory.used) / float(memory.total) * 100), 2)  # 内存使用率
 
#         ret_list = [total_nc, used_nc, free_nc, syl_nc] # 总内存， 已用内存 ，空闲内存 ，内存使用率
#         #print("内存信息(G)：总内存，已用内存，空闲内存，内存使用率")
#         return ret_list
 
 
#     # 获取硬盘信息
#     @staticmethod
#     def GetDiskInfo():
#         list = psutil.disk_partitions()  # 磁盘列表
#         ilen = len(list)  # 磁盘分区个数
#         i = 0
#         retlist1 = []
#         retlist2 = []
#         while i < ilen:
#             diskinfo = psutil.disk_usage(list[i].device)
#             total_disk = round((float(diskinfo.total) / 1024 / 1024 / 1024), 2)  # 总大小
#             used_disk = round((float(diskinfo.used) / 1024 / 1024 / 1024), 2)  # 已用大小
#             free_disk = round((float(diskinfo.free) / 1024 / 1024 / 1024), 2)  # 剩余大小
#             syl_disk = diskinfo.percent # 占用率
 
#             retlist1 = [i, list[i].device, total_disk, used_disk, free_disk, syl_disk]  # 序号，磁盘名称，总大小， 已用大小，剩余大小，占用率
#             retlist2.append(retlist1)
#             i = i + 1
#         print("硬盘信息(G)：序号，磁盘名称，总大，已用大小，剩余大小，占用率")
#         return retlist2
 
#     @staticmethod
#     def GetCPUTmpInfo():
#         retlist3 = psutil.sensors_temperatures()
#         print("CPU温度:",retlist3)
#         return retlist3
     