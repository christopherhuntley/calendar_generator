#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 12:57:56 2017

@author: chuntley

A utility for scraping Fairfield U course data from Banner Web (HTML) snapshots.
"""

import re
import csv
import json

#conda install beautifulsoup4
from bs4 import BeautifulSoup

# conda install beautifulsoup4

banner_cols = {
    'CRN':1,
    'Subj':2,
    'Crse':3,
    'Sec':4,
    'Cmp':5,
    'Cred':6,
    'Title':7,
    'Days':8,
    'Time':9,
    'Cap':10,
    'Act':11,
    'Rem':12,
    'Instructor':16,
    'Date':17,
    'Location':18
}

def scrape_banner_course_schedule(filename):
    '''Uses Beautiful Soup to parse an HTML file exported from Banner Web'''

    with open(filename) as fp:
        course_specs = []
        soup = BeautifulSoup(fp,'html.parser')
        data_display_table_rows = soup.find('table',class_='datadisplaytable').find_all('tr')
        #print(data_display_table_rows)

        #read the table one row at a time, skipping things we don't need
        for row in data_display_table_rows:
            cols = row.select("td.dddefault")
            if (cols):
                crn_raw = str(cols[banner_cols['CRN']].string).strip('\xa0')
                times = str(cols[banner_cols['Time']].string)
                times = times.replace(' pm','pm')
                times = times.replace(' am','am')
                times = times.replace(':','')
                times = times.strip('\xa0')
                meeting = {'days':str(cols[banner_cols['Days']].string).strip('\xa0').strip('\u00a0'),
                            'times':times,
                            'dates':str(cols[banner_cols['Date']].string),
                            'location':str(cols[banner_cols['Location']].string)}
                timecode = meeting['days']+" "+meeting['times']+" "+meeting['dates']+" "+meeting['location']


                if crn_raw:
                    # the normal case, not a continuation of the previous row with more timecodes
                    course_spec = {}
                    course_spec['crn']=int(crn_raw)
                    course_spec['catalog_id'] = str(cols[banner_cols['Subj']].string)+" "+ str(cols[banner_cols['Crse']].string)
                    course_spec['section'] = str(cols[banner_cols['Sec']].string)
                    course_spec['credits'] = str(cols[banner_cols['Cred']].string)
                    course_spec['title'] = str(cols[banner_cols['Title']].string)
                    course_spec['meetings'] = []
                    course_spec['timecodes'] = []
                    if meeting['days']:
                        course_spec['meetings'] += [meeting]
                        course_spec['timecodes'] += [timecode]
                    course_spec['primary_instructor'] = str(cols[banner_cols['Instructor']].get_text()).split(' (P)')[0]
                    course_spec['cap'] = str(cols[banner_cols['Cap']].string)
                    course_spec['act'] = str(cols[banner_cols['Act']].string)
                    course_spec['rem'] = str(cols[banner_cols['Rem']].string)
                    course_specs += [course_spec]
                else:
                    # extra timecodes
                    if meeting['days']:
                        course_specs[-1]['meetings'] += [meeting]
                        course_specs[-1]['timecodes'] += [timecode]




    #print(course_specs[:50])
    return course_specs;


#scrape_banner_course_schedule('Spring2018GradClassSchedule.html')
# course_offerings = scrape_banner_course_schedule('ClassData/Spring2019.html')
#print(course_offerings)
# f = open("Spring2019.json","w")
# json.dump(course_offerings,f)
