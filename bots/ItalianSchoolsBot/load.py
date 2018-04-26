#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wikidataintegrator import wdi_login, wdi_core
from time import strftime, gmtime
import config
import csv
import re
import os


# Basic stuff

dirname = os.path.dirname(__file__)
FILENAME = os.path.join(dirname, config.FILENAME)

ITEMS = {
    'GenBank'           : 'Q901755',
    'primary school'    : 'Q9842',
    'Italy'             : 'Q38',
    'Schools Portal'    : 'Q52116343',
}

PROPS = {
    'instance of'       : 'P31',
    'country'           : 'P17',
    'located in city'   : 'P131',
    'located at address': 'P969',
    'zip'               : 'P281',
    'email'             : 'P968',
    'stated in'         : 'P248',
    'retrieved'         : 'P813',
    'reference URL'     : 'P854',
}


EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")





# login object
login_instance = wdi_login.WDLogin(config.USER, config.PWD)

"""
# hopefully: https://www.wikidata.org/wiki/Wikidata:Property_proposal/Generic#Italian_School_ID
wdi_property_store.wd_properties['PXXXX'] = {
    'core_id': True
}
"""

def pre_load(filename):
    """Read from file and return a dataset in memory."""

    schools = list()

    with open(filename, newline='') as File:  
        reader = csv.reader(File)
        
        next(reader) # skip first line

        for row in reader:

            school = dict()

            if row[10] == '': # create new school
                school['wiki_item'] = None
            else:
                school['wiki_item'] = row[10].split('https://www.wikidata.org/wiki/')[1]
        
            school['name_it'] = row[15].title() + ' di ' + row[13].title() + ' in provinica di ' +row[4].title() +' (Italia)'
            school['name_en'] = row[27].title() + ' in ' + row[13].title() + ' in the province of ' +row[4].title() + ' (Italy)'
            school['category'] = row[26].split('https://www.wikidata.org/wiki/')[1]
            school['address'] = "{via}, {cap} {com}".format(via = row[9].title(), com = row[13].title(), cap = row[11])
            school['zip'] = row[11]
            school['city'] = row[22].split('http://www.wikidata.org/entity/')[1]

            # check email
            if EMAIL_REGEX.match(row[18]):
                school['email'] = row[18]
            else:
                school['email'] = None

            schools.append(school)
            print (school)

    return schools



def create_reference():
    """Create references for an item."""

    stated_in = wdi_core.WDItemID(ITEMS['Schools Portal'], PROPS['stated in'], is_reference=True)
    retrieved = wdi_core.WDTime(strftime("+%Y-%m-%dT00:00:00Z", gmtime()), PROPS['retrieved'], is_reference=True)
    url = "http://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Scuole"
    ref_url = wdi_core.WDUrl(url, PROPS['reference URL'], is_reference=True)
    return [stated_in, retrieved, ref_url]



def wd_load(dataset, base_reference):
    """Load the dataset in Wikidata adding a basereference where necessary."""

    for item in dataset:
        data = list()
        data.append( wdi_core.WDString(item['address'], PROPS['located at address'], references=[base_reference]) )

        # Search for and then edit/create new item
        if item['wiki_item'] is None: # create
            wd_item = wdi_core.WDItemEngine( data=data )
        else:
            wd_item = wdi_core.WDItemEngine( wd_item_id=item['wiki_item'], data=data )

        wd_item.write(login_instance)
        print wd_item # TODO: check if we can track wikidaa id for new items



if __name__ == "__main__":
    """ let's go! """

    # load data in memory
    dataset = pre_load(FILENAME)

    # create basereference
    base_reference = create_reference()
    print (base_reference)

    # load in wikidata
    wd_load(dataset, base_reference)