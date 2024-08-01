
def runnikto(port):
	nikto_pre = f'{color_main}[{port},nikto]{color_reset}'

	cmd = f"nikto -host {args.target} -port {port}"

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

def rungobuster(port):
	gobusterpre = f'{color_main}[{port},gobuster]{color_reset}'

	cmd = f'gobuster -w {args.wordlist.name} -u http://{args.target}:{port} -e -np -x txt,html,php,js'

	debug2(f'{gobusterpre}Starting gobuster on port {port}...')
	debug3(f'running command {cmd}...')

	out_r , out_w = pty.openpty()
	gobuster_p1 = subprocess.Popen(cmd, shell=True, stdout=out_w)

	f = OutStream(out_r)

	while True:
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

				

