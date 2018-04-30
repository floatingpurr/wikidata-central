#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wikidataintegrator import wdi_login, wdi_core
from datetime import datetime
from time import strftime, gmtime
import config
import csv
import re
import os
import json



# Basic stuff

dirname = os.path.dirname(__file__)
DATA_FILE = os.path.join(dirname, config.DATA_FILE)
REPORT_FILE = os.path.join(dirname, config.REPORT_FILE)
LOG_DIR = dirname+"/logs"

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
            school['name'] = row[8].replace('"', '').title()
            if row[10] == '': # create new school
                school['wiki_item'] = None
            else:
                school['wiki_item'] = row[10].split('https://www.wikidata.org/wiki/')[1]
        
            school['desc_it'] = row[15].title() + ' di ' + row[13].title() + ' in provinica di ' +row[4].title() +' (Italia)'
            school['desc_en'] = row[27].title() + ' in ' + row[13].title() + ' in the province of ' +row[4].title() + ' (Italy)'
            school['category'] = row[26].split('https://www.wikidata.org/wiki/')[1]
            school['address'] = "{via}, {cap} {com}".format(via = row[9].title(), com = row[13].title(), cap = row[11])
            school['zip'] = row[11]
            school['city'] = row[22].split('http://www.wikidata.org/entity/')[1]
            school['externalID'] = row[7]

            # check email
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

    report = list()

    for item in dataset:
        data = list()
        
        data.append( wdi_core.WDItemID(item['category'],  PROPS['instance of'], references=[base_reference]) )
        data.append( wdi_core.WDString(item['address'], PROPS['located at address'], references=[base_reference]) )
        data.append( wdi_core.WDString(item['zip'],  PROPS['zip'], references=[base_reference]) )
        data.append( wdi_core.WDItemID(item['city'], PROPS['located in city'], references=[base_reference]) )

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

        # update report
        if item['wiki_item'] is None: 
            report.append( ( wd_item.wd_item_id, item['externalID'], 'I' ) )
        else:
            report.append( ( wd_item.wd_item_id, item['externalID'], 'U' ) )

    return report



def save_report(report, file):
    with open(file, 'w') as f:
        f.write('WD_QID, External ID, Upsert status\n')
        csv_out=csv.writer(f)
        for item in report:
            csv_out.writerow(item)



if __name__ == "__main__":
    """ let's go! """
    # setup logging
    #wdi_core.WDItemEngine.setup_logging(log_dir = LOG_DIR, header=json.dumps({'name': 'Italian Schools', 'timestamp': str(datetime.now()), 'run_id': str(datetime.now())}))

    # load data in memory
    dataset = pre_load(DATA_FILE)

    # create basereference
    base_reference = create_reference()

    # login object
    login_instance = wdi_login.WDLogin(config.USER, config.PWD)

    # load in wikidata
    report = wd_load(login_instance, dataset, base_reference)

    # write report (map wikidata QIDs to external IDs)
    save_report(report, REPORT_FILE)