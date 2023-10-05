# How to do AI data collection

## Steps
1. Ensure you have the pre-requisites installed to run `collect.py`. See _Pre-requisites to run collect.py_ section.

2. Find out the Serial Port (i.e `/dev/tty<something>`) that you will be connecting your Beetle to.
    1. Relatively easy for Linux based OS (you can use `dmesg`). No guide provided.
    2. _Might_ be easy for Windows 11 running WSL2 (according to Microsoft). No guide provided.
    2. Total clusterfuck for Windows 10 running WSL2 (according to me). Guide provided under _Windows 10 and WSL2 guide_. **Follow the steps in that guide first before continuing**.
    
3. Edit the `SERIAL_PORT` variable in `collect.py` appropriately.
    
4. **ONLY APPLICABLE FOR WINDOWS 10 RUNNING WSL2 USERS**  
  It's already mentioned under _Windows 10 running WSL2 guide_, but just putting here incase you forgot.
    1. Launch a WSL command line (Ubuntu for me) **and keep it open**.
    2. Open `Powershell` **in administrator mode**.
    3. Connect the Beetle to your laptop using micro-usb cable.
    4. Ensure that Uno IDE's Serial Monitor is **not** open (i.e Uno must not be communicating through the port).
    5. Type `usbipd wsl attach --busid <busid>` in `Powershell`, where `busid` corresponds to USB device you just attached (i.e the cable from Beetle to your laptop).
    6. You can run `usbipd wsl list` in `Powershell` and observe the output to check if it succeeded.
        1. You should see _Attached-WSL_ under `STATE` for the `BUSID` you just inputted.
    7. Or you can just listen for the disconnection sound that your laptop plays when you disconnect something.
    
5. **ONLY APPLICABLE FOR LINUX USERS**  
    1. Connect the Beetle to your laptop using micro-usb cable.

**I'm not sure if Windows 11 users will have problems ensuring the Beetle and `collect.py` can communicate through Serial. Hopefully it works just like Linux (just Plug n Play)**
    
6. Run `collect.py` with the appropriate command-line arguments and permissions.
    1. `sudo python3 collect.py -n damien -a fist` means you want to collect data for _fist_ actions, and file it under `data_dumps/fist/damien`.
    2. You need `sudo` access so that `collect.py` can read your `\dev\tty` port.
  
7. Observe the output of `collect.py`. It **must** say the following **two** lines below.  
  If you don't see it, it means that the Beetle failed to connect to the MPU (it happens sometimes). You can do `Ctrl-C` to stop `collect.py`, and reattempt step 6 again **until it succeeds**.
    1. _MPU6050 connection successful_
    2. _>****......>......DMP enabled..._

8. You are now ready for data collection. Do the move 'x' amount of times.
    1. Recommended for 'x' to be ~50. Above that, fatigue sets in and the reading might not be accurate. Post-processing takes longer too.
    
9. Once you are done collecting data, `Ctrl-C` to stop `collect.py`. You should observe the following output in-order...
    1. _Ctrl-C pressed, stopping AI data collection_
    2. _Stopped serial communication with Arduino_
    3. _Post-processing data, please wait..._
    4. _Done post-processing_
    
10. See _Data Format guide_ section for more information on how the data is formatted.

11. I suppose you want to disconnect the Beetle from your laptop now.
    1. **ONLY APPLICABLE FOR WINDOWS 10 RUNNING WSL2 USERS**  
  In `Powershell`, run `usbipd wsl detach --busid <busid>` to disconnect WSL from the your `dev\tty` port.
  Alternatively, you can just unplug the cable connecting the Beetle to your laptop.
    2. **ONLY APPLICABLE FOR LINUX USERS**  
      Just unplug the cable from the Beetle to your laptop. Or maybe there is a more Linux-ey way to disconnect?


## Windows 10 running WSL2 guide
### Background
* Serial devices are not mounted properly if you are running WSL2 on Windows 10. So you can't directly see the Serial Port you are using for the Beetle.
  * https://github.com/microsoft/WSL/issues/4322
* Online chatter said that reverting to WSL1 allows you to see the Serial Port, but I couldn't get it to work.
* So we will be using `usbipd-win` project as a workaround.

### My WSL2 specs
* Windows 10 
* Ubuntu 20.04.3 LTS
* Linux kernel version 5.15.90.1

### Guide
* You can follow https://learn.microsoft.com/en-us/windows/wsl/connect-usb, under _Install the USBIPD-WIN project_.
**Just ensure that your Linux kernel version is 5.10.60.1 or later (like what they say)**.
  * To upgrade your kernel version, open `Powershell` **as administrator** and run `wsl --update`.
  * For reference, Serial port on Uno IDE said `COM4` which was `/dev/ttyACM0` for me (I observed it using `dmesg`). Alot of online guides said that `COM4` should be `/dev/ttyS4`, which wasn't true for me.


## Pre-requisites to run collect.py
* pyserial
* psutil

