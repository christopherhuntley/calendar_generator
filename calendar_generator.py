#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thursday January 4 19:19:00 2018

@author: chuntley

A utility to generate ical calendars and meetings from course schedules
"""

import json
import re
from datetime import date,time,datetime,timedelta

# conda install -c conda-forge icalendar
from icalendar import Calendar, Event,vPeriod,vDatetime

# conda install -c anaconda python-dateutil
from dateutil.rrule import *
from dateutil.parser import *

# courses = []

# A bunch of regular expressions and constants for parsing timecode strings
tc_date_range_re = re.compile(r'([0-9]+)/([0-9]+)-([0-9]+)/([0-9]+)')
tc_time_range_re = re.compile(r'([0-9][0-9][0-9][0-9][PpAa][Mm])-([0-9][0-9][0-9][0-9][PpAa][Mm])')
tc_days_of_week_re = re.compile('(^[MTWRFSU]*) ')
tc_day_map = {'M':'MO','T':'TU','W':'WE','R':'TH','F':'FR','S':'SA','U':'SU'} # needed for icalendar
tc_day_map_du = {'M':MO,'T':TU,'W':WE,'R':TH,'F':FR,'S':SA,'U':SU} # needed for dateutil
tc_days_of_week = "UMTWRFS"

def generate_course_calendar(course,cal_rules):
    '''
    Generates one icalendar Calendar() and a list of meetings from the course timecodes
    Timecodes are dicts with 'days' (of week),'times' (range),'dates' (range), and 'location'
    '''

    meetings=[]
    cal = Calendar()
    cal['summary'] = str(course['crn']) + " " + course['catalog_id']+" "+ str(course['section'])
    cal['description'] = course['catalog_id'] +":" + course['title'] +" ("+ course['primary_instructor']+")"

    # generate one recurring event per timecode
    for meeting in course['meetings']:
        mdates = []

        # skip if there are no days
        if not meeting['days'] or meeting['days'] == [''] or meeting['days'] == '\xa0':
            break
        #print(course['crn'],meeting['days'],meeting['times'],meeting['location'])

        # handle explicit date ranges
        if '/' in meeting['dates']:
             year = cal_rules['term-year']
             drange = tc_date_range_re.findall(meeting['dates'])[0]
             startdate = date(year, int(drange[0]), int(drange[1]))
             enddate = date(year, int(drange[2]), int(drange[3]))

        # event metadata
        event = Event()
        event['summary'] = course['catalog_id']+" "+course['section']+" "+meeting['location']
        #event['uid'] = 'fairfield'+str(course['crn'])

        # timing parameters
        trange = tc_time_range_re.findall(meeting['times'])
        if not trange or trange == ['']:
            break
        starttime = datetime.strptime(trange[0][0],'%I%M%p')
        endtime = datetime.strptime(trange[0][1],'%I%M%p')

        # use datetime and dateutil to enumerate all the event start times
        tc_rrule = ''
        if startdate==enddate:
            if course['crn']==39006:
                print("AAAA", startdate)
            mdates += [datetime.combine(startdate,starttime.time())]
        else:
            wdays =[tc_day_map_du[d] for d in meeting['days']]
            # print(wdays)
            tc_rrule=rrule(WEEKLY, dtstart=datetime.combine(startdate,starttime.time()),byweekday=wdays, until=datetime.combine(enddate,endtime.time()))
            # print(tc_rrule)
            # print(course['crn'],datetime.combine(startdate,starttime.time()),wdays)
            mdates += list(tc_rrule)

        if course['crn']==39006:
            print("DDDD", mdates)

        # the first icalendar event
        event.add('dtstart',datetime.combine(mdates[0].date(),starttime.time()))
        event.add('dtend', datetime.combine(mdates[0].date(),endtime.time()))

        # icalendar recurrence rules
        days = [tc_day_map[d] for d in meeting['days'][0].strip()]
        event.add('rrule',{'freq':'weekly','byday':days,'until':enddate})

        # set up to use the rules to modify the icalendar dates
        cancel_dates = [] # These become exclusions to the rrule
        new_dates =[] # These are additional dates not coverd by the rrule

        # date shift rules ("Tuesday is on a Monday schedule")
        if 'date-shift-rules' in cal_rules:
            for ds_rule in cal_rules['date-shift-rules']:
                to_date = datetime.strptime(ds_rule['to-date'],"%Y-%m-%d")
                from_date = datetime.strptime(ds_rule['from-date'],"%Y-%m-%d")

                # check to see if the course is excluded
                if 'exclusions' in ds_rule:
                    skip = False
                    for exclusion in ds_rule['exclusions']:
                        exclusion_re = re.compile(exclusion)
                        if exclusion_re.match(course['catalog_id']):
                            skip = True
                    if skip:
                        break

                for rdate in mdates:
                    # cancel (pre-empt) classes on to-date
                    if rdate.date() == to_date.date():
                        cancel_dates += [rdate]

                    # add classes on from-date
                    if rdate.date() == from_date.date():
                        new_start = datetime.combine(to_date.date(),starttime.time())
                        new_end = datetime.combine(to_date.date(),endtime.time())
                        new_dates += [{'dtstart':new_start,'dtend':new_end}]

        # holiday rules
        if 'holiday-rules' in cal_rules:
            for holiday_rule in cal_rules['holiday-rules']:
                # check to see if the course is excluded
                if 'exclusions' in holiday_rule:
                    skip = False
                    for exclusion in holiday_rule['exclusions']:
                        exclusion_re = re.compile(exclusion)
                        if exclusion_re.search(course['catalog_id']):
                            skip = True
                    if skip:
                        break
                if tc_rrule:
                    start_dt = datetime.strptime(holiday_rule['start-dt'],"%Y-%m-%dT%H:%M")
                    end_dt = datetime.strptime(holiday_rule['end-dt'],"%Y-%m-%dT%H:%M")
                    cancel_dates += tc_rrule.between(start_dt,end_dt)

        if cancel_dates:
            for d in cancel_dates:
                mdates.remove(d)
            event.add('exdate',cancel_dates)

        cal.add_component(event)

        # add an event for each new_date not covered by the recurrence rule
        if course['crn']==39006:
            print("BBBB", new_dates)
        for new_date in new_dates:
            mdates += [new_date['dtstart']]
            new_event = Event()
            new_event['summary']=event['summary']
            new_event.add('dtstart',new_date['dtstart'])
            new_event.add('dtend',new_date['dtend'])
            cal.add_component(new_event)

        if course['crn']==39006:
            print("CCCC", mdates)
        for m in mdates:
            starttime_iso = datetime.isoformat(datetime.combine(m.date(),starttime.time()))
            endtime_iso = datetime.isoformat(datetime.combine(m.date(),endtime.time()))
            meetings += [{'crn':course['crn'],'location':meeting['location'],'day':"MTWRFSU"[m.date().weekday()],'start':starttime_iso,'end':endtime_iso}]

    return {'ical':cal.to_ical(),'meetings':meetings}

import yaml
def generate_term_calendars():
    f = open('CourseDataRepo/Spring2019/cal_rules.yaml','r')
    cal_rules = yaml.load(f)
    #print(cal_rules)
    f = open('CourseDataRepo/Spring2019/course_specs.json','r')
    course_specs = json.load(f)
    for course in course_specs[:1]:
        out = generate_course_calendar(course,cal_rules)
        print(out['ical'])
        print(out['meetings'])

# generate_term_calendars()

# Use the code to generate calendars
# fin = open("Spring2019.json","r")
# courses = json.load(fin)
# for course in courses:
#     with open('calendars/Spring2019/'+str(course['crn'])+".ics","wb") as fout:
#         # print(course['crn'])
#         fout.write(generate_course_calendar(course,cal_rules).to_ical())
