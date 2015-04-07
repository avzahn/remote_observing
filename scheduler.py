import datetime
import pytz
from copy import copy
from sys import maxint

"""
shifts are UTC localized datetime object (start,end) tuples

"""

class schedule_manager(object):
	def __init__(self, schedule):
		self.schedule = schedule
	def 



class schedule(dict):
	"""
	Indexed by datetime objects which specify the shift, and valued
	by observer objects that specify the observer
	"""
	def __init__(self, shifts, observers):
		
		self.observers = observers
		
		for shift in shifts:
			self[shift] = None

		# sort in ascending karmic order
		self.observers.sort(key = lambda x: x.karma)
		
		self.unassigned_observers = copy(self.observers)
		self.unfilled_shifts = self.keys()
		self.weekend_shifts = [shift for shift in self if is_weekend(shift)]
		self.weekday_shifts = [shift for shift in self if is_weekday(shift)]

		self.can_weekend = [obs for obs in observers if is_weekday(obs.last())]

		# default karma values to award for shifts. These will be 
		# ignored if an observer chooses to specify a different value
		
		# karma equal or greater to this corresponds to a shift
		# for which someone is available only if that shift cannot
		# be filled any other way
		self.maybe_karma = 50

		self.weekend_karma = 25
		self.weekday_karma = 10

	def schedule(self):
		return self.schedule_v1()	
	
	def shift_to_string(shift):
		
		h0, h1 = shift[0].hour, shift[0].hour
		m0, m1 = shift[0].minute, shift[1].minute
		d0, d1 = shift[0].weekday(), shift[1].weekday()
		
		if d0 == d1:
			s = shift[0].strftime( "%a %I:%M %p") +
			
	def text(self):
		"""
		return the shift schedule as a mostly human readable string
		"""
		text = ""

		for obs in self.observers:

			line = obs.name + " " + self.shift_to_string(obs.next_shift) + "\n"
			text += line

		if len(self.unfilled_shifts) > 0: 

			text += "\n unfilled shifts:\n"

			for shift in self.unfilled_shifts:

				text += self.shift_to_string(shift) + "\n"

		return text

	def assign(self, shift, obs):
		
		self[shift] = obs
		obs.assign(shift)

		self.unfilled_shifts.remove(shift)
		self.unassigned_observers.remove(obs)

		if is_weekday(shift):
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
			
		return self.break_karmic_degeneracy(candidates)
		
	def break_karmic_degeneracy(self, shift, observers):
		
		frequency = dict([ (obs,0) for obs in observers  ])
		
		for obs in frequency:
			
			hist = obs.last_n(4)
			for h in hist:
				frequency[obs] += shift_compare(shift,h)
				
		return max(frequency, key=frequency.get)
		
	def schedule_v1(self):

	# try to pass off the weekend shifts on the lowest karma
	# observers first

		for shift in copy(self.weekend_shifts):

			# recall this is sorted in ascending karmic order
			for obs in copy(unassigned_observers):
				
				shift = obs.minimize_karma(weekend_shifts)

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
			 shift = obs.minimize_karma(weekday_shifts)

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
			
def is_weekend(shift):
	"""
	For the moment, only test the start time
	of a shift for weekendness
	"""
	
	if shift[0].weekday() > 4:
		return True
	if shift[0].weekday = 4:
		# Friday nights count as weekends
		if shift[0].hour > 16
			return True
		
	return False
	
def is_weekday(shift):
	
	return !(is_weekend(shift))

def shift_compare(shift1, shift2, locale):
	"""
	Return 1 if the day, hour, and minute of two shifts
	are the same in a given locale, given by a pytz.timezone,
	and 0 otherwise
	"""

	s1 = locale.localize(shift1)
	s2 = locale.localize(shift2)

	a = [s1[0].weekday(), s1[0].hour, s1[0].minute, s1[1].weekday(), s1[1].hour, s1[1].minute]
	b = [s2[0].weekday(), s2[0].hour, s2[0].minute, s2[1].weekday(), s2[1].hour, s2[1].minute]


	# in principle we could generalize to return a number
	# that is a function of the similarity between 
	# the two shifts
	if a == b:
		return 1
	return 0

class observer(object):
	def __init__(self):
		"""
		The schedule class is responsible for most of the initialization,
		all we do here is declare some attributes
		"""
		
		# dict mapping a shift to the quantity of karma an observer gains
		# from that shift. A shift with a karma value of zero indicates 
		# nonavailability.
		self.availability = None
		
		# should be a string
		self.name = None
		self.email = None		
		
		# scheduler will attempt to keep karma as close to equal across
		# all observers as possible
		self.karma = None
		
		# list of shifts this observer has completed
		self.history = None
		
		# the next shift
		self.next_shift = None
		
	def assign(self, shift):
		self.next_shift = shift
		
	def last(self):
		try:
			return copy(self.history).sort()[-1]
		except:
			return None
			
	def last_weekday(self):
		
		for entry in copy(self.history).sort(reverse = True):
			if is_weekday(entry):
				return entry
				
	def last_n(self,n):
		"""
		return a list of the last n an observer has done,
		or fewer if there are fewer than n shifts
		"""
		
		self.history.sort(reverse = True)

		if len(self.history) >= n:
			history = self.history[0:n-1]
		
		else:
			history = self.history[0:len(self.history)-1]
			
		return history

	def break_karmic_degeneracy(self, shifts):
		"""
		Finds the shift that this observer has done most commonly
		in the past month
		"""

		history = self.last_n(4)
			
		frequency = dict([ (s, 0) for s in shifts ])
		
		for s in frequency:
			for h in history:
				frequency[s] += shift_compare(h,s)
				
		return max(frequency, key=frequency.get)
				
	def minimize_karma(self, shifts, desperate = False, maybe_karma = None):
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
						if karma < maybe_karma:
							running_min = karma
							minimal_shift.append(shift)
				
		return self.break_karmic_degeneracy(minimal_shift)
		
