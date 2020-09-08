import xml.sax
import re
from collections import defaultdict
from nltk.corpus import stopwords
import Stemmer
import time
import os
import sys
import heapq

count_of_pages = 1
Identities = {}
stop_words=set(stopwords.words('english'))
split_on_reference = ['==References==', '== References ==']
split_on_external_links = ['==External links==', '== External links ==']
TYPE_LIST = ['t', 'b', 'i', 'c', 'r', 'e']

idd =""
tag =""
title =""
flag = 0
ind = 1
text_data = ["", "", "", "", ""] # infobox, body, reference, external, categories
balance = 0
infobox= []
body = []
references = [] 
external_links = []
categories= []
my_stemmer = Stemmer.Stemmer('english') 
temp_posting_list = defaultdict(list)
gap = 0
count_of_files = 0
count_of_final_files = 0
total_words = 0
distinct_terms = 0  # The number of distinct terms in corpus -> useful for binary-search

class MyParser(xml.sax.ContentHandler):
    
    def characters(self, content):
        global tag
        global ind
        global text_data
        global balance
        global title
        global idd
        global flag
        content_len = len(content)
        if tag == 'text':
            good_to_add = True
            if ind < 2:
                for i in range(2):
                    ll = len(split_on_reference[i])
                    if content_len >= ll and content[0 : ll] == split_on_reference[i]:
                        ind = 2
                        good_to_add = False
            if ind < 3:
                for i in range(2):
                    ll = len(split_on_external_links[i])
                    if content_len >= ll and content[0 : ll] == split_on_external_links[i]:
                        ind = 3
                        good_to_add = False
            if ind >= 2 and ind < 4:
                if content_len >= 10 and content[0 : 10] == "[[Category":
                    ind = 4
            
            if ind == 1 and content_len >= 9 and content[0 : 9] == "{{Infobox":
                ind = 0
            # Add data to correct section of data
            if good_to_add:
                text_data[ind] += content
            
            if ind == 0:
                if content_len > 1:
                    prev = content[0]
                    for i in range(1, content_len):
                        if prev == '{' and content[i] == '{':
                            balance += 1
                        if prev == '}' and content[i] == '}':
                            balance -= 1
                        prev = content[i]
                    if balance == 0:
                        ind = 1
            
            
        if tag == 'title':
            title += content
        if tag == 'id' and flag==0:
            idd = content
            flag=1
    
    def startElement(self,name,attrs):
        global tag
        tag = name

    def endElement(self,name):
        global count_of_pages
        global idd
        global tag
        global title
        global flag
        global ind
        global text_data
        
        if name=='page':
            title = title.strip().encode("ascii",errors="ignore").decode()
            title = remove_crap(title)
            title = ' '.join(title)
            Identities[count_of_pages] = title
            text_processor()
            index_creation()
            count_of_pages += 1
            tag=""
            title=""
            idd=""
            flag=0
            ind = 1
            text_data = ["" , "", "", "", ""]
'''
Differentiates different part of wikipedia article and separates them into different 
'''
def text_processor():
    global infobox
    global body
    global references
    global external_links
    global categories
    infobox = []
    body = []
    references = []
    external_links = []
    categories = []
    # process infobox
    if len(text_data[0]) > 0:
        infobox = remove_crap(text_data[0][10 : ])
    
    # process body
    if len(text_data[1]) > 0:
        result = re.sub(r'\{\{.*\}\}',r' ',text_data[1])
        body = remove_crap(result)
    
    # process reference
    if len(text_data[2]) > 0:
        refer = re.findall(r'\|\s*title[^\|]*',text_data[2])
        result = []
        for r in refer:
            ii = r.find('=')
            result.append(r[ii+1 : len(r) - 1])
        references = remove_crap(' '.join(result))
    
    # process external_links
    if len(text_data[3]) > 0:
        links = re.findall(r'\*\s*\[.*\]',text_data[3])
        result = []
        for i in links:
            result.append(i[2:len(i)-1])
        external_links = remove_crap(' '.join(result))
    
    # process categories
    if len(text_data[4]) > 0:
        category = text_data[4].split('\n')
        result = []
        for cat in category:
            result.append(cat[11 : len(cat) - 2])
        categories = remove_crap(' '.join(result))
'''
Checks whether given text is a four digit number or not, or just maybe not even a number to begin with
'''
def check_num(text):
    n = len(text)
    if n > 0:
        if text[0] >= '1' and text[0] <= '9':
            if n == 4:
                ok = True
                for i in range(1, 4):
                    if text[i] < '0' or text[i] > '9':
                        ok = False
                return ok
            else:
                return False
        else:
            return True

