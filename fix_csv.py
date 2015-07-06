with open('availability.csv','r') as f:
	lines = f.readlines()

def join(l1,l2):
	_l1 = l1.translate(None,'"')
	_l2 = l2.translate(None,'"')
	return _l1.strip() + l2[1:]

newlines = []

for line in lines:

	if line[0] == '#':
		newlines.append(line)
	elif len(newlines) > 0:
		newlines.append(join(newlines.pop(),line))

with open('availability.csv','w') as f:
	for line in newlines:
		f.write(line)


