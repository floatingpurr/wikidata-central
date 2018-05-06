#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wikidataintegrator import wdi_login, wdi_core
from datetime import datetime
from time import strftime, gmtime, sleep
import config
import csv
import re
import os
import json



# Basic stuff

FINAL_REPORT = list()

dirname = os.path.dirname(__file__)
DATA_FILE = os.path.join(dirname, config.DATA_FILE)
MAP_FILE = os.path.join(dirname, 'test_data/permanent_map.csv')
REPORT_FILE = os.path.join(dirname, config.REPORT_FILE)
LOG_DIR = dirname+"/logs"


# setup logging
wdi_core.WDItemEngine.setup_logging(log_dir = LOG_DIR, header=json.dumps({'name': 'Italian Schools', 'timestamp': str(datetime.now()), 'run_id': str(datetime.now())}))


ITEMS = {
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
    'Italian School ID' : 'P5114',
}


EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")


"""
# hopefully: https://www.wikidata.org/wiki/Wikidata:Property_proposal/Generic#Italian_School_ID
wdi_property_store.wd_properties['PXXXX'] = {
    'core_id': True
}
"""

def pre_load(filename):
    """Read from file and return a dataset in memory."""

    schools = list()
    test_map = dict()

    # TODO: remove this map after test run
    with open(MAP_FILE, newline='') as File:
        reader = csv.reader(File)
        next(reader) # skip first line

        for row in reader:

            test_map[row[1]] = row[0]
        

    # data file
    with open(filename, newline='') as File:  
        reader = csv.reader(File, delimiter=';')
        
        next(reader) # skip first line

        for row in reader:

            school = dict()
            school['name'] = row[8].replace('"', '').title()
            
            if row[10] != '':
                school['wiki_item'] = row[10].split('https://www.wikidata.org/wiki/')[1]
                print ('Found existing entry in source file')
            elif row[7] in test_map: #TODO: remove the check on row[7] after test run       
                school['wiki_item'] = test_map[ row[7] ]
                print ('Found existing entry in permanent map')
            else: # create new school
                school['wiki_item'] = None

        
            school['desc_it'] = row[15].lower() + ' di ' + row[13].title() + ' in provinica di ' +row[4].title() +' (Italia)'
            school['desc_en'] = row[27].lower() + ' in ' + row[13].title() + ' in the province of ' +row[4].title() + ' (Italy)'
            school['category'] = row[26].split('https://www.wikidata.org/wiki/')[1]
            school['address'] = "{via}, {cap} {com}".format(via = row[9].title(), com = row[13].title(), cap = row[11])
            school['zip'] = row[11]
            school['city'] = row[22].split('http://www.wikidata.org/entity/')[1]
            school['externalID'] = row[7]

            # check email -  TODO: not available for test run
            if EMAIL_REGEX.match(row[18]):
                school['email'] = "mailto:"+row[18]
            else:
                school['email'] = None

            schools.append(school)

    return schools



def create_reference():
    """Create references for an item."""

    stated_in = wdi_core.WDItemID(ITEMS['Schools Portal'], PROPS['stated in'], is_reference=True)
    retrieved = wdi_core.WDTime(strftime("+%Y-%m-%dT00:00:00Z", gmtime()), PROPS['retrieved'], is_reference=True)
    url = "http://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Scuole"
    ref_url = wdi_core.WDUrl(url, PROPS['reference URL'], is_reference=True)
    return [stated_in, retrieved, ref_url]



def wd_load(login_instance, dataset, base_reference):
    """Load the dataset in Wikidata adding a basereference where necessary."""

    i = 0


    for item in dataset:
        data = list()
        
        data.append( wdi_core.WDItemID(item['category'],  PROPS['instance of'], references=[base_reference]) )
        data.append( wdi_core.WDString(item['address'], PROPS['located at address'], references=[base_reference]) )
        data.append( wdi_core.WDString(item['zip'],  PROPS['zip'], references=[base_reference]) )
        data.append( wdi_core.WDItemID(item['city'], PROPS['located in city'], references=[base_reference]) )
        data.append( wdi_core.WDItemID(ITEMS['Italy'], PROPS['country'], references=[base_reference]) )
        data.append( wdi_core.WDString(item['externalID'], PROPS['Italian School ID'], references=[base_reference]) )
        
        # TODO: not available for test run
        if item['email'] is not None:
            data.append( wdi_core.WDString(item['email'], PROPS['email'], references=[base_reference]) )


        # Search for and then edit/create new item
        if item['wiki_item'] is None: 
            # insert
            wd_item = wdi_core.WDItemEngine( item_name = item['name'], data = data, domain = None )
        else:
            # update
            wd_item = wdi_core.WDItemEngine( wd_item_id = item['wiki_item'], data = data )

        wd_item.set_label(item['name'], lang='it')
        wd_item.set_label(item['name'], lang='en')
        wd_item.set_description(item['desc_it'], lang='it')
        wd_item.set_description(item['desc_en'], lang='en')


        wd_item.write(login_instance)

        i += 1

        if i % 100 == 0:
            print ("Upserted {} items".format(i))

        # update report and log
        msg = '{},{}'.format( wd_item.wd_item_id, item['externalID'] )
        wdi_core.WDItemEngine.log("WARNING", msg)

        if item['wiki_item'] is None: 
            FINAL_REPORT.append( ( wd_item.wd_item_id, item['externalID'], 'I' ) )
        else:
            FINAL_REPORT.append( ( wd_item.wd_item_id, item['externalID'], 'U' ) )

        # print('Waiting...')
        # sleep(10) 

    # return FINAL_REPORT



def save_report(report, file):
    with open(file, 'w') as f:
        f.write('WD_QID, External ID, Upsert status\n')
        csv_out=csv.writer(f)
        for item in report:
            csv_out.writerow(item)



if __name__ == "__main__":
    """ let's go! """

    # load data in memory
    dataset = pre_load(DATA_FILE)

    # create basereference
    base_reference = create_reference()

    # login object
    login_instance = wdi_login.WDLogin(config.USER, config.PWD)

    # load in wikidata
    try:
        wd_load(login_instance, dataset, base_reference)
    except Exception as e:
        print (e)

    # write report (map wikidata QIDs to external IDs)
    save_report(FINAL_REPORT, REPORT_FILE)