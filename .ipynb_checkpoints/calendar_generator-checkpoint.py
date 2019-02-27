#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thursday January 4 19:19:00 2018

@author: chuntley

A utility to generate ical files from course schedules
"""

import json
import re
from datetime import date,time,datetime,timedelta

# conda install -c conda-forge icalendar
from icalendar import Calendar, Event,vPeriod,vDatetime

# conda install -c anaconda python-dateutil
from dateutil.rrule import *
from dateutil.parser import *

courses = []
cal_rules = {
    'term-start-date':datetime(2018,1,16),
    'term-end-date':datetime(2018,5,11),
    'date-shift-rules':[{'from-date':date(2018,2,19), 'to-date':date(2018,2,20),'exclusions':[re.compile(r'NS [5-6][0-9][0-9]'),re.compile(r'NSAN [5-6][0-9][0-9]'),re.compile(r'NSMW [5-6][0-9][0-9]')]}],
    'holiday-rules':[
        {'start-dt':datetime(2018,2,19,0,0,0),'end-dt':datetime(2018,2,20,0,0,0)}, # President's Day
        {'start-dt':datetime(2018,3,10,0,0,0),'end-dt':datetime(2018,3,18,23,59,59)}, # Spring Recess
        {'start-dt':datetime(2018,3,29,16,55,0),'end-dt':datetime(2018,4,2,16,55,0)}  # Easter
    ]
}



# A bunch of regular expressions and constants for parsing timecode strings
tc_date_range_re = re.compile(r'([0-9]+)/([0-9]+)-([0-9]+)/([0-9]+)')
tc_time_range_re = re.compile(r'([0-9][0-9][0-9][0-9][PpAa][Mm])-([0-9][0-9][0-9][0-9][PpAa][Mm])')
tc_days_of_week_re = re.compile('(^[MTWRFSU]*) ')
tc_day_map = {'M':'MO','T':'TU','W':'WE','R':'TH','F':'FR','S':'SA','U':'SU'} # needed for icalendar
tc_day_map_du = {'M':MO,'T':TU,'W':WE,'R':TH,'F':FR,'S':SA,'U':SU} # needed for dateutil

def generate_course_calendar(course):
    '''
    Generates one icalendar Calendar() from the course timecodes
    '''

    cal = Calendar()
    cal['summary'] = str(course['crn']) + " " + course['catalog_id']+" "+ str(course['section'])
    cal['description'] = course['catalog_id'] +":" + course['title'] +" ("+ course['instructor']+")"

    # generate one recurring event per timecode
    for tc in course['timecodes']:
        # determine days of the week
        tc_days = tc_days_of_week_re.findall(tc)
        # skip if there are no days
        if not tc_days or tc_days == ['']:
            break
        print(course['crn'],tc,tc_days)
        #set default date range
        startdate = cal_rules['term-start-date']
        enddate = cal_rules['term-end-date']

        # handle explicit date ranges
        if '/' in tc:
             year = cal_rules['term-start-date'].year
             drange = tc_date_range_re.findall(tc)[0]
             startdate = date(year, int(drange[0]), int(drange[1]))
             enddate = date(year, int(drange[2]), int(drange[3]))

        # event metadata
        event = Event()
        event['summary'] = course['catalog_id']+" "+course['section']
        #event['uid'] = 'fairfield'+str(course['crn'])

        # timing parameters
        trange = tc_time_range_re.findall(tc)
        if not trange or trange == ['']:
            break
        starttime = datetime.strptime(trange[0][0],'%I%M%p')
        endtime = datetime.strptime(trange[0][1],'%I%M%p')

        # use dateutil to enumerate all the event start times from the rrule
        wdays =[tc_day_map_du[d] for d in tc_days[0].strip()]
        tc_rrule=rrule(WEEKLY, dtstart=datetime.combine(startdate,starttime.time()),byweekday=wdays, until=datetime.combine(enddate,endtime.time()))
        #print(course['crn'],datetime.combine(startdate,starttime.time()),wdays)
        rdates = list(tc_rrule)

        # the first event
        event.add('dtstart',rdates[0])
        event.add('dtend', datetime.combine(rdates[0].date(),endtime.time()))

        # recurrence rules
        days = [tc_day_map[d] for d in tc_days[0].strip()]
        event.add('rrule',{'freq':'weekly','byday':days,'until':enddate})

        # set up to use the rules to modify the calendar dates
        cancel_dates = [] # These become exclusions to the rrule
        new_dates =[] # These are additional dates not coverd by the rrule

        # date shift rules ("Tuesday is on a Monday schedule")
        for ds_rule in cal_rules['date-shift-rules']:
            skip = False
            # check to see if the course is excluded
            for exclusion_re in ds_rule['exclusions']:
                if exclusion_re.match(course['catalog_id']):
                    skip = True
            if skip:
                break

            for rdate in rdates:
                # cancel (pre-empt) classes on to-date
                if rdate.date() == ds_rule['to-date']:
                    cancel_dates += [rdate]

                # add classes from the from date
                if rdate.date() == ds_rule['from-date']:
                    new_start = datetime.combine(ds_rule['to-date'],starttime.time())
                    new_end = datetime.combine(ds_rule['to-date'],endtime.time())
                    new_dates += [{'dtstart':new_start,'dtend':new_end}]

        # holiday rules
        for holiday_rule in cal_rules['holiday-rules']:
            cancel_dates += tc_rrule.between(holiday_rule['start-dt'],holiday_rule['end-dt'])

        if cancel_dates:
            event.add('exdate',cancel_dates)

        cal.add_component(event)

        # add an event for each new_date not covered by the recurrence rule
        for new_date in new_dates:
            new_event = Event()
            new_event['summary']=event['summary']
            new_event.add('dtstart',new_date['dtstart'])
            new_event.add('dtend',new_date['dtend'])
            cal.add_component(new_event)

    return cal

# Use the code to generate calendars
fin = open("FairfieldUniversitySpring2018.json","r")
courses = json.load(fin)


for course in courses:
    with open('calendars/'+str(course['crn'])+".ics","wb") as fout:
        print(course['crn'])
        fout.write(generate_course_calendar(course).to_ical())
