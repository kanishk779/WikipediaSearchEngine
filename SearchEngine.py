import sys
import os
import math
import Stemmer
import time
import heapq
from nltk.corpus import stopwords
from collections import defaultdict

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
TYPE_DICT = {'t':0, 'b':1, 'i':2, 'c':3, 'r':4, 'e':5}
# We are storing the index in memory for now as it just 144MB , but this will not scale
INDEX = {}
title_dict = {}
distinct_words = 0
count_of_files = 0
first_term_list = []
doc_score = defaultdict(float) # this stores the score of each of the doc for a given query
count_of_documents = 0
first_num_list = []
count_of_title_files = 0
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
        return False, []
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
            if len(result) > 0:
                file.close()
                return True, result
            else:
                file.close()
                return False, result

                


'''
This adds score to list of document_ID which contain 'term' in 'field' using tf-idf
'''
def handle_field_query(term, field):
    global doc_score
    ok, posting = find_term(term)
    if ok:
        start = ""
        done = False
        for char in posting[1]:
            if char == 's':
                done = True
            if done:
                start += str(char)
        start = int(start)
        for i in range(TYPES):
            if field == i:
                docs = ""
                done = False
                for char in posting[1]:
                    if char >= 'a' and char <= 'z':
                        if char == TYPE_LIST[i]:
                            done = True
                        else:
                            done = False
                    else:
                        if done:
                            docs += str(char)
                if len(docs) > 0:
                    docs = int(docs)
                    docs = float(docs)
                else:
                    return
                idf = float(math.log(count_of_documents/docs))
                for data in posting[2:]:
                    if TYPE_LIST[i] in data:
                        docID = ''
                        ind = 0
                        for char in data:
                            if char >= 'a' and char <= 'z':
                                break
                            else:
                                docID += char
                            ind += 1
                        
                        current_char = '?'
                        freq = ""
                        sum = 0
                        for char in data[ind:]:
                            if char >= 'a' and char <= 'z':
                                if len(freq) > 0:
                                    freq = int(freq)
                                    i = TYPE_DICT[current_char]
                                    sum += RELEVANCE[i] * freq
                                    freq = ""
                                current_char = char
                            else:
                                freq += str(char)
                        freq = int(freq)
                        i = TYPE_DICT[current_char]
                        sum += RELEVANCE[i] * freq
                        
                        docID = int(docID)
                        docID += start
                        # add to the score of this docID
                        tf = 1.0 + math.log(1.0 + sum)
                        doc_score[docID] += float(tf*idf)
                break

'''
This adds score to list of document_ID which contains 'term' anywhere in it using tf-idf
'''
def handle_simple_query(term):
    global doc_score
    ok, posting = find_term(term)
    if ok:
        start = ""
        done = False
        for char in posting[1]:
            if char == 's':
                done = True
            if done:
                start += str(char)
        start = int(start)
        docs = ""
        for char in posting[1]:
            if char == 'f':
                continue
            if char >= 'a' and char <= 'z':
                break
            docs += str(char)
        docs = int(docs)
        docs = float(docs)
        idf = float(math.log(count_of_documents/docs))
        for data in posting[2:]:
            docID = ''
            ind = 0
            for char in data:
                if char >= 'a' and char <= 'z':
                    break
                else:
                    docID += char
                ind += 1
            docID = int(docID)
            current_char = '?'
            freq = ""
            sum = 0
            for char in data[ind:]:
                if char >= 'a' and char <= 'z':
                    if len(freq) > 0:
                        freq = int(freq)
                        i = TYPE_DICT[current_char]
                        sum += RELEVANCE[i] * freq
                        freq = ""
                    current_char = char
                else:
                    freq += str(char)
            freq = int(freq)
            i = TYPE_DICT[current_char]
            sum += RELEVANCE[i] * freq
            
            docID = int(docID)
            docID += start
            tf = 1.0 + math.log(1.0 + sum)
            doc_score[docID] += float(tf*idf)
            # add to the score of this docID
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
    global first_num_list
    global count_of_documents
    global count_of_title_files
    with open('./data/stat.txt', 'r') as file:
        terms = int(file.readline())
        distinct_words = int(file.readline())
        count_of_files = int(file.readline())
        count_of_documents = int(file.readline())
        file.close()
    
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
            file.close()
    count_of_title_files = 60
    for i in range(count_of_title_files):
        with open('./data/title' + str(i) + '.txt', 'r') as file:
            line = file.readline()
            term = ""
            for char in line:
                if char == ' ':
                    break
                else:
                    term += str(char)
            first_term_list.append(int(term))
            file.close()

'''
Prints the final results
'''
def print_title(nums):
    global first_num_list
    nums.sort()
    title_file_dict = defaultdict(list)
    for n in nums:
        ans = -1
        low = 0
        high = count_of_title_files - 1
        while low <= high:
            mid = low + int((high - low)//2)
            if first_num_list[mid] <= n:
                ans = mid
                low = mid + 1
            else:
                high = mid - 1
        if ans != -1:
            title_file_dict[ans].append(n)
    for key in title_file_dict.keys():
        title_file_dict[key].sort()
        freq = len(title_file_dict[key])
        with open('./data/title' + str(key) + '.txt', 'r') as file:
            ind = 0
            while True:
                line = file.readline().strip()
                term = ""
                for char in line:
                    if char == ' ':
                        break
                    else:
                        term += str(char)
                term = int(term)
                if term == title_file_dict[key][ind]:
                    print(line)
                    ind += 1
                    if ind == freq:
                        break
            file.close()



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
    # we need to see which one gives better results
    # load_titles()
    while True:
        query = input("ASK : ")
        start_time = time.time()
        query = query.lower().strip()
        if query == 'exit':
            break
        terms = query.split()
        print(terms)
        doc_score = defaultdict(float)
        query_terms = []
        k = ""
        for num in terms[0]:
            if num >= '0' and num <= '9':
                k += str(num)
        k = int(k)
        for term in terms[1:]:
            term = term.strip()
            if term not in stop_words:
                term = my_stemmer.stemWord(term)
                query_terms.append(term)
        if len(query_terms) == 0:
            print('This is not a good Query, Ask something meaningful')
            continue
        query_type = -1
        print('Query-terms')
        print(query_terms)
        for term in query_terms:
            start = False
            for i in range(TYPES):
                if term[0:2] == field_queries[i]:
                    query_type = i
                    start = True
                    break
            if query_type == -1:
                if start:
                    handle_simple_query(term[2:])
                else:
                    handle_simple_query(term)
            else:
                if start:
                    handle_field_query(term[2:], query_type)
                else:
                    handle_field_query(term, query_type)
            
        
        # WE are ouputting all the files which are related to any of the term in the query, But we should actually use the merge algo to AND the lists
        if len(doc_score) == 0:
            print('Could not find anything related to your query')
        else:
            print('These docs contain your answer')
            score_list = []
            for key in doc_score.keys():
                score_list.append((-1.0 * doc_score[key], key))
                print((key, doc_score[key]))
            heapq.heapify(score_list)

            n = len(score_list)
            titles_num = []
            for i in range(min(n, k)):
                top = heapq.heappop(score_list)
                num = top[1]
                # print(num, end=' ')
                # print(title_dict[num])
                # do binary search
                titles_num.append(num)
            print_title(titles_num)
            
        print('\nTime: ', time.time()-start_time)
        print("\n")
        
        
if __name__ == '__main__':
    main()