
def add_to_host_file(host, ip):
	with open('/etc/hosts') as f:
		if host in f.read():
			return
		f.write(f'\n{ip} {host}')

