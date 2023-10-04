ARE YOU USING WSL?
- check your WSL version using wsl --list --verbose (in Powershell)
- if using WSL2, then you cannot see COM ports (which Arduino uses)

https://learn.microsoft.com/en-us/windows/wsl/connect-usb

- check Kernel version
wsl --status

You require WSL2 5.10.60.1 kernel or higher
as ADMINISTRATOR, open Powershell and run wsl --update


Ensure Serial Monitor is not active, otherwise usbpid canno bind to it
- Just close the Serial Monitor


ttyACM0 for me, under dmesg


1. Install pyvenv in this directory
sudo apt install python3.8-venv

2. Run pyenv in this directory
python3 -m venv .

3. Activate pyvenv
source bin/activate

4. Install prereqs
pip install pyserial

import serial gives importError warning, but it's false

https://github.com/microsoft/WSL/issues/4322

You should see MPU6050 connection successful, and DMP enabled

Installing psutil
For Ubuntu, https://stackoverflow.com/questions/33303899/issue-on-import-psutil-inside-python-script
- i.e. sudo apt -get install python3-psutil

Check number of PHYSICAL CORES
print(psutil.cpu_count(logical=False))


usbipd wsl list
usbipd wsl attach --busid 2-2
usbipd wsl detach --busid 2-2