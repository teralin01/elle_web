import psutil

class HWInfoHandler ():
    def get(self):
        mem_status =  psutil.virtual_memory()
        cpu_persentage = psutil.cpu_percent()
        cpu_temperature = psutil.sensors_temperatures()['coretemp'][0][1]
        info = { "memTotal":mem_status.total,"memUsed":mem_status.used,"CPU_Persent":cpu_persentage
                ,"CPU_Temp":cpu_temperature }
        return info
