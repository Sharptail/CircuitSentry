from constants import *
import clr, utils

class HardwareMonitor:
    def __init__(self, window):
        self.window = window
        
        Hardware = self.import_libre_hm()
        self.handle = Hardware.Computer()
        self.handle.IsCpuEnabled  = True
        self.handle.IsGpuEnabled  = True
        self.handle.IsMemoryEnabled  = True
        self.handle.IsMotherboardEnabled  = True
        self.handle.MainboardEnabled = True
        self.handle.IsControllerEnabled  = True
        self.handle.IsNetworkEnabled   = True
        self.handle.IsStorageEnabled   = True
        self.handle.Open()

    def import_libre_hm(self):
        clr.AddReference(utils.get_file(LHM_FILENAME))
        from LibreHardwareMonitor  import Hardware
        return Hardware


    def init_libre_hm(self, window):
        # disable updating when window is being dragged to prevent window jumping around
        if not window.is_dragging:
            for i in self.handle.Hardware:
                i.Update()
                for sensor in i.Sensors:
                    if str(i.HardwareType) == "Motherboard":
                        print(sensor.Name, ": ", sensor.Value)
                    if sensor.Value is not None:
                        if str(sensor.SensorType) == 'Temperature':
                            if str(sensor.Name) == "Core (Tctl/Tdie)" or str(sensor.Name) == "CPU Package":
                                window.cpu_temp_label.config(text="CPU\n%d°" % sensor.Value)
                            if  str(sensor.Name) == "GPU Core":
                                window.gpu_temp_label.config(text="GPU\n%d°" % sensor.Value)
                        if str(sensor.SensorType) == "Load":
                            if str(sensor.Name) == "CPU Total":
                                window.cpu_usage_label.config(text="CPU\n%d%%" % sensor.Value)
                            if str(sensor.Name) == "GPU Core":
                                window.gpu_usage_label.config(text="GPU\n%d%%" % sensor.Value)
        
        window.after(1000, lambda : self.init_libre_hm(window))