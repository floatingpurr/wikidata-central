#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os

dirname = os.path.dirname(__file__)
FILE_IN = os.path.join(dirname, '../data/dataset.csv')
FILE_OUT = os.path.join(dirname, '../test_data/existing_wd_items.csv')



with open(FILE_IN, newline='') as f_in, open(FILE_OUT, 'w') as f_out:
        reader = csv.reader(f_in, delimiter=';')
        writer = csv.writer(f_out, delimiter=';')


        for row in reader:

            if row[10] != '':
                # copy line
                writer.writerow(row)