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
python2 make.py -c -p --with-pressurev4b=0 102
```

If successful It is now programmed to use the pressurev4 module that gives you pressure/temperature/rh, and responses when address `102` is queried.


## Sensor Hub

To program the hub you would run with the programmer in place and powered:
```
cd sensor_hubv3/code
./fuse_crystal_clock.sh && make program
```