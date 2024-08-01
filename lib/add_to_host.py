
def add_to_host_file(ip, host):
	with open('/etc/hosts', 'a+') as f:
		if host in f.read():
			return
		f.write(f'{ip} {host}\n')

