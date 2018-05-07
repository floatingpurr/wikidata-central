#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os

dirname = os.path.dirname(__file__)
FILE_IN = os.path.join(dirname, '../data/report.csv')
FILE_OUT = os.path.join(dirname, '../data/inserted.csv')



with open(FILE_IN, newline='') as f_in, open(FILE_OUT, 'w') as f_out:
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)


        for row in reader:

            if row[2] == 'I':
                # copy line
                writer.writerow(row[:-1])