from time import gmtime
from datetime import tzinfo
from scheduler import *
from copy import copy, deepcopy
import datetime
import pytz
import re

def classify(line):
    """
    First step in parsing the CSV version of a doodle poll
    """
    
    days =  ["Wed","Thu","Fri","Sat","Sun","Mon","Tue"]
    
    l = line.split(",")
    
    # test for month line
    pattern = "(January|February|March|April|May|June|July|August|September|November|December)"
    pattern += "\s[0-9][0-9][0-9][0-9]$"
    for entry in l:
        if re.match(pattern,entry):
            return "month"
    
    # test for the day line
    pattern = "(Wed|Thu|Fri|Sat|Sun|Mon|Tue)\s[0-3][0-9]$"
    for entry in l:
        if re.match(pattern, entry) != None:
            return "day"
            
    # test for the shift time line
    pattern = "[0-9]:[0-5][0-9]\s(AM|PM)$"
    for entry in l:
        if re.match(pattern, entry) != None:
            return "shift"
        
    # test for an availability line
    pattern = "(OK|\(OK\))$"
    for entry in l:
        if re.match(pattern,entry) != None:
            return "availability"
        
    return "useless"

def gen_pacific_shifts(year,month,day, is_dst):

    if is_dst:
        hour = 10
    else:
        hour = 9
    
    start = datetime.datetime(year,month,day,hour)

    locale = pytz.timezone("US/Pacific")

    locale.localize(start, is_dst = is_dst)

    utc_start = pytz.utc.localize(deepcopy(start))

    short_dt = datetime.timedelta(hours = 4)
    long_dt = datetime.timedelta(hours = 16)

    utc_shifts = [shift_t(utc_start, utc_start+short_dt)]

    for i in range(1,21):

        s = utc_shifts[-1].end

        if i % 2 != 0:

            nxt = shift_t(s,s+short_dt)

        else:

            nxt = shift_t(s,s+long_dt)

        utc_shifts.append(nxt)

    return utc_shifts







