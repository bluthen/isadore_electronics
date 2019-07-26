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
import csv
import sys
import re


def main():
    if len(sys.argv) != 4:
        print("Usage: %s pos_file bom_file out_file" % (sys.argv[0],))
        sys.exit(1)
    combined = []
    with open(sys.argv[1], 'r') as f:
        for line in f.readlines():
            if line[0] == '#':
                continue
            pos = {}
            line_split = re.split('\s+', line)
            pos['ref'] = line_split[0].strip()
            pos['val'] = line_split[1]
            pos['package'] = line_split[2]
            pos['posx'] = line_split[3]
            pos['posy'] = line_split[4]
            pos['rot'] = line_split[5]
            pos['side'] = line_split[6]
            pos['digikey'] = ''
            pos['bom_desc'] = ''
            combined.append(pos)
    with open(sys.argv[2], 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            split_labels = row['Labels'].split(',')
            split_labels = map(str.strip, split_labels)
            digikey_part = row['Primary Source'].split(': ')
            if len(digikey_part) == 2:
                digikey_part = digikey_part[1]
                found = 0
                for crow in combined:
                    #print(crow['ref'], split_labels)
                    if crow['ref'] in split_labels:
                        crow['digikey'] = digikey_part
                        crow['bom_desc'] = row['Part']
                        found += 1
                if found != len(split_labels):
                    print("Warning: Not found all of" + str(split_labels), found)
    with open(sys.argv[3], 'w') as f:
        writer = csv.DictWriter(f, fieldnames=combined[0].keys())
        writer.writeheader()
        for row in combined:
            writer.writerow(row)
    print('Done: ' + sys.argv[3])


if __name__ == '__main__':
    main()