1. You can use `venv` to install pre-reqs and run `collect.py`, that's what I did.
    1. Note that my WSL2 was running Ubuntu. In that case, even after running `pip install psutil` my Python3 couldn't import `psutil` successfully. You can try using apt instead, `sudo apt -get install python3-psutil`. Ya it kinda defeats the point of using `venv` to localize any damage, but couldn't find a workaround.
    
2. Or you can just rawdog it and install the pre-reqs globally.

## Data format guide
### Navigating to the data dump
If I ran `sudo python3 collect.py -n damien -a fist`, then the data dump is at `data_dumps/fist/damien`.
 
### What is arduino_dump.txt
* `arduino_dump.txt` is the raw `Serial.prints()` from the Beetle, dumped into a .txt file.  

* Every line has the sensor readings in CSV format \<AccX\>,\<AccY\>,\<AccZ\>,\<GyroX\>,\<GyroY\>,\<GyroZ\>
  
* The only processing done is to add an `E` character to demarcate where each sample window ends, and where the next sample window starts. The last few readings usually do not form a full sample window (unless you just so happen to terminate `collect.py` at the right time), and that's fine. 

* Post-processing will ensure that the before-mentioned 'window-less' values do not get sent for AI training, and the `E` character does not get sent too.

An example is given below (for sampling window size == 32)
```
110,25,81,-4763,438,3988
107,44,77,-5381,-615,3246
98,67,65,-5128,-1379,1229
84,89,45,-3940,-1544,-998
10,118,-74,2272,2038,-137
35,70,124,-3538,1284,784
39,90,101,-3381,870,517
34,109,71,-2957,-208,156
20,81,124,-4104,634,641
17,102,98,-4148,-196,119
-19,-106,-84,2482,1309,406
-7,-123,-97,3975,2628,741
10,110,-93,4852,3423,937
-46,120,-44,-308,-1361,-365
-55,120,-82,910,-534,-191
-56,111,-111,2115,819,-57
-50,95,-128,3217,2080,180
-36,75,-127,4055,3054,412
-20,-115,-94,1229,399,198
-18,-127,-123,2380,1471,605
-10,114,120,3403,2399,668
2,97,126,4315,3036,498
1,92,-120,-5618,-649,699
-10,125,89,-5083,-1944,-186
-67,-85,-88,-891,-992,-176
-71,-94,125,889,820,432
-61,-113,100,2697,2876,753
-41,116,94,4305,4558,713
-15,86,108,5581,5503,404
63,-37,-126,793,-2986,-1146
-25,92,96,-5282,-2959,-344
-49,120,41,-4550,-3260,-816
E
-85,-102,-69,-1605,-961,-517
-89,-103,-111,346,882,-153
-80,-115,119,2199,2883,-52
-62,121,111,3768,4423,-155
-38,94,119,5110,5262,-463
63,46,-109,-3218,4444,725
82,57,-96,-3373,4411,314
93,71,-98,-3398,3769,-29
96,85,-114,-3297,2833,-115
93,97,117,-2939,2072,12
91,104,87,-2451,1965,310
93,107,60,-1818,2566,609
103,106,39,-1135,3525,731
117,104,21,-442,4193,552
-124,104,6,190,4234,161
-112,105,-10,925,3555,-270
-105,105,-29,1673,2536,-535
-101,101,-48,2302,1809,-511
-96,91,-58,2774,1583,-255
-88,76,-52,3070,1607,141
-96,-4,111,2955,-8986,1304
108,-21,-126,1962,-12734,42
-68,-32,118,-1814,-10332,-4530
-101,-17,94,-1905,-5992,-4613
69,19,-115,-3600,4836,-811
87,31,-102,-3257,4686,-1193
101,49,-101,-2811,4205,-1193
112,68,-109,-2397,3499,-1024
120,86,-123,-2194,2855,-582
127,101,115,-2184,2524,-109
-121,115,95,-2171,2592,351
-112,126,75,-1976,2582,646
E
-103,-122,50,-1366,2121,697
-98,-119,20,-415,1230,504
-97,-121,-13,858,315,181
-100,126,-48,2183,10,32
```
  
  
  
### What is Acc\<something\>.txt or Gyro\<something\>.txt
* `Acc\<something\>.txt` or `Gyro\<something\>.txt` is the post-processed values of `arduino_dump.txt`

* Every line contains the sensor readings (for **one** corresponding sampling window) in the format \<sample_1_reading\> , <sample_2_reading\> , ... , <SAMPLE_WINDOW_SIZE_reading\>.

An example (for AccX) is given below  
  (note that it corresponds with the example given under _What is arduino_dump.txt_)
```
110,107,98,84,10,35,39,34,20,17,-19,-7,10,-46,-55,-56,-50,-36,-20,-18,-10,2,1,-10,-67,-71,-61,-41,-15,63,-25,-49
-85,-89,-80,-62,-38,63,82,93,96,93,91,93,103,117,-124,-112,-105,-101,-96,-88,-96,108,-68,-101,69,87,101,112,120,127,-121,-112
```
