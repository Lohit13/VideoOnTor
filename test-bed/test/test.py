


parallel_calls = [1,10,50,80,90,100]

cmd = "wget http://192.168.2.80:5000/parallel_streams/xx"
args = shlex.split(cmd)

def make_calls(i):
	


def main():
	global parallel_calls
	for i in parallel_calls:
		make_calls(i)

if __name__=='__main__':
	main()