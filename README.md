# isadore_electonics

Design files for the electronics of the Isadore Dryer Management System. Also included is what is called the MID software which queries the electronics and reports it back to the [isadore_server](https://github.com/bluthen/isadore_server/)


# Electronics Manufacture

Electronics manufactures usually want gerbers, centroid file, and a bill of materials. The latest pre-generated versions of these files can usually be found in the out directory (Example: `sensor_unitv3/out/`).

* The centroid and gerbers are in the zip file.
* The bill of materials is in the excel spreadsheet file (xlsx)
* An optional pins.png file may exist to show the manufacturer the location of pin1 for ICs.

Optionally you can generate the gerbers and centroid yourself depending by opening it up in [Eagle](https://www.autodesk.com/products/eagle/overview).


# Electronics Firmware

After you have a sensor unit or sensor hub, you need to program their firmware. To do this you need a AVR ISP programmer. Then there are script to help you program them. `sensor_unitv3/code/make.py`, `sensor_hubv3/code/Makefile`, and `fuse_crystal_clock.sh`.

*Note* you need a 5 pin ISP programmer. Most sold are 10 pin, so an adapter is needed.

To program the units or hubs you need some software installed:

* `avrdude`
* `gcc-avr`
* `avr-libc`

## Sensor Unit
A sensor unit can be programmed in many ways depending on what sensor modules you are going to plug into it.

Here is the help usage for `make.py`

```
Usage: make.py [OPTIONS] ADDRESS
  -h, --help                      Show this screen
  -d, --debug                     Debug build
  -p, --program                   Program unit
  -c, --clean                     Clean
  -f, --fuse                      Set fuse
  --prev303                       Build for prev3.03 unit
  --with-th                       Build with temperature humidty
  --with-pressurev1=m,b           Build in v1 pressure module
  --with-pressurev4a=cal_adjust   Build in v4a pressure module
  --with-pressurev4b=cal_adjust   Build in v4b pressure module
  --with-pressurev5=m,b           Build in v5 pressure module
  --with-anemometer               Build in Anemometer module
  --with-thermo                   Build in thermocouple module
  --with-multit                   Build in Multipoint-temp module
  --with-tach                     Build in tachometer module
```

So for example you might do with a unit, with the programmed placed and the unit powered.
```
python2 make.py -f -c -p --with-pressurev4b=0 102
```

If successful It is now programmed to use the pressurev4 module that gives you pressure/temperature/rh, and responses when address `102` is queried.


## Sensor Hub

To program the hub you would run with the programmer in place and powered:
```
cd sensor_hubv3/code
./fuse_crystal_clock.sh && make program
```

# MID (Master Interface Device)

This is basically the combination of a small computer (raspberry pi) and the hub electronics board. The hub and raspberry pi communicate serially. The hub has voltage regulators to power the raspberry pi.

## HUB<-> pi wiring

![HUB Pi wiring diagram](https://github.com/bluthen/isadore_electronics/raw/master/pi_com_pwr.jpg)


Notice for the power, Red is on TP1, and black is outside of usb connector.

Communication headers on pins 4 and 5 from outside corner.

## Install and configure raspbian

After installing raspian you'll want to set to enable access to the serail port with `raspi-config` and [disable the use of console by uart](https://www.raspberrypi.org/documentation/configuration/uart.md).

```
$ raspi-config
Interface Options->Serial->No->Yes
```

You'll also want to make sure the following are installed:

```
apt-get install python python-pip python-dev
pip install flask pytz requests restkit pyserial pymodbus numpy termcolor netifaces netaddr
```


## Troubleshooting
There is a script called `midsim.py` that can aid in troubleshooting. It allows you to query sensors from the command line. It is located at `sensor_hubv3/code/test/midsim.py` 

Below is the usage:

```
Usage: midsim.py [OPTION]...
  -h, --help            show this screen
  -v, --verbose         output verbose debug output
  -c, --continous=t,c   Keep pulling every t seconds, c many times c=0 for infinite
                        default is to pull once.
  -f, --format=format   The output format to use:
                        default:   The default style output
                        csv:       csv style output
  -t, --type=TYPE       TYPE=(temphum|anemometer|tachometer|thermocouple|pressure|pressurewide|
                              multipointreset|multipointc[1-4]|multipointaddrc[1-4]|ping|
                              unitversion|hubversion) *Required
  --get-cal             Get calibration value for type
  --set-cal=CAL_VALUE   Set calibration value for type
  -p, --port=PORT       PORT=#
  -a, --address=ADDRESS ADDRESS=#,#,#,...
  -u                    use udp instead of serial
  -d, --device=PATH     serial device to use for version 3, default /dev/ttyAMA0
  -o                    Use direct command code instead of general (aka version2)
  -j                    Just send commands then exit immediatly
  -s, --server=IP:PORT  Start midsim server listening on IP:PORT
  -r, --remote=IP:PORT  Query remote midsim server on IP:PORT

  address,port required except for --type=ping
  Max number of addresses is 32.
```


## Calibration
The main goal of the pressure modules was to report differencial pressure. The pressure module can be calibrated and there is a script to help with that process. It takes a large amounts of samples and sets an offset to match the reference. This script can be found at `sensor_hubv3/code/test/calibrator.py`


## Configure mid_software

Copy the mid_software to the raspberry pi. Copy `MID.cfg.example` to `MID.cfg` but one directory down from the location of mid_software. Modify MID.cfg for your needs. The most importanted are `baseurl` and `MIDpassword`Below is a reference for what each key means:

* `baseurl` The url to the base location of your running instance of [isadore_server](https://github.com/bluthen/isadore_server/).
* `MIDname` If you have multiple mids, this needs to be set so it knows which config to fetch. If it doesn't exist, all configs are fetched.
* `MIDpassword` The mid password that was set for your instance of isadore_server.
* `configpath` relative url where it should get the systems unit configuration. shouldn't need changing.
* `uploadpath` the relative url it should use to upload sensor data it gets. shouldn't need changing.
* `rcstatuspath` the relative url it uses for controls. shouldn't need changing.
* `hub_serial` the serial port to use to communicate with the hub electronics board. `/dev/ttyAMA0` on old raspberry pi's, `/dev/serial0` on new ones.
* `STORE_RAW_DATA_MODE` shouldn't need changing
* `RAW_DATA_LOC` shouldn't need changing
* `RS485_TIMEOUT` time out per unit. shouldn't need changing
* `RS485_BAUD` The serial baud rate to use. shouldn't need changing
* `enableRC_p` shouldn't need changing
* `mid_reading_interval_seconds` The minimal amount of time to pass before reading sensor data again.
* `log_level` The level to log at, can be `ERROR`, `WARNING`, or `DEBUG`
* `turn_off` If it should be not be activly getting readings and uploading them.

There are also some other configurations for specific temperature controls. For now for those parameters, please see the code to find them.

## Running mid_software

Put the following in the crontab of the user that is going to run mid_software on the MID. Replace the path to where you copied mid_software.

```
*/15 * * * * /home/pi/mid_software/processCheck.sh
*/10 * * * * /home/pi/mid_software/mid_log_check.sh
```

* `processCheck.sh` will start the process if it doesn't find it running.
* `mid_log_check.sh` tries to detect if the process locked up and will restart it, if it thinks it has.