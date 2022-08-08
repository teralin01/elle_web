import psutil

class HWInfoHandler ():
    def get():
        memStatus =  psutil.virtual_memory() 
        cpuPersent = psutil.cpu_percent()
        cpuTemperature = psutil.sensors_temperatures()['coretemp'][0][1]
        Info = { "memTotal":memStatus.total,"memUsed":memStatus.used,"CPU_Persent":cpuPersent,"CPU_Temp":cpuTemperature }
        return Info