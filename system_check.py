import sys
import time
import platform
import wx
import orpg.orpg_version

class system_check:

    def start(self,log_file='openrpg_sysinfo.txt'):
        self.log_file = open(log_file,'w')
        self.log_file.write("OpenRPG System Info " + time.strftime( '%m-%d-%y', time.localtime( time.time() ) ))
        self.check_openrpg()
        self.check_py()
        self.check_wxpython()
        self.check_platform()
        self.log_file.close()

    def check_wxpython(self):
        self.log_file.write("\nwxPython Version: " + wx.__version__)

    def check_py(self):
        self.log_file.write("\nPython: " + sys.version)

    def check_platform(self):
        self.log_file.write("\nPlatform: " + platform.platform())

    def check_openrpg(self):
        self.log_file.write("\nOpenRPG Version: " + orpg.orpg_version.VERSION)
        self.log_file.write("\nOpenRPG Build: " + orpg.orpg_version.BUILD)



if __name__ == "__main__":
    syscheck = system_check()
    syscheck.start()
