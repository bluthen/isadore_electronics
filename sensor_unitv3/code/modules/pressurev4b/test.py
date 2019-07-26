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
import sys

def calc(temp, hum):
    temp=(-40.2)+0.018*temp
    h=-2.0468+0.0367*hum+-1.5955e-6*hum**2
    h=(( (temp-32.0)/1.8)-25)*(0.01+0.00008*hum)+h
    return temp, h

def psmall(p):
    p=0.0022888*p+50.0
    return p

print calc(int(sys.argv[1]), int(sys.argv[2]))
print psmall(int(sys.argv[3]))


