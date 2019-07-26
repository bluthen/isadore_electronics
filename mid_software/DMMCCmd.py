#   Copyright 2010-2019 Dan Elliott, Russell Valentine
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#import spidev -- We import below so spidev is only a requirement if using dryer master
from conversion import evalConversion

def processDMMCCommands(JSON):
	cmds = []
	# This uses SPI ADC Mikro Click on Pi, Port is spi device slot, address is adc channel
	dm_mc_json = filter(lambda x: x["type"]=="dm_mc",JSON)
	if dm_mc_json:
		for json_grp in dm_mc_json:
			cmd = DMMCCmd(
				sensorID = json_grp['sensor_id'],
				slot=json_grp['port'],
				channel=json_grp['addy'],
				convertPy=json_grp['convert'],
			    bias=json_grp['bias'])
			cmd.execute()
			cmds.append(cmd)
	return cmds


class DMMCCmd:
	def __init__(self, sensorID=-1, slot=0, channel=1, convertPy="x", bias=0.0):
		self.sensorID = sensorID
		self.slot = slot
		self.channel = channel-1
		self.convertPy = convertPy
		self.bias = bias
		self.value=-1
		self.raw_data = -1
		self.error = False

	def _readADC(self):
		import spidev
		spi = spidev.SpiDev(0, self.slot)
                spi.max_speed_hz = 100000
		values = []
		for i in range(0, 18):
			buffer = spi.xfer2([0x06, self.channel<<6, 0])
			value = ((buffer[1] & 0x0F) << 8) + buffer[2]
			print value
			values.append(value)
		values.remove(max(values))
		values.remove(min(values))

		value = float(sum(values))/len(values)
		spi.close()
		return value

	def execute(self):
		self.raw_data = self._readADC()
		self.value = evalConversion(self.convertPy, self.raw_data) + float(self.bias)

	def to_JSON_WWW_data(self, readingTime):
		if self.error:
			return []
		else:
			return [{"sensor_id": self.sensorID,
					 "type": 'dm_mc',
					 "value": self.value,
					 "raw_data": self.raw_data,
					 "datetime": readingTime.isoformat()}]
