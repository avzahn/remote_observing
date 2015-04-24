import datetime
import pytz
from copy import copy, deepcopy
from sys import maxint

class schedule(dict):
    """
    Indexed by datetime objects which specify the shift, and valued
    by observer objects that specify the observer.
    """
    def __init__(self, shifts, observers):
        
        self.observers = observers
        
        for shift in shifts:

            self[shift] = None

        # sort in ascending karmic order
        self.observers.sort(key = lambda x: x.karma)
        
        self.unassigned_observers = copy(self.observers)
        self.unfilled_shifts = self.keys()
        self.weekend_shifts = [shift for shift in self if shift.is_weekend()]
        self.weekday_shifts = [shift for shift in self if shift.is_weekday()]

        self.can_weekend = [obs for obs in observers if obs.last(1).is_weekday()]


        # TODO: Find a proper place for this
        self.maybe_karma = 50


    def schedule(self):
        self.schedule_v1()   
    
        return a + "-" + b
            
    def text(self):
        """
        return the shift schedule as a mostly human readable string
        """
        text = ""

        shifts = sorted(self.keys)

        for shift in shifts:
            obs = self[shift]
            line = "%s ::  %s \n"%(obs.name, str(shift))

            text += line

        if len(self.unfilled_shifts) > 0: 

            text += "\n----unfilled shifts:----\n\n"

            for shift in self.unfilled_shifts:

                text += self.shift_to_string(shift) + "\n"

        unfillable = self.unfillable_shifts()

        text += "\n----unfillable shifts:----\n\n"
        for shift in unfillable:
                text += str(shift) + "\n"


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
                        if karma < obs.maybe_karma:
                            candidates.append(obs)
                            candidate_karma = karma
            
        return self.break_karmic_degeneracy(shift,candidates)
        
    def break_karmic_degeneracy(self, shift, observers):

        if len(observers) == 0:
            return None
        
        frequency = dict([ (obs,0) for obs in observers  ])
        
        for obs in frequency:
            
            hist = obs.last(4)
            for h in hist:
                frequency[obs] += shift_t.similar(shift,h)
                
        return max(frequency, key=frequency.get)

    def schedule_v1(self):
        self.first_pass_v1()
        
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

    def unfillable_shifts(self):

        unfillable = []

        for shift in self.unfilled_shifts:

            k = 0

            for obs in self.observers:

                k += obs.availability[shift]

            if k == 0:
                unfillable.append(shift)
        return unfillable

class observer(object):

    def __init__(self, maybe_karma = 26):
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
        _self.history = []
        
        # the next shift
        self.next_shift = None

        self.maybe_karma = maybe_karma

    @property
    def history(self):
        self._history.sort(reverse=True)
        return self._history

    @history.setter
    def history(self,value):
        self._history = sorted(value,reverse = True)

    def assign(self, shift):
        self.next_shift = shift
            
    def last_weekday(self):
        
        for shift in self.history:
            if shift.is_weekday:
                return deepcopy(shift)
                
    def last(self,n = 1):
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
            
        return deepcopy(history)

    def break_karmic_degeneracy(self, shifts):
        """
        Finds the shift that this observer has done most commonly
        in the past month

        Expects a list of shift_t's
        """

        history = self.last_n(4)

        if len(history) == 0:
            if len(shifts) > 0:
                return shifts[0]
            return None
            
        frequency = dict([ (s, 0) for s in shifts ])

        for s in frequency:
            for h in history:
                frequency[s] += shift_t.similar(h,s)

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


        
