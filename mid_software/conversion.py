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
from math import *

#http://lybniz2.sourceforge.net/safeeval.html

def evalConversion(evalStr, x, t=0):
	#make a list of safe functions 
	safe_list = ['math','acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh', 'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod', 'frexp', 'hypot', 'ldexp', 'log', 'log10', 'modf', 'pi', 'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh'] 
	#use the list to filter the local namespace 
	safe_dict = dict([ (k, locals().get(k, None)) for k in safe_list ]) 
	#add any needed builtins back in. 
	safe_dict['abs'] = abs
	safe_dict['x'] = float(x)
	safe_dict['t'] = float(t)
	#safe_dict['dir'] = dir 
	return eval(evalStr,{"__builtins__":None},safe_dict)


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
