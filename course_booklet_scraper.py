#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 12:57:56 2017

@author: chuntley

A utility for scraping Fairfield U course data from course booklet (PDFs) using tabula.
"""

import re
import csv
import json

# A set of tags that appear in the Notes field of a course_spec string
tags = {
  'CLRC':'Creative Life Residential College',
  'CORN':'Cornerstone Course',
  'HYBD':'Hybrid Course',
  'IGRC':'Ignatian Residential College',
  'RCOL':'Residential Colleges',
  'SERO':'Service Learning Option',
  'RNNU':'RN to BSN Students Only',
  'SJRC':'Service for Justice Residential College',
  'SDNU':'Second Degree Nurses Only',
  'UDIV':'U.S. Diversity',
  'SERL':'Service Learning',
  'WDIV':'World Diversity'
}

# A set of regular expressions (regex patterns) to use to extract data fields from a table row
flds = {
    'crn':re.compile('(^[0-9]+)'),
    'catalog_id':re.compile('(^[A-Z]+ [0-9,A-Z]+)'),
    'section':re.compile('(^[0-9,A-Z]+)'),
    'credits':re.compile('(^[0-9])'),
    'timecode':re.compile('(TBA|[Bb]y [Aa]rrangement|[Oo]nline|[MTWRFSU]+ [0-9]{4}-[0-9]{4}[PpAa][Mm])'),
    'tags':re.compile('('+'|'.join(tags.keys())+')'),
    'instructor':re.compile('(.+)'),
    'title':re.compile('(.+)')
}

def parse_table_row(row,date_range):
    ''' Parse one row of tabula data; each row is a column-wise list of strings'''

    course_spec = {}

    # Deal with extra timecodes on rows by themselves
    if not row[0]:
        unparsed = ' '.join(row)
        # use a regex to extract the timecode
        course_spec['timecodes'] = flds['timecode'].findall(unparsed)

        # return a partial course_spec with just the timecode
        return course_spec

    # What follows handles a typical table row exported from tabula

    # Parse out the easier columns that always seem to work in tabula
    course_spec['crn'] = int(row[0])
    course_spec['catalog_id'] = row[1] + ' ' + row[2]
    course_spec['section'] = row[3]
    course_spec['title'] = row[4]

    # Parse out the trickier columns that seem to merge awkwardly in tabula.
    # The logic below applies regular expressions to an unparsed string.
    # For each column:
    #   1. use a regex to extract data from the unparsed string;
    #   2. remove the extracted data from the unparsed string
    unparsed = ' '.join(row[5:]) # create a string of columns

    credits = flds['credits'].findall(unparsed)
    course_spec['credits'] = int(credits[0]) if credits else 0 # number of credits
    unparsed = flds['credits'].sub('',unparsed)

    course_spec['tags'] = flds['tags'].findall(unparsed) # list of tags
    unparsed = flds['tags'].sub('',unparsed)

    course_spec['timecodes']=flds['timecode'].findall(unparsed) # list of timecodes
    if date_range:
        for i in range(len(course_spec['timecodes'])):
            course_spec['timecodes'][i] += " "+date_range
    unparsed = flds['timecode'].sub('',unparsed)

    course_spec['instructor']=unparsed.strip() # remainder, minus extra whitespace

    return course_spec

def scrape_undergrad_course_booklet(filename,date_range=''):
    ''' Parse a course booklet that has been exported as a CSV from Tabula.'''
    with open(filename, newline='') as csvfile:
        linereader = csv.reader(csvfile)
        course_specs =[]
        for row in linereader:
            if not row[0].startswith('CRN'):
                course_spec = parse_table_row(row,date_range)
                if 'crn' in course_spec:
                    # add the new course_spec
                    course_specs += [course_spec]
                elif 'timecodes' in course_spec:
                    # merge timecode into last course_spec
                    course_specs[-1]['timecodes'] += course_spec['timecodes']
    return {'course_offerings':course_specs,'tags':tags}

#print(scrape_undergrad_course_booklet('tabula-201801CourseBooklet.csv','01/16-05/01'))
