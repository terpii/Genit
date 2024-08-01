from lib.debugging import *
from lib.arg_init import *
from lib.outstream import *
import pty
import subprocess

def runnikto(domain, port):
	nikto_pre = f'{color_main}[{port},nikto]{color_reset}'

	cmd = f"nikto -host {domain} -port {port}"

	debug2(f'{nikto_pre}Starting nikto on port {port}')
	debug3(f"running command {cmd}...")
	out_r, out_w = pty.openpty()
	nikto_p1 = subprocess.Popen(cmd, shell=True, stdout=out_w)
	
	f = OutStream(out_r)

	while True:
		lines, readable = f.read_lines()

		for line in lines:
			
			if 'tested' in line:
				debug(nikto_pre + color_main + line)
				debug1(f'{nikto_pre}Done!')
				return
				
			#nikto starts good things with a plus, so we mark that as informational
			if line.startswith('+'):
				debug(nikto_pre + color_info + line)
				continue 
			else:
				debug(nikto_pre + line)
		else:#else acts if the for loop hasnt been broke out of, so here it breaks out of both loops
			continue
		break
	return

def rungobuster(protocol, domain, port):
	gobusterpre = f'{color_main}[{port},gobuster]{color_reset}'

	cmd = f'gobuster dir --wordlist {args.wordlist.name} --url "{protocol}://{domain}:{port}" -x txt,php,html,js'

	debug2(f'{gobusterpre}Starting gobuster on port {port}...')
	debug3(f'running command {cmd}...')

	out_r , out_w = pty.openpty()
	gobuster_p1 = subprocess.Popen(cmd, shell=True, stdout=out_w)

	f = OutStream(out_r)

	while True:
		if gobuster_p1.poll() is not None:
			break
		lines , readable = f.read_lines()

		for line in lines:
			if line.startswith('http'):
				debug(gobusterpre + color_info + line + ' found')
				continue
			if 'Finished' in line:
				break
		else:
			continue
		break
					

	debug1(f'{gobusterpre}Done!')
	return

				

