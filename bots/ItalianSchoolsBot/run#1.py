#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wikidataintegrator import wdi_login, wdi_core, wdi_helpers
import config
import csv
import re
import os


dirname = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(dirname, config.DATA_FILE)


def load(filename):

    son_2_father = dict()
    father_2_sons = dict()

    # data file
    with open(filename, newline='') as File:  
        reader = csv.reader(File, delimiter=';')
        
        next(reader) # skip first line

        for row in reader:
            father = row[5] # ref
            son = row[7]
            
            if father != son:
                son_2_father[son] = father
                if father in father_2_sons:
                    father_2_sons[father].append(son)
                else:
                    father_2_sons[father] = [son]

        return son_2_father, father_2_sons





if __name__ == "__main__":
    """ let's go! """

    p,s = load(DATA_FILE)


# login object
# login_instance = wdi_login.WDLogin(config.USER, config.PWD)


# fast_run_base_filter = {'P5114' : ''}
# fast_run = True


# tax_qid_map = wdi_helpers.id_mapper('P5114', return_as_set=True)

# print (len(tax_qid_map))

# tax_qid_map = {k:list(v)[0] for k,v in tax_qid_map.items() if len(v)==1}

# print (len(tax_qid_map))






# Search for and then edit/create new item
#wd_item = wdi_core.WDItemEngine(item_name='<your_item_name>', fast_run=fast_run, fast_run_base_filter=fast_run_base_filter)