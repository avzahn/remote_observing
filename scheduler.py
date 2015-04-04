import datetime
import pytz
from copy import copy

class schedule(dict):
	"""
	Indexed by datetime objects which specify the shift, and valued
	by observer objects that specify the observer
	"""
	def __init__(self, 	gcalendar = None,
						gsheet = None,
						shifts = None,
						observers = None):
		
		self.observers = observers
		
		for shift in shifts:
			self[shift] = None		
		
		if gsheet != None:
			self.gpull()
			self.gsheet = gsheet
			
		if gcalendar != None:
			self.gcalendar = gcalendar
		
	def gpush(self):
		"""
		Push a new google calendar
		"""
		pass
		
	def gpull(self):
		"""
		Pull new availability information and last weeks handoff information
		from a google sheet
		"""
		pass		
	
	def update(self):
		pass
	
	def shift_to_string(shift):
		pass
	
	def string_to_shift(string):
		pass
			
	def text(self):
		"""
		return the shift schedule as a mostly human readable string
		"""
		pass
				
	def assign(self, shift, obs):
		
		self[shift] = obs
		obs.assign(shift)
		
	def minimize_karma(self, observers, shift):
		"""
		Find the observer who requires the least karma to do a given shift
		"""
				
	def schedule_v1(self):

		# sort in ascending karmic order
		self.observers.sort(key = lambda x: x.karma)
		
		unassigned_observers = copy(self.observers)
		unfilled_shifts = self.keys()
		weekend_shifts = [shift for shift in self if is_weekend(shift)]
		weekday_shifts = [shift for shift in self if is_weekday(shift)]
		
		# try to pass off the weekend shifts on the lowest karma
		# observers first
		
		for obs in copy(unassigned_observers):
			
			# look for someone who hasn't done a weekend
			# the previous week
			if is_weekday(obs.last()):
				
				shift = obs.minimize_karma(weekend_shifts)
				
				if shift != None:
					
					self.assign(shift,obs)
					weekend_shifts.remove(shift)
					unfilled_shifts.remove(shift)
					unassigned_observers.remove(obs)					
						
		if len(weekend_shifts) > 0:
			
			# someone will have to do a weekend shift two weeks
			# consecutively
			
			shift = obs.minimize_karma(weekend_shifts)
				
			if shift != None:
					
				self.assign(shift,obs)
				weekend_shifts.remove(shift)
				unfilled_shifts.remove(shift)
				unassigned_observers.remove(obs)		
						
		# now fill the weekday shifts
		
		for obs in copy(unassigned_observers):
			
			# again do this in ascending karmic order
			
			for shift in copy(weekday_shifts):
				
						
						
			
				
				
			
		
			
			
						
			
def is_weekend(shift):
	
	if shift.weekday() > 4:
		return True
	if shift.weekday = 4:
		# Friday nights count as weekends
		if shift.hour > 16
			return True
		
	return False
	
def is_weekday(shift):
	
	if shift.weekday() < 5:
		return True
	return False

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
			return self.history[-1]
		except:
			return None
			
	def last_weekday(self):
		
		for entry in self.history.sort():
			if is_weekday(entry):
				return entry
				
	def minimize_karma(self, shifts):
		"""
		For a given list of shifts, return the shift that gives the
		least nonzero karma
		"""
		
		running_min = 0
		minimal_shift = None
		
		for shift in shifts[1:]:
			
			karma = self.availability[shift]
			if karma > 0:
				if karma < running_min:
					running_min = karma
					minimal_shift = shift
				
		return minimal_shift
		