'''
removes the special symbols from the text which are not useful information for search
'''
def remove_crap(text):
    result = []
    if len(text) == 0:
        return result
    text = text.strip().encode("ascii",errors="ignore").decode()
    text = re.sub(r'\`|\~|\!|\@|\#|\"|\'|\$|\%|\^|\&|\*|\(|\)|\-|\_|\=|\+|\\|\||\]|\[|\}|\{|\;|\:|\/|\?|\.|\>|\,|\<|\'|\n|\||\|\/"',r' ',text)
    text = re.sub(r'&nbsp;|&lt;|&gt;|&amp;|&quot;|&apos;|&cent;|&pound;|&yen;|&euro;|&copy;|&reg;',r' ',text)

    text = text.split()
    for w in text:
        w = w.strip()
        if w not in stop_words and check_num(w):
            w = my_stemmer.stemWord(w.lower())
            result.append(w)
    return result
'''
creates the inverted index using the frequency information stored in the freq_* lists it create
'''
def index_creation():
    global temp_posting_list
    global total_words
    terms = defaultdict(int)
    title_terms = title.split()
    freq_title = defaultdict(int)
    freq_global = defaultdict(int)
    freq_infobox = defaultdict(int)
    freq_references = defaultdict(int)
    freq_body = defaultdict(int)
    freq_categories = defaultdict(int)
    freq_external_links = defaultdict(int)
    
    for i in title_terms:
        freq_title[i] += 1
        freq_global[i] += 1
        
    for i in infobox:
        freq_infobox[i] += 1
        freq_global[i] += 1
    
    for i in references:
        freq_references[i] += 1
        freq_global[i] += 1
    
    for i in body:
        freq_body[i] += 1
        freq_global[i] += 1
    
    for i in external_links:
        freq_external_links[i] += 1
        freq_global[i] += 1
    
    for i in categories:
        freq_categories[i] += 1
        freq_global[i] += 1
    # helps in forming blocks like :-  100f30i5b35r2c3e22t5
    for key in freq_global.keys():
        total_words += freq_global[key]
        string = str(count_of_pages)
        if freq_infobox[key]:
            string += 'i' + str(freq_infobox[key])
        if freq_body[key]:
            string += 'b' + str(freq_body[key])
        if freq_references[key]:
            string += 'r' + str(freq_references[key])
        if freq_categories[key]:
            string += 'c' + str(freq_categories[key])
        if freq_external_links[key]:
            string += 'e' + str(freq_external_links[key])
        if freq_title[key]:
            string += 't' + str(freq_title[key])
        
        temp_posting_list[key].append(string)
    rem = count_of_pages%400
    if not rem:
        write_partial_index()
    
'''
Write partial index into files so that it can later be merged into single index, this helps
improving the speed of indexing, also for large corpus this is necessary, as large data cannot
fit into the memory.
'''   
def write_partial_index():
    global gap
    global temp_posting_list
    global Identities
    global count_of_files
    datum = []
    for term in sorted(temp_posting_list.keys()):
        posting_list = temp_posting_list[term]
        st = term + ' '
        st += ' '.join(posting_list)
        datum.append(st)
    
    with open('./data/index' + str(count_of_files) + '.txt', 'w') as file:
        file.write('\n'.join(datum))
    
    datum = []
    # offset = []
    for ind in sorted(Identities):
        # offset.append(str(gap))
        string = str(ind) + ' ' + Identities[ind].strip()
        datum.append(string)
        # gap += 1 + len(string)
    
    # with open('./data/titleOffset.txt', 'a') as file:
    #     file.write('\n'.join(offset))
    #     file.write('\n')
    with open('./data/title.txt', 'a') as file:
        file.write('\n'.join(datum))
        file.write('\n')
    
    count_of_files += 1
    print('count_of_files ' + str(count_of_files))
    Identities = {}
    temp_posting_list = defaultdict(list)

