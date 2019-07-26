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
import json

NUM_BINS = 3

bins=[];fanBins=[];burnerBins=[]
totalBinCount = 1;binCount = 1;fanCount = 1;burnerCount=1

fanBins += [makeBinItem(id=totalBinCount,name="fan "+str(fanCount),x=totalBinCount,y=0)]
totalBinCount+=1
fanCount += 1

bins += [makeBinItem(id=totalBinCount+id,name="bin "+str(id),x=totalBinCount+id,y=0) for id in range(NUM_BINS)]
totalBinCount += len(bins)
binCount += len(bins)

fanBins += [makeBinItem(id=totalBinCount,name="fan "+str(fanCount),x=totalBinCount,y=0)]
totalBinCount += len(fanBins)
fanCount += len(fanBins)

