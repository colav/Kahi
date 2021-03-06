import json
from pymongo import MongoClient
from time import time
from fuzzywuzzy import fuzz,process
import re
from unidecode import unidecode
import sys
from pandas import read_csv
from joblib import Parallel, delayed

from Kahi.KahiDb import KahiDb




class Kahi(KahiDb):
    def __init__(self,dbserver_url="localhost",port=27017,colav_db="colav",db_suffix="_antioquia",ror_url='https://api.ror.org/organizations?affiliation=',n_jobs=12,verbose=0):
        '''
        Class with the attributes and methods that will put the entire ETL process together
        '''
        super().__init__(dbserver_url=dbserver_url,port=port,colav_db=colav_db,db_suffix=db_suffix,ror_url=ror_url,n_jobs=n_jobs,verbose=verbose)
        
        self.data_articles=[]
        self.found_ids=[]
        self.articles=[] #articles with dois
        self.transformed=[] #articles in CoLav format
        self.loaded=[] #link to the ids of the loaded registers {document,author,institution,source}
        self.status={} #Marks the status of the process. For example: data cannot be loaded if its not linked
    
    #there should be different options to extract from files, lists or collections in mongo
    def extract_doi(self,data):
        '''
        Extracts the articles from the different raw sources in the database given a list of dois

        Parameters
        ----------
        data : list
            List of dois
        '''
        self.articles.extend(self.find_many_doi(data))

    def extract_from_doi_file(self,file,column):
        '''
        Uses a csv file with a column with the required DOIs to find the accurrences of a document in the different raw databases.

        Parameters
        ----------
        file : str
            path to csv file
        column : str
            Name of the column from which to extract the DOIs

        Returns
        -------
        List of tuples with the found registers in the order: lens, wos, scielo, scopus, scholar, oadoi
        If the register was not found, the entry is None

        '''
        self.articles.extend(self.find_doi_file(file,column))

    def extract_similarity(self,data):
        '''
        Extracts articles using a similarity algorithm
        to find the corresponding entity in each raw database

        Parameters
        ----------
        data : list
            List of dictionaries with the keys: "title", "source", "year". Which is the information needed to
            use the similarity algorithm. If one of those fields is not present, use epty string.
        '''
        self.articles.extend(self.find_many_similarity(data))

    def extract_from_collection(self,db,collection,field):
        '''
        Search for the entities given a dataset in a mongo db collection.
        Dataset must have the keys: doi, title, source and year.
        The function searches the corresponding entity in the raw databases
        even if the doi is not provided.

        Parameters
        ----------
        db : str
            Name of the mongodb database
        collection : str
            Name of the collection inside db which contains the data

        Returns
        -------
        List of tuples with the found registers in the order: lens, wos, scielo, scopus, scholar, oadoi
        If the register was not found, the entry is None.

        '''
        self.articles.extend(self.find_from_collection(db,collection,field))


    def transform(self):
        '''
        Transforms the data extracted in CoLav's format
        '''
        parsed=[]
        for paper in self.articles:
            entry={}
            entry["document"]=self.parse_document(paper)
            entry["author_institutions"]=self.parse_authors_institutions(paper)
            entry["source"]=self.parse_source(paper)
            parsed.append(entry)
        for paper in parsed:
            entry={}
            entry["document"]=self.join_document(paper["document"])
            entry["author_institutions"]=self.join_authors_institutions(paper["author_institutions"])
            entry["source"]=self.join_source(paper["source"])
            self.transformed.append(entry)

    def transform_one(self,register):
        entry={}
        entry["document"]=self.parse_document(register)
        entry["author_institutions"]=self.parse_authors_institutions(register)
        entry["source"]=self.parse_source(register)
        entry["document"]=self.join_document(entry["document"])
        entry["author_institutions"]=self.join_authors_institutions(entry["author_institutions"])
        entry["source"]=self.join_source(entry["source"])
        return entry

    def parallel_transform(self):
        self.transformed=Parallel(n_jobs=self.n_jobs,backend="threading",verbose=10)(delayed(self.transform_one)(reg) for reg in self.articles)

    def link(self):
        '''
        Links the transformed data to existing registers in the database
        '''
        linked=[]
        for paper in self.transformed:
            entry={}
            entry["author_institutions"]=[]
            entry["document"]=paper["document"]
            for author in paper["author_institutions"]:
                entry["author_institutions"].append(self.link_authors_institutions(author))
            entry["source"]=self.link_source(paper["source"])
            linked.append(entry)
        self.transformed=linked

    def link_one(self,register):
        entry={}
        entry["author_institutions"]=[]
        entry["document"]=register["document"]
        for author in register["author_institutions"]:
            entry["author_institutions"].append(self.link_authors_institutions(author))
        entry["source"]=self.link_source(register["source"])
        
        return entry
    
    def parallel_link(self):
        result=Parallel(n_jobs=self.n_jobs,backend="threading",verbose=10)(delayed(self.link_one)(reg) for reg in self.transformed)
        self.transformed=result

    def load(self):
        '''
        Loads the new registers to the databse and modify them if needed.
        '''
        for paper in self.transformed:
            self.insert_one(paper)

    def process_one(self,index):
        data=self.find_one_doi(self.articles[index])
        parsed=self.transform_one(data)
        del(data)
        linked=self.link_one(parsed)
        del(parsed)
        return self.insert_one(linked)

    def parallel_all_from_collection(self,db,collection,field):
        self.articles=self.get_doilist_from_collection(db,collection,field)
        result=Parallel(n_jobs=self.n_jobs,backend="threading",verbose=10)(delayed(self.process_one)(i) for i in range(len(self.articles)))
        self.status=result

    def parallel_all_from_doilist(self,doilist):
        self.articles=doilist
        result=Parallel(n_jobs=self.n_jobs,backend="threading",verbose=10)(delayed(self.process_one)(i) for i in range(len(self.articles)))
        self.status=result

    def process_one_data(self,index):
        raw=self.data_articles[index]
        indexes,data=self.find_one_similarity(raw)
        self.found_ids.append(indexes)
        del(raw)
        parsed=self.transform_one(data)
        del(data)
        linked=self.link_one(parsed)
        
        for key,value in indexes.items():
            if value or value==0:
                #Adding the checkpoint data to the register
                linked["document"]["source_checked"].append({"source":key+self.db_suffix,"id":self.mongo_ids[key][value]})
                #removing the processed information from similarity lists
                self.mongo_ids[key].pop(value)
                self.titles[key].pop(value)
                self.sources[key].pop(value)
                self.years[key].pop(value)
                print("Now the similarity list for {} has {} elements".format(key,len(self.mongo_ids[key])))
        del(parsed)
        return self.insert_one(linked)

    def process_all_data(self):
        for i in range(len(self.data_articles)):
            process_one_data(i)
        
    def process_data_from_db(self,db,collection="stage",doi_field="doi_idx"):
        #get the register from the collection
        full_data,self.data_articles=self.find_data_through_database(db,collection,doi_field)
        #get the rest of the entitites from the similarity check not including the db
        for index,raw in enumerate(self.data_articles):
            indexes,data=self.find_one_similarity(raw,exclude=[db])
            self.found_ids.append(indexes)
            #add the register from the actual db
            data[db]=full_data[index]     
            #Proceed as usual
            parsed=self.transform_one(data)
            linked=self.link_one(parsed)
            del(parsed)
            for key,value in indexes.items():
                if value or value==0:
                    #Adding the checkpoint data to the register
                    linked["document"]["source_checked"].append({"source":key+self.db_suffix,"id":self.mongo_ids[key][value]})
                    #removing the processed information from similarity lists
                    self.mongo_ids[key].pop(value)
                    self.titles[key].pop(value)
                    self.sources[key].pop(value)
                    self.years[key].pop(value)
                    print("Now the similarity list for {} has {} elements".format(key,len(self.mongo_ids[key])))
            self.insert_one(linked)



    def parallel_all_from_datalist(self,datalist,batch_size=1):
        self.data_articles=datalist
        for i in range(0,len(self.data_articles),batch_size):
            if i+batch_size<=len(self.data_articles):
                result=Parallel(n_jobs=batch_size,backend="multiprocessing",verbose=10)(delayed(self.process_one_data)(j) for j in range(i,i+batch_size))
            else:
                result=Parallel(n_jobs=batch_size,backend="multiprocessing",verbose=10)(delayed(self.process_one_data)(j) for j in range(i,len(self.data_articles)))
            #erase the items in raw list of titles, sources and years according to the found ids

