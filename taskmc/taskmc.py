#!/usr/bin/python3.7

"""Monte carlo estimation of completion dates for tasks in taskwarrior.

Requires some tasks with totalexistingtime as a user-defined attribute (UDA) to make a prediction.

Heavily based on Evidence-Based Scheduling by Joel Spolsky:
http://www.joelonsoftware.com/items/2007/10/26.html

and on the "RunMCSim code from the "mc_schedule" excel workbook written by
Michael J. Wade: http://stackexchange.com/users/2794703/mikewade

Copyright (C) 2020 by the author(s). Licensed under MIT license."""

import datetime
import time
import re
import random
#from workdays import workdays # Under BSD license, so not included.

from taskw import TaskWarrior

WORKING_HRS_PER_DY = 8
WORKING_DAYS_PER_WK = 5
HOLIDAYS = []

NUM_TRIALS = 1000 # Number of trials for Monte Carlo Sim
UDA_VELOCITY_KEY = 'velocity' # type: "number"
UDA_ESTIMATED_KEY = 'estimatedtime' # type: duration
UDA_ACTUAL_KEY = 'totalactivetime'  # type: duration

DISPLAY_WIDTH = 80

w = TaskWarrior()
config = w.load_config()
if UDA_ESTIMATED_KEY not in config['uda']:
    error('Missing UDA for estimated duration. Please follow setup procedures.')
if UDA_ACTUAL_KEY not in config['uda']:
    error('Missing UDA for total active time in config. Please follow setup procedures.')

def update_velocities(taskw, filters=''):
    "Loads velocities from taskwarrior instance, but saves values in taskwarrior UDA."
    # Same as 'load_velocities'
    pass

def load_velocities(taskw, filters=''):
    "Loads velocities from taskwarrior instance without changing values."
    tasks = taskw.load_tasks('completed')
    tasks = tasks['completed']
    tasks = [t for t in tasks
             if (UDA_ESTIMATED_KEY in t and UDA_ACTUAL_KEY in t)
                or (UDA_VELOCITY_KEY in t)]
    velocities = []
    # Todo: Filter tasks here
    for i in range(len(tasks)):
        if UDA_ESTIMATED_KEY in tasks[i] and UDA_ACTUAL_KEY in tasks[i]:
            # These come out as strings, so convert to timedelta objects
            est = duration_str_to_time_delta(tasks[i][UDA_ESTIMATED_KEY])
            act = duration_str_to_time_delta(tasks[i][UDA_ACTUAL_KEY])
            v = est / act
            velocities.append(v)
        elif UDA_VELOCITY_KEY in tasks[i]:
            pass # Todo: add a parser here to allow caching of velocities.
            # do some magic to convert to number
    return velocities # in seconds

#ToDo: Allow user to imput filters, so as to estimate time remaining in a project etc.
def incomplete_task_estimates(taskw, filters=''):
    "Retrieve totalestimatedtime estimates from as-yet-uncompleted tasks."
    #Todo: remove elapsed time from totalestimatedtime*estimated velocity.A bit tricky.
    tasks = taskw.load_tasks('pending')
    tasks = tasks['pending']
    tasks = [t for t in tasks if UDA_ESTIMATED_KEY in t]
    estimates = []
    for task in tasks:
        if UDA_ESTIMATED_KEY in task:
            # These come out as strings...
            estimates.append(duration_str_to_time_delta(task[UDA_ESTIMATED_KEY]))
    return estimates

