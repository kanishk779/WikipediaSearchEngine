import sys
import os
import math
import Stemmer
import time
from nltk.corpus import stopwords

stop_words=set(stopwords.words('english'))
my_stemmer = Stemmer.Stemmer('english')
TITLE = 0
BODY = 1
INFOBOX = 2
CATEGORY = 3
REFERENCE = 4
LINKS = 5
TYPES = 6
TYPE_LIST = ['t', 'b', 'i', 'c', 'r', 'e']
# We are storing the index in memory for now as it just 144MB , but this will not scale
INDEX = {}
title_dict = {}
distinct_words = 0
count_of_files = 0
first_term_list = []
doc_score = {} # this stores the score of each of the doc for a given query
count_of_documents = 0
RELEVANCE = [0.3, 0.1, 0.2, 0.25, 0.05, 0.1]

'''
This finds the term using binary search and returns its posting list
'''
def find_term(term):
    global INDEX
    global count_of_files
    global first_term_list
    low = 0
    high = count_of_files - 1
    ans = -1
    while low <= high:
        mid = low + int((high - low)//2)
        if first_term_list[mid] <= term:
            ans = mid
            low = mid + 1
        else:
            high = mid - 1
    if ans == -1:
        return 0, []
    else:
        with open('./data/findex' + str(ans + 1) + '.txt', 'r') as file:
            # check whether it is more efficient to read line by line or read all the lines at once
            line = file.readline()
            result = []
            while len(line) > 0:
                doc_term = ""
                for char in line:
                    if char == ' ':
                        break
                    else:
                        doc_term += str(char)
                if doc_term == term:
                    result = line.split()
                    break
                line = file.readline()

            return 1, result
                


'''
This returns list of document_ID which contain 'term' in 'field'
'''
def handle_field_query(term, field):
    ok, posting = find_term(term)
    result = []
    if not ok:
        return result
    for i in range(TYPES):
        if field == i:
            for data in posting[1:]:
                if TYPE_LIST[i] in data:
                    docID = ''
                    for char in data:
                        if char >= 'a' and char <= 'z':
                            break
                        else:
                            docID += char
                    result.append(docID)
            break
    return result

'''
This returns list of document_ID which contains 'term' anywhere in it
'''
def handle_simple_query(term):
    ok, posting = find_term(term)
    result = []
    if not ok:
        return result
    for data in posting[1:]:
        docID = ''
        for char in data:
            if char >= 'a' and char <= 'z':
                break
            else:
                docID += char
        result.append(docID)
    return result
'''
This loads the titles in memory for easy access of data instead of reading everytime from disk, titles can be multi words
'''
def load_titles():
    global title_dict
    with open('./data/title.txt','r') as file:
        lines = file.readlines()
        for line in lines:
            num = ""
            ind = 0
            for char in line:
                ind += 1
                if char == ' ':
                    break
                else:
                    num += char
            title_dict[int(num)] = line[ind : ]
    
'''
This reads the partial index into memory. We read such a file which contains our term
'''
def read_index_into_memory(num):
    global INDEX
    with open('./data/findex' + str(num) + '.txt', 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.split()
            INDEX[line[0]] = line[1 : ]
'''
Load necessary information in memory
'''
def load_info():
    global count_of_files
    global distinct_words
    global first_term_list
    global count_of_documents
    with open('./data/stat.txt', 'r') as file:
        terms = int(file.readline())
        distinct_words = int(file.readline())
        count_of_files = int(file.readline())
        count_of_documents = int(file.readline())
    
    for i in range(count_of_files):
        with open('./data/findex' + str(i+1) + '.txt', 'r') as file:
            line = file.readline()
            term = ""
            for char in line:
                if char == ' ':
                    break
                else:
                    term += str(char)
            first_term_list.append(term)

def main():
    global doc_score
    field_queries = ['t:', 'b:', 'i:', 'c:', 'r:', 'e:']
    
    '''
    we assume queries will follow certain rules
    1. If a field query is asked than it will be of the form 't:sachin india great i:2019 c:england'
    2. Which means this is not allowed 't:sachin t:india c:2019 i:great c:help'
    
    Maybe we can parse these, YES WE CAN!!
    '''
    
    # read_index_into_memory()
    load_info()
    load_titles()
    while True:
        query = input("ASK : ")
        start_time = time.time()
        query = query.lower().strip()
        if query == 'exit':
            break
        terms = query.split()
        doc_score = {}
        query_terms = []
        for term in terms:
            term = term.strip()
            if term not in stop_words:
                term = my_stemmer.stemWord(term)
                query_terms.append(term)
        if len(query_terms) == 0:
            print('This is not a good Query, Ask something meaningful')
            continue
        query_type = -1
        result = []
        print('Query-terms')
        print(query_terms)
        for term in query_terms:
            start = False
            for i in range(TYPES):
                if term[0:2] == field_queries[i]:
                    query_type = i
                    start = True
                    break
            docIDs = []
            if query_type == -1:
                if start:
                    docIDs = handle_simple_query(term[2:])
                else:
                    docIDs = handle_simple_query(term)
            else:
                if start:
                    docIDs = handle_field_query(term[2:], query_type)
                else:
                    docIDs = handle_field_query(term, query_type)
            
            result += docIDs
        
        # WE are ouputting all the files which are related to any of the term in the query, But we should actually use the merge algo to AND the lists
        if len(result) == 0:
            print('Could not find anything related to your query')
        else:
            print('These docs contain your answer')
            print(result)
            
        print('\nTime: ', time.time()-start_time)
        print("\n")
        
if __name__ == '__main__':
    main()