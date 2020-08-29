import xml.sax
import re
from collections import defaultdict
from nltk.corpus import stopwords
import Stemmer
import time
import os
import sys

count_of_pages = 1
Identities = {}
stop_words=set(stopwords.words('english'))
split_on_reference = ['==References==', '== References ==']
split_on_external_links = ['==External links==', '== External links ==']

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

def remove_crap(text):
    result = []
    if len(text) == 0:
        return result
    text = text.strip().encode("ascii",errors="ignore").decode()
    text = re.sub(r'\`|\~|\!|\@|\#|\"|\'|\$|\%|\^|\&|\*|\(|\)|\-|\_|\=|\+|\\|\||\]|\[|\}|\{|\;|\:|\/|\?|\.|\>|\,|\<|\'|\n|\||\|\/"',r' ',text)
    text = re.sub(r'&nbsp;|&lt;|&gt;|&amp;|&quot;|&apos;|&cent;|&pound;|&yen;|&euro;|&copy;|&reg;',r' ',text)

    text = text.split()
    for w in text:
        if w.strip() not in stop_words:
            w = my_stemmer.stemWord(w.lower())
            result.append(w)
    return result

def index_creation():
    global temp_posting_list
    
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
    
    for key in freq_global.keys():
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
    rem = count_of_pages%20000
    if not rem:
        write_partial_index()
    
    
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
        gap += 1
    
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

def main():
    global count_of_pages
    global Identities
    current_directory = os.getcwd()
    directory = os.path.join(current_directory, 'data')
    if not os.path.exists(directory):
        os.mkdir(directory)
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, False)
    handler = MyParser()
    parser.setContentHandler(handler)
    output = parser.parse(sys.argv[1])
    write_partial_index()
    print(count_of_files)
    print(count_of_pages)

if __name__ == '__main__':
	main()