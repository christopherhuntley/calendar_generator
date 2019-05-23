"""
Created on Wednesday February 20 18:19:00 2019

@author: chuntley

A utility to populate course data repositories
"""

from calendar_generator import generate_course_calendar
from course_schedule_banner_scraper import scrape_banner_course_schedule

from pathlib import Path
import shutil
import json
import csv
import yaml

def generate_term_repos():
    for banner_file in sorted(Path("BannerData").glob("*.html")):
        # extract the term from the file name
        term_name = banner_file.name.split('.')[0]
        print(term_name)
        # set up a folder for the term's data
        term_folder_path = Path('CourseDataRepo/'+term_name)
        if not term_folder_path.is_dir():
            term_folder_path.mkdir()
        if not term_folder_path.joinpath("Calendars").is_dir():
            term_folder_path.joinpath("Calendars").mkdir()


        # copy the banner file to the term term_folder_path as banner.html
        shutil.copy2('BannerData/'+banner_file.name,'CourseDataRepo/'+term_name+'/banner.html')

        # generate the course_specs.json file from banner.html
        course_offerings = scrape_banner_course_schedule('CourseDataRepo/'+term_name+'/banner.html')
        with Path('CourseDataRepo/'+term_name+"/course_offerings.json").open("w") as f:
            json.dump(course_offerings,f)

        # generate courses.csv from course_offerings.json
        with Path('CourseDataRepo/'+term_name+"/courses.csv").open('w',newline='') as csvfile:
            field_names = ['term']+list(course_offerings[0].keys())
            writer = csv.DictWriter(csvfile,field_names)
            writer.writeheader()
            for c in course_offerings:
                c['term'] = term_name
                writer.writerow(c)

        # generate calendars and meetings
        f = open('CourseDataRepo/'+term_name+'/cal_rules.yaml','r')
        cal_rules = yaml.load(f)

        meetings=[]
        for c in course_offerings:
            out = generate_course_calendar(c,cal_rules)
            meetings += out['meetings']
            cal = out['ical']
            with term_folder_path.joinpath("Calendars").joinpath(str(c['crn'])+".ics").open("wb") as icalfile:
                icalfile.write(cal)
        with term_folder_path.joinpath('course_meetings.csv').open('w',newline='') as csvfile:
            field_names = ['term']+ list(meetings[0].keys())
            writer = csv.DictWriter(csvfile,field_names)
            writer.writeheader()
            for meeting in meetings:
                meeting['term'] = term_name
                writer.writerow(meeting)


generate_term_repos()
