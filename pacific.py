from shifts import shift_t
from scheduler import schedule, observer
from pytz import utc, timezone
import datetime
from re import search
from sys import argv
from fix_csv import fix

strptime = datetime.datetime.strptime
pacific = timezone('US/Pacific')

def gen_shifts(year,month,day, is_dst):
    """
    Create the list of Pacific shifts to be
    filled
    """

    if is_dst:
        hour = 10
    else:
        hour = 9
    
    start = datetime.datetime(year,month,day,hour)

    locale = timezone("US/Pacific")

    start = locale.localize(start, is_dst = is_dst)

    short_dt = datetime.timedelta(hours = 4)
    long_dt = datetime.timedelta(hours = 12)

    shifts = [shift_t(start, start+short_dt)]

    for i in range(1,21):

        s = shifts[-1].end

        if i % 3 != 0:

            nxt = shift_t(s,s+short_dt)

        else:

            nxt = shift_t(s+long_dt,s+long_dt+short_dt)

        shifts.append(nxt)

    # Monday is 0
    startday = start.weekday()
    # need to make sure a Monday is in the
    # first position in the list
    shifts = cycle(shifts,3*(7-startday))

    return shifts

def cycle(l,n):
    """
    move the first n elements of l to the end
    """
    end = l[:n]
    start = l[n:]
    return start + end

def karma(resp):
    """
    Take an availability response and turn it into 
    a karma value
    """

    if resp == None:
        return 10

    if resp =="":
        return 10

    resp = resp.lower()

    if search('yes',resp):
        return 10
    if search('no',resp):
        return 0
    if search('maybe',resp):
        return 26

def init_observers(sheet,shifts):
    """
    Creates a list of partially initialized observers 
    from the availability spreadsheet

    shifts is a list of shifts that must align with the
    columns of the availability sheet
    """
    observers = []

    with open(sheet,'r') as f:
        lines = f.readlines()

    for line in lines:

        row = line.split(',')

        if row[0] == '#':
            obs = observer(locale = pacific)
            obs.name = row[1].lower().rstrip()

            row = row[2:]
            for cell,shift in zip(row,shifts):
                weekend = 0
                if shift.is_weekend(pacific):
                    if karma(cell) == 10:
                        weekend = 15

                obs.availability[shift] = karma(cell) + weekend

            observers.append(obs)

    return observers

def handoff_dict(fname):

    fmt = '%m/%d/%Y %H:%M:%S'
    m = {}
    dt = datetime.timedelta(hours = 4)

    lookback = 42*6 # six weeks

    with open(fname,'r') as f:
        lines = f.readlines()

    for line in lines[-lookback:]:
        line = line.split(',')

        name,time = line[0].lower().rstrip(),line[1]
        time = utc.localize(strptime(time.rstrip(),fmt))

        s = shift_t(time - dt,time)
        try:
            m[name].append(s)
        except:
            m[name] = [s]

    return m

def finalize_observer(obs,handoff):

    for shift in obs.availability:

        try:
            for t in handoff[obs.name.lower().rstrip()]:
    
                obs.history.append(t)
    
                if shift_t.similar(shift.end,t.end,pacific):
                    # we really should be giving karma
                    # based on the availability value when
                    # the shift ocurred...
                    # TODO: save availabilities to a name indexed
                    # file for this purpose
                    obs.karma +=  obs.availability[shift]
                    
        except:
            print 'finalize observer: %s not found in handoff' % (obs.name)

def finalize_observers(handoff,observers):
    """
    Finish the initialization of a list of observers
    using the handoff report spreadsheet 
    """
    for obs in observers:
        finalize_observer(obs,handoff)

def main():
    """
    Create, fill, and output a schedule
    """
    
    fix("availability.csv")
    
#    shifts = gen_shifts(2015,8,5,True)

    if argv[4] == 'True':
        is_dst = True
    if argv[4] == 'False':
        is_dst = False

    shifts = gen_shifts(int(argv[1]),int(argv[2]),int(argv[3]),is_dst)

    observers = init_observers('availability.csv',shifts)

    handoff = handoff_dict('handoff.csv')

    finalize_observers(handoff,observers)

    sch = schedule(shifts,observers,pacific)

    sch.schedule()

    with open('sch.txt','w') as f:

        print >>f, sch.text()

    for shift in sorted(sch.keys()):
        print str(shift), sch[shift].name


if __name__ == "__main__":
    main()
