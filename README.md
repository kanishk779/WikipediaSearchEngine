# WikipediaSearchEngine
This is a IRE (Information Retrieval and Extraction) project which aims at
building a search engine on wikipedia corpus of about 40 GB size. 
The size of index is 10.5 GB.
The two main python scripts are ParserIndexer.py and SearchEngine.py
ParserIndexer.py builds the index from the wikipedia articles
1. It includes parsing the wikipedia corpus using xml parser.
2. Than words are grouped together based on where they are present, like
   infobox.
3. The inverted index is than created using the frequency calculated while
   parsing.
4. We first write the index in small chunks to files and later merge them to
   create the final index.
5. For merging we use the k-way merge algorithm.
6. At last to reduce space we take the difference of each of the term from the
   first term in the posting list.
7. Each term is stored in 'term f10t1b3i1c2r2e1 ......'
