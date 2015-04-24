from copy import copy, deepcopy
from pytz import utc, timezone

class shift_t(object):
    """
    A hashable, comparable pair of datetime objects
    representing the start and end of a shift. Note that
    whoever creates this is responsible for localizing 
    the datetimes.
    """
    def __init__(self, start, end):
        
        self.start = start
        self.end = end

        tz = start.tzinfo

        if tz != utc:
            self.utc = shift_t.utc(self)

    def __getitem__(self,i):
        if i == 0:
            return self.start
        if i == 1:
            return self.end
    def __hash__(self):
        return hash(self.start)

    @classmethod
    def utc(cls,shift):

        try:
            s = utc.localize(shift.start)
            e = utc.localize(shift.end)
        except:
            s = shift.start.astimezone(utc)
            e = shift.end.astimezone(utc)

        return shift_t(s,e)

    @classmethod
    def datetime_eq(cls,dt0,dt1, attrs = None):
        """
        Determine if two datetimes occur at the
        same point in time
        """

        dt0,dt1 = copy(dt0), copy(dt1)
        dt0,dt1 = dt0.astimezone(utc), dt1.astimezone(utc)

        if attrs == None:

            attrs = ['year',
                'day',
                'hour',
                'minute',
                'second',
                'microsecond']

        for attr in attrs:
            if getattr(dt0,attr) != getattr(dt1,attr):
                return False
        return True

    @classmethod
    def similar(cls,dt0,dt1, locale = utc):
        """
        Determine if two utc datetimes occur at the
        same point in a weekly schedule.

        Currently, this tests to see if the two
        datetimes are within an hour in time
        """
        dt0 = dt0.astimezone(locale)
        dt1 = dt1.astimezone(locale)

        diff = 0
        diff += 24 * dt0.weekday()-dt1.weekday()
        diff += dt0.hour - dt1.hour
        diff += (dt0.minute - dt0.minute)/60.

        if abs(diff) <= 1:
            return 1

        return 0



    def __eq__(self,other):
        """
        shift_t comparison function used for key matching
        in dictionaries. Only returns true for shifts that
        start and end at nearly exactly the same time
        """

        if not isinstance(other,shift_t):
            return False

        a = shift_t.datetime_eq(self.start,other.start)
        b = shift_t.datetime_eq(self.end,other.end)

        if a and b:
            return True
        return False

    def is_weekend(self):
        
        if self.start.weekday() > 4:
            return True
        if self.start.weekday() == 4:
            # Friday nights count as weekends
            if self.start.hour > 14:
                return True

        return False

    def is_weekday(self):

        return not(self.is_weekend())

    def __str__(self):

        s,e = self.start, self.end
        
        h0, h1 = s.hour, e.hour
        m0, m1 = s.minute, e.minute
        d0, d1 = s.weekday(), e.weekday()
        
        if d0 == d1:
            a = s.strftime( "%a %d %I:%M %p")
            b = e.strftime( "%I:%M %p %Z")
        else:
            a = s.strftime( "%a %d %I:%M %p")
            b = e.strftime( "%a %d %I:%M %p %Z")

    def __repr__(self):
        a = self.start.strftime("%a %d %I:%M %p")
        b = self.end.strftime("%a %d %I:%M %p")
        return a + " - " + b

    def __lt__(self,other):
        return self.start < other

    def __gt__(self,other):
        return self.start > other

    def __le__(self,other):
        return self.start <= other

    def __ge__(self,other):
        return self.start >= other