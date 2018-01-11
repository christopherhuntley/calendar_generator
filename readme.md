# Course Calendar Generator

This python project generates iCal files for class schedules scraped from Banner.
While the code is designed to scrape Fairfield University course data,
it could be adapted from other schools if needed. Many, many schools use Banner
to administer course scheduling and registration.  

The code is divided into two Python scripts:
* `course_schedule_scraper.py`, which generates JSON-formatted course data based on an HTML dump from Banner Web.
* `calendar_generator.py`, which generates an icalendar (ics) file for each course in the schedule. The caledars are dumped in the `calendars` folder and can be imported into any icalendar-compatible calendaring app (Google Calendar, Apple Calendar, etc.).

The current state of the code is pretty raw and is not intended to be production-ready. Please direct any questions to me at chuntley@fairfield.edu.