def run_mc_sim():
    "Main function to load data, run sims, and display output."
    sims = [0]*NUM_TRIALS

    velocities = load_velocities(w)
    estimates = incomplete_task_estimates(w) # in seconds 

    for i in range(NUM_TRIALS):
        sims[i] = mcsim(estimates, velocities)

    sims = sorted(sims)

    # Calculate the distribution of predicted end dates
    now = time.localtime()
    start_date = datetime.datetime(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)

    #dates = [(workday(start_date, d, HOLIDAYS)) for i,d in enumerate(days)]
    #above code removed because of license issues.
    dates = [start_date + datetime.timedelta(seconds=s)
             * (7/WORKING_DAYS_PER_WK) * (24/WORKING_HRS_PER_DY) for s in sims]
    probs = [round(i+1)/len(dates) for i in range(len(dates))]

    probs70 = [p for p in probs if p >= 0.7]
    probs95 = [p for p in probs70 if p >= 0.9]
    index70 = probs.index(probs70[0])
    index95 = probs.index(probs95[0])

    print()
    print(' 70% probability of completion by',
          dates[index70])
    print(' 95% probability of completion by',
          dates[index95])

    # Create nice plot - evenly spaced time periods with percentiles
    print()

    max_dates = max(dates)
    min_dates = min(dates)
    dates_to_plot = [min_dates + i*(max_dates-min_dates)/30 for i in range(1, 30)]
    indexes_to_plot = []
    i = 0
    for d in dates_to_plot:
        while d > dates[i]:
            i += 1
        indexes_to_plot.append(i)

    probs_to_plot = [probs[i] for i in indexes_to_plot]
    dates_to_plot = [d.strftime('%Y.%m.%d %H:%M') for d in dates_to_plot]

    
    date_width = max(len(d) for d in dates_to_plot) + 1

    for i in range(len(dates_to_plot)):
        print(dates_to_plot[i], \
              chr(186) * int(probs_to_plot[i]*(DISPLAY_WIDTH - date_width)) +  \
              '-' * int((1-probs_to_plot[i])*(DISPLAY_WIDTH - date_width)))
    return

def mcsim(estimates, velocities):
    "Actually run a single monte carlo simulation"
    
    # Assumptions:
    # estimates = durations, in seconds, >= 0
    # velocity = estimate/actual, a floating point number >= 0

    # Check the inputs for garbage
    zerosec = duration_str_to_time_delta('0s')
    velocities = [v for v in velocities if v > 0]
    estimates = [e for e in estimates if e > zerosec]

    # Simulation happens here
    total_time = zerosec
    for est in estimates:
        random_velocity = random.choice(velocities)
        # Future improvements: prefer random velocities of tasks with similar estimated durations.
        total_time += est/random_velocity
    return total_time.seconds

# The below is modified from "timewarrior-time-tracking-hook" commit 0a813ef (Dec 3 2017)
# By Adam Coddington (coddingtonbear)
# Under MIT license

ISO8610DURATION = re.compile(
    "P((\d*)Y)?((\d*)M)?((\d*)D)?T((\d*)H)?((\d*)M)?((\d*)S)?")

# Convert duration string into a timedelta object.
# Valid formats for duration_str include
# - int (in seconds)
# - string ending in seconds e.g "123seconds"
# - ISO-8601: e.g. "PT1H10M31S"

def duration_str_to_time_delta(duration_str):
    "Convert a string representing a duration to a time-delta object"
    if duration_str.startswith("P"):
        match = ISO8610DURATION.match(duration_str)
        if match:
            year = match.group(2)
            month = match.group(4)
            day = match.group(6)
            hour = match.group(8)
            minute = match.group(10)
            second = match.group(12)
            value = 0
            if second:
                value += int(second)
            if minute:
                value += int(minute)*60
            if hour:
                value += int(hour)*3600
            if day:
                value += int(day)*3600*24
            if month:
                # Assume a month is 30 days for now.
                value += int(month)*3600*24*30
            if year:
                # Assume a year is 365 days for now.
                value += int(year)*3600*24*365
    elif duration_str.endswith("seconds") or \
         duration_str.endswith("second") or \
         duration_str.endswith("sec"):
        value = int(duration_str.rstrip('cdeons'))
    elif duration_str.endswith("minutes") or \
         duration_str.endswith("minute") or \
         duration_str.endswith("mins") or \
         duration_str.endswith("min"):
        value = int(duration_str.rstrip('eimnstu'))*60
    elif duration_str.endswith("hours") or \
         duration_str.endswith("hour") or \
         duration_str.endswith("hrs") or \
         duration_str.endswith("hr") or \
         duration_str.endswith("h"):
        value = int(duration_str.rstrip('hours'))*3600
    elif duration_str.endswith("days") or \
         duration_str.endswith("day") or \
         duration_str.endswith("d"):
        value = int(duration_str.rstrip('days'))*WORKING_HRS_PER_DY*3600
    elif duration_str.endswith("weeks") or \
         duration_str.endswith("week") or \
         duration_str.endswith("wks") or \
         duration_str.endswith("wk") or \
         duration_str.endswith("wk"):
        value = int(duration_str.rstrip("weeks"))*WORKING_HRS_PER_DY*WORKING_DAYS_PER_WK*3600
    elif duration_str.endswith("s"):
        value = int(duration_str.rstrip("s"))
    else:
        value = int(duration_str)
    return datetime.timedelta(seconds=value)

if __name__ == '__main__':
    run_mc_sim()
