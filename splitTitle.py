import os
import sys

count_of_title_files = 99
def splitTitleFile():
    with open('title.txt', 'r') as file:
        lines = file.readlines()
        n = len(lines)
        div = n//count_of_title_files
        last = n - div*count_of_title_files
        ind = 0
        for i in range(count_of_title_files):
            with open('ftitle' + str(i) + '.txt', 'w') as file:
                datum = []
                for j in range(div):
                    datum.append(lines[ind])
                    ind += 1
                file.write('\n'.join(datum))
                file.write('\n')
                file.close()
        if last > 0:
            with open('ftitle' + str(count_of_title_files) + '.txt', 'w') as file:
                datum = []
                for i in range(last):
                    datum.append(lines[ind])
                    ind += 1
                file.write('\n'.join(datum))
                file.write('\n')
                file.close()
                
                    
            