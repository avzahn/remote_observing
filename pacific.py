from shifts import shift_t
from scheduler import schedule, observer
from pytz import utc, timezone
import datetime

strptime = datetime.datetime.strptime

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

    locale = pytz.timezone("US/Pacific")

    start = locale.localize(start, is_dst = is_dst)

    short_dt = datetime.timedelta(hours = 4)
    long_dt = datetime.timedelta(hours = 16)

    shifts = [shift_t(start, start+short_dt)]

    for i in range(1,21):

        s = shifts[-1].end

        if i % 2 != 0:

            nxt = shift_t(s,s+short_dt)

        else:

            nxt = shift_t(s,s+long_dt)

        shifts.append(nxt)

    return shifts

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
	if resp =='yes':
		return 10
	if resp == 'no':
		return 0
	if resp == 'maybe':
		return 26


def init_observers(sheet,shifts):
	"""
	Creates a list of partially initialized observers 
	from the availability spreadsheet

	shifts is a list of shifts that must align with the
	columns of the availability sheet
	"""

	with open(sheet,'r') as f:
		for line in f:
			row = line.split(',')
			if row[0] == '#':
				obs = observer()
				obs.name = row[1]
				# may need to permute row
				row = row[2:]
				for cell,shift in zip(row,shifts):
					weekend = 0
					if shift.is_weekend():
						weekend = 15
					obs.availability[shift] = karma(cell)+weekend

def handoff_dict(fname):
	fmt = '%m/%d/%Y %H:%M:%S'
	m = {}
	with open(fname,'r') as f:
		lines = f.readlines()
	for line in lines:
		line = line.split(',')
		name,time = line[1],line[5]
		time = utc.localize(strptime(time,fmt))
		try:
			m[name].append(time)
		except:
			m[name] = [time]

	return m

def finalize_observer(obs,handoff):



	





def finalize_observers(handoff,observers):
	"""
	Finish the initialization of a list of observers
	using the handoff report spreadsheet 
	"""
	pass

def main():
	"""
	Create, fill, and output a schedule
	"""
	pass

if __name__ == "__main__":
	main()
