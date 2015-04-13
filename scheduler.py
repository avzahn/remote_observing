import datetime
import pytz
from copy import copy
from sys import maxint

"""
shifts are UTC localized datetime object (start,end) tuples

"""

def dt_eq(dt0,dt1):

    if dt0.tzname != dt1.tzname:
        return False
    if dt0.year != dt1.year:
        return False
    if dt0.month != dt1.month:
        return False
    if dt0.day != dt1.day:
        return False
    if dt0.hour != dt1.hour:
        return False
    if dt0.minute != dt1.minute:
        return False
    if dt0.second != dt1.second:
        return False
    if dt0.microsecond != dt1.microsecond:
        return False


class shift_t(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end
    def __getitem__(self,i):
        if i == 0:
            return self.start
        if i == 1:
            return self.end
    def __hash__(self):
        return hash(self.start)

    def __eq__(self,other):

        if not isinstance(other,shift_t):
            return False

        a = dt_eq(self.start,other.start)
        b = dt_eq(self.end,other.end)

        if a and b:
            return True
        return False 


class schedule(dict):
    """
    Indexed by datetime objects which specify the shift, and valued
    by observer objects that specify the observer
    """
    def __init__(self, shifts, observers, locale, dst):

        self.locale = locale
        self.dst = dst
        
        self.observers = observers
        
        for shift in shifts:

            self[shift] = None

        # sort in ascending karmic order
        self.observers.sort(key = lambda x: x.karma)
        
        self.unassigned_observers = copy(self.observers)
        self.unfilled_shifts = self.keys()
        self.weekend_shifts = [shift for shift in self if is_weekend(shift, locale, dst)]
        self.weekday_shifts = [shift for shift in self if is_weekday(shift, locale, dst)]

        self.can_weekend = [obs for obs in observers if is_weekday(obs.last(),locale,dst)]


        # TODO: Find a proper place for this
        self.maybe_karma = 50


    def schedule(self):
        self.schedule_v1()   
    
    def shift_to_string(self,_shift):

        if _shift == None:
            return ""

        locale = self.locale
        dst = self.dst

        shift = (_shift[0].astimezone(locale),_shift[1].astimezone(locale))
        
        h0, h1 = shift[0].hour, shift[0].hour
        m0, m1 = shift[0].minute, shift[1].minute
        d0, d1 = shift[0].weekday(), shift[1].weekday()
        
        if d0 == d1:
            a = shift[0].strftime( "%a %d %I:%M %p")
            b = shift[1].strftime( "%I:%M %p %Z")
        else:
            a = shift[0].strftime( "%a %d %I:%M %p")
            b = shift[1].strftime( "%a %d %I:%M %p %Z")


        return a + "-" + b
            
    def text(self):
        """
        return the shift schedule as a mostly human readable string
        """
        text = ""

        for obs in self.observers:

            line = obs.name + "  ::   "

            for next_shift in obs.next_shift:

                line += self.shift_to_string(next_shift) + " || "

            line += "\n"

            text += line

        if len(self.unfilled_shifts) > 0: 

            text += "\n----unfilled shifts:----\n\n"

            for shift in self.unfilled_shifts:

                text += self.shift_to_string(shift) + "\n"

        unfillable = self.unfillable_shifts()

        text += "\n----unfillable shifts:----\n\n"
        for shift in unfillable:
                text += self.shift_to_string(shift) + "\n"


        """
        must_trade = self.must_trade()
        text += "\n----must_trade: " + str(len(must_trade)) + "----\n"
        if len(must_trade) > 0:
            for obs in must_trade:
                text += obs.name
                text += "\n"
        """

        return text

    def assign(self, shift, obs):
        
        self[shift] = obs
        obs.assign(shift)

        self.unfilled_shifts.remove(shift)
        self.unassigned_observers.remove(obs)

        if is_weekday(shift,self.locale,self.dst):
            self.weekday_shifts.remove(shift)
        else:
            self.weekend_shifts.remove(shift)

    def minimize_karma(self, observers, shift, desperate = False):
        """
        Find the observer who requires the least karma to do a given shift. If 
        the desperation parameter is false, add the constraint that the observer
        is considered unavailable if they need more than the desperation limit
        of karma to do a shift

        Breaks degeneracies by how often an observer has had a given shift
        """

        candidates = []
        candidate_karma = maxint

        for obs in observers:
            karma = obs.availability[shift]
            if karma < candidate_karma:
                if karma > 0:
                    if desperate == True:
                        candidates.append(obs)
                        candidate_karma = karma
                    if desperate == False:
                        if karma < self.maybe_karma:
                            candidates.append(obs)
                            candidate_karma = karma
            
        return self.break_karmic_degeneracy(shift,candidates)
        
    def break_karmic_degeneracy(self, shift, observers):

        if len(observers) == 0:
            return None
        
        frequency = dict([ (obs,0) for obs in observers  ])
        
        for obs in frequency:
            
            hist = obs.last_n(4)
            for h in hist:
                frequency[obs] += shift_compare(shift,h)
                
        return max(frequency, key=frequency.get)

    def schedule_v1(self):
        self.first_pass_v1()

        must_trade = self.must_trade()
        
        if len(must_trade) > 0:

            self.trade_v1(must_trade)

        self.second_pass_v1()
    
        
    def first_pass_v1(self):
        """
        Make an attempt at not assigning any observer more than
        once. This pass is the only pass that makes much of an
        attempt at fairness in v1
        """

        # try to pass off the weekend shifts on the lowest karma
        # observers first

        for shift in copy(self.weekend_shifts):

            # recall this is sorted in ascending karmic order
            for obs in copy(self.unassigned_observers):
                
                shift = obs.minimize_karma(self.weekend_shifts)

                if shift != None:
                    self.assign(shift,obs)          
                        
        if len(self.weekend_shifts) > 0:
            
            # someone will have to do a weekend shift two weeks
            # consecutively
            
            for shift in copy(self.weekend_shifts):

                # make a weak attempt at minimizing global unhappiness
                obs = self.minimize_karma(self.unassigned_observers, shift)
                
                if obs != None:
                    
                    self.assign(shift,obs)

        if len(self.weekend_shifts) > 0:

            # we'll have to reach into the set of people who are available
            # only if necessary
            for shift in copy(self.weekend_shifts):

                # make a weak attempt at minimizing global unhappiness
                obs = self.minimize_karma(self.unassigned_observers, shift, desperate = True)
                
                if obs != None:
                    
                    self.assign(shift,obs)

        # now fill the weekday shifts
        
        for obs in copy(self.unassigned_observers):
            
            # again do this karmic order
            shift = obs.minimize_karma(self.weekday_shifts)

            # notice that unless an observer's last weekday
            # shift was marked available only if necessary,
            # that shift will default to having slightly lower
            # than the default weekday karma

            if shift != None:
                self.assign(shift,obs)


        if len(self.weekday_shifts) > 0:

            # look for people who are available only if necessary

            for shift in copy(self.weekend_shifts):
                obs = self.minimize_karma(self.unassigned_observers,shift, desperate = True)

    def second_pass_v1(self):

        can_weekend = copy(self.can_weekend)
        self.unassigned_observers = copy(self.observers)

        for obs in can_weekend:

            try:
                if is_weekend(obs.next_shift[-1],self.locale,self.dst):
                    can_weekend.remove(obs)
            except:
                pass

        for shift in copy(self.weekend_shifts):

            obs = self.minimize_karma(can_weekend, shift, desperate = True)

            if obs != None:
                self.assign(shift,obs)
                print obs.name
            else:
                print "not found"

        for shift in copy(self.weekday_shifts):

            obs = self.minimize_karma(self.unassigned_observers, shift, desperate = True)

            if obs != None:
                self.assign(shift,obs)
                print obs.name

            else:

                print "not found"



        






    def unfillable_shifts(self):

        unfillable = []

        for shift in self.unfilled_shifts:

            k = 0

            for obs in self.observers:

                k += obs.availability[shift]

            if k == 0:
                unfillable.append(shift)
        return unfillable


    def must_trade(self):

        must_trade = []

        for obs in self.unassigned_observers:
            k = 0
            for shift in self.unfilled_shifts:
                k += obs.availability[shift]
            if k == 0:
                must_trade.append(obs)
        return must_trade



    def trade_v1(self,observers):
        """
        Second attempt at not having any double shifts. Pass through
        all of the unassigned observers and attempt to execute a sequence
        of trades that increases the number of filled shifts
        """
        pass

            
def is_weekend(_shift, locale, dst):
    """
    For the moment, only test the start time
    of a shift for weekendness
    """
    
    if _shift == None:
        return False

    dt0 = copy(_shift.start)
    dt1 = copy(_shift.end)

    shift = shift_t( dt0.astimezone(locale), dt1.astimezone(locale))

    locale.normalize(shift.start)
    locale.normalize(shift.end)


    if shift[0].weekday() > 4:
        return True
    if shift[0].weekday() == 4:
        # Friday nights count as weekends
        if shift[0].hour > 16:
            return True
        
    return False
    
def is_weekday(shift, locale, dst):
    
    return not(is_weekend(shift,locale,dst))

def shift_compare(shift1, shift2, locale, dst):
    """
    Return 1 if the day, hour, and minute of two shifts
    are the same in a given locale, given by a pytz.timezone,
    and 0 otherwise
    """

    s1 = locale.localize(shift1, is_dst =  dst)
    s2 = locale.localize(shift2, is_dst = dst)

    a = [s1[0].weekday(), s1[0].hour, s1[0].minute, s1[1].weekday(), s1[1].hour, s1[1].minute]
    b = [s2[0].weekday(), s2[0].hour, s2[0].minute, s2[1].weekday(), s2[1].hour, s2[1].minute]


    # in principle we could generalize to return a number
    # that is a function of the similarity between 
    # the two shifts
    if a == b:
        return 1
    return 0

class observer(object):
    """
    remember to add None to history for no shift
    """

    def __init__(self):
        """
        The schedule class is responsible for most of the initialization,
        all we do here is declare some attributes
        """
        
        # dict mapping a shift to the quantity of karma an observer gains
        # from that shift. A shift with a karma value of zero indicates 
        # nonavailability.
        self.availability = {}
        
        # should be a string
        self.name = None
        self.email = None       
        
        # scheduler will attempt to keep karma as close to equal across
        # all observers as possible
        self.karma = 0
        
        # list of shifts this observer has completed
        self.history = []
        # make sure it's in reverse time order, with the most recent
        # shifts first
        self.history.sort(reverse = True)
        
        # the next shift
        self.next_shift = []


        # default karma values to award for shifts. These will be 
        # ignored if an observer chooses to specify a different value
        
        # karma equal or greater to this corresponds to a shift
        # for which someone is available only if that shift cannot
        # be filled any other way
        self.maybe_karma = 50

        self.weekend_karma = 25
        self.weekday_karma = 10


        
    def assign(self, shift):
        self.next_shift.append(shift)
        
    def last(self):
        try:
            return copy(self.history).sort()[-1]
        except:
            return None
            
    def last_weekday(self):
        
        for shift in self.history:
            if is_weekday(entry):
                return entry
                
    def last_n(self,n):
        """
        return a list of the last n an observer has done,
        or fewer if there are fewer than n shifts
        """

        if len(self.history) == 0:
            return []

        if len(self.history) >= n:
            history = self.history[0:n-1]
        
        else:
            history = self.history[0:len(self.history)-1]
            
        return copy(history)

    def break_karmic_degeneracy(self, shifts):
        """
        Finds the shift that this observer has done most commonly
        in the past month
        """

        history = self.last_n(4)

        if len(history) == 0:
            if len(shifts) > 0:
                return shifts[0]
            return None
            
        frequency = dict([ (s, 0) for s in shifts ])

        for s in frequency:
            for h in history:
                frequency[s] += shift_compare(h,s)

        return max(frequency, key=frequency.get)
                
    def minimize_karma(self, shifts, desperate = False):
        """
        For a given list of shifts, return the shift that gives the
        least nonzero karma
        """
        
        running_min = maxint
        minimal_shift = []
        
        for shift in shifts:
            
            karma = self.availability[shift]
            if karma > 0:
                if karma < running_min:
                    if desperate == True:
                        running_min = karma
                        minimal_shift.append(shift)
                    if desperate == False:
                        if karma < self.maybe_karma:
                            running_min = karma
                            minimal_shift.append(shift)
                
        return self.break_karmic_degeneracy(minimal_shift)


    def weekend_viability(self):
        pass


        