'''
Merge multiple partial indexes into a single large index and store meta-information in files
'''
def merge_small_indexes():
    # write this method using heapq, we will get set
    global path_to_indexes
    global count_of_final_files
    global distinct_terms
    not_processed = [1] * count_of_files
    indexes = {}
    term_list = []
    for i in range(count_of_files):
        indexes[i] = open(path_to_indexes+'index' + str(i) + '.txt', 'r')
        first_line = indexes[i].readline().strip()
        term = ""
        ind = 0
        for char in first_line:
            if char == ' ':
                break
            term += str(char)
            ind += 1
        # we need to use this as the key for heapq
        term_list.append((term, first_line[ind+1 : ], i))
    
    heapq.heapify(term_list)
    top = heapq.heappop(term_list)
    prev_term = top[0]
    posting_list = defaultdict(list)
    posting_list[prev_term].append(top[1])
    # read next line from this file
    first_line = indexes[top[2]].readline().strip()
    if len(first_line) > 0:
        term = ""
        ind = 0
        for char in first_line:
            if char == ' ':
                break
            term += str(char)
            ind += 1
        heapq.heappush(term_list, (term, first_line[ind+1 : ], top[2])) # this avoids the unnecessary space
    else:
        not_processed[top[2]] = 0
        indexes[top[2]].close()
        os.remove(path_to_indexes+'index'+str(i)+'.txt')
    
    count = 1
    while any(not_processed):
        top = heapq.heappop(term_list)
        diff = False
        if top[0] != prev_term:
            diff = True
        # write after reading 10000 lines, but ensure all lines with same term are read before reading
        if count > 16800 and count < 17800 and diff:
            datum = []
            count_of_final_files += 1
            for term in sorted(posting_list.keys()):
                distinct_terms += 1
                posting = posting_list[term]
                st = term + ' '
                docs = 0
                type_dict = defaultdict(int)
                for block in posting:
                    bb = block.split()
                    for b in bb:
                        docs += 1
                        for category in TYPE_LIST:
                            if category in b:
                                type_dict[category] += 1
                temp = "f" + str(docs)
                for category in TYPE_LIST:
                    if type_dict[category] > 0:
                        temp += category + str(type_dict[category])
                st += temp +  ' '
                st += ' '.join(posting)
                datum.append(st)
    
            with open(path_to_indexes+'findex' + str(count_of_final_files) + '.txt', 'w') as file:
                file.write('\n'.join(datum))
            posting_list = defaultdict(list)
            count = 0
        
        posting_list[top[0]].append(top[1])
        count += 1
        first_line = indexes[top[2]].readline().strip()
        if len(first_line) > 0:
            term = ""
            ind = 0
            for char in first_line:
                if char == ' ':
                    break
                term += str(char)
                ind += 1
            heapq.heappush(term_list, (term, first_line[ind+1 : ], top[2]))
        else:
            not_processed[top[2]] = 0
            indexes[top[2]].close()
            os.remove(path_to_indexes+'index'+str(top[2])+'.txt')
        prev_term = top[0]
        
    
    if count > 0:
        datum = []
        count_of_final_files += 1
        for term in sorted(posting_list.keys()):
            distinct_terms += 1
            posting = posting_list[term]
            st = term +  ' '
            docs = 0
            type_dict = defaultdict(int)
            for block in posting:
                bb = block.split()
                for b in bb:
                    docs += 1
                    for category in TYPE_LIST:
                        if category in b:
                            type_dict[category] += 1
            temp = "f" + str(docs)
            for category in TYPE_LIST:
                if type_dict[category] > 0:
                    temp += category + str(type_dict[category])

            st += temp +  ' '
            st += ' '.join(posting)
            datum.append(st)

        with open(path_to_indexes+'findex' + str(count_of_final_files) + '.txt', 'w') as file:
            file.write('\n'.join(datum))

'''
It changes the document Id to difference, which helps in reducing the size of index
'''
def keep_differences():
    global count_of_final_files
    for i in range(count_of_final_files):
        datum = []
        with open('./data/findex' + str(i+1) + '.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                terms = line.split()
                start = ""
                for char in terms[2]:
                    if char >= 'a' and char <= 'z':
                        break
                    else:
                        start += str(char)
                terms[1] += "s" + start
                start = int(start)
                new_terms = []
                new_terms.append(terms[0])
                new_terms.append(terms[1])
                n = len(terms)
                for j in range(2, n):
                    block = ""
                    num = ""
                    ind = 0
                    for char in terms[j]:
                        if char >= 'a' and char <= 'z':
                            break
                        else:
                            num += str(char)
                        ind += 1
                    num = int(num)
                    diff = num - start
                    if diff < 0:
                        print(terms[0])
                        raise ValueError("diff is negative")
                    block = str(diff)
                    block += terms[j][ind:]
                    new_terms.append(block)
                
                string = ' '.join(new_terms)
                datum.append(string)
            file.close()
        
        with open('./data1/findex' + str(i+1) + '.txt', 'w') as file:
            file.write('\n'.join(datum))
            file.close()


def main():
    global count_of_pages
    global Identities
    global distinct_terms
    global path_to_indexes
    global count_of_final_files
    current_directory = os.getcwd()
    folder = sys.argv[2]
    if folder[-1] != '/':
        folder += '/'
    directory = os.path.join(current_directory, folder)
    path_to_indexes = directory
    if not os.path.exists(directory):
        os.mkdir(directory)
    
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, False)
    handler = MyParser()
    parser.setContentHandler(handler)
    output = parser.parse(sys.argv[1])

    write_partial_index()
    # merge all the small index created using K-way merge
    merge_small_indexes()
    # we will need to change distinct_terms when we write the merge file function

    # only keep the difference
    keep_differences()
    with open(folder + sys.argv[3], 'w') as file:
        file.write(str(total_words) + '\n')
        file.write(str(distinct_terms) +'\n')
        file.write(str(count_of_final_files) + '\n')
        file.write(str(count_of_pages))
    
    print(count_of_files)
    print(count_of_pages)
    print(count_of_final_files)
if __name__ == '__main__':
	main()