#!/bin/python3

import argparse
import errno
import os
import pty
import re
import socket
import subprocess
import sys
from threading import Thread
from urllib.parse import urlparse

from colorama import Fore, init
from colorama.ansi import Back


#class for handling command output
class OutStream:
	def __init__(self, fileno):
		self._fileno = fileno
		self._buffer = b""

	def read_lines(self):
		try:
			output = os.read(self._fileno, 1000)
		except OSError as e:
			if e.errno != errno.EIO: raise
			output = b""
		lines = output.split(b"\n")
		lines[0] = self._buffer + lines[0] # prepend previous
										   # non-finished line.
		if output:
			self._buffer = lines[-1]
			finished_lines = lines[:-1]
			readable = True
		else:
			self._buffer = b""
			if len(lines) == 1 and not lines[0]:
				# We did not have buffer left, so no output at all.
				lines = []
			finished_lines = lines
			readable = False
		finished_lines = [line.rstrip(b"\r").decode()
						  for line in finished_lines]
		return finished_lines, readable




color_main = Fore.MAGENTA;
color_reset = Fore.RESET + Back.RESET;
color_good = Fore.GREEN;
color_bad = Fore.RED;
color_info = Fore.LIGHTBLUE_EX;

banner = f"""
{color_main}
						   oo   dP   
								88   
.d8888b. .d8888b. 88d888b. dP d8888P 
88'  `88 88ooood8 88'  `88 88   88   
88.  .88 88.  ... 88    88 88   88   
`8888P88 `88888P' dP    dP dP   dP   
	 .88                             
 d8888P             
{color_reset}
https://github.com/terpii/Genit

"""


parser = argparse.ArgumentParser("A startup enumeration tool for penetration testing purposes")
parser.add_argument("-t", '--target' , metavar='127.0.0.1', help="The target to scan", dest="target", required=True)
parser.add_argument("-v", '--verbose', metavar='1', default="1" , help="a level of verbosity from 0 to 3, with 0 being very quiet", choices=range(4), type=int, dest="verbose")
parser.add_argument('--noclear', action='store_true', dest='noclear', help="will not clear your terminal on startup")
parser.add_argument("-f", "--fast", action='store_true', dest='fast', help="will try to focus on speed, faster but not as reliable")
parser.add_argument('-w', '--wordlist', metavar='/usr/share/wordlists/rockyou.txt', dest='wordlist', help='A wordlist to use when bruteforcing for directories on websites' , required=True , type=argparse.FileType('r'))
parser.add_argument('-o', '--output', metavar='path/to/outfile.txt', dest='output', help='A File to log all output to', type=argparse.FileType('w', encoding='UTF-8'))

args = parser.parse_args()


outputinargs = args.output is not None

#debug for only certain verbositys
def debug3(cmdoutput):
	if args.verbose == 3:
		debug(cmdoutput)

def debug2(cmdoutput):
	if args.verbose >= 2:
		debug(cmdoutput)

def debug1(cmdoutput):
	if args.verbose >= 1:
		debug(cmdoutput)

#just print but with color reset and log file
def debug(cmdoutput):
	print(cmdoutput + color_reset)
	
	if outputinargs:
		file = open(args.output.name, 'a')
		file.write(cmdoutput + color_reset + '\n')
		file.close()


def newline(count=1):
	for i in range(count):
		print("\n")

#return numbers only of a string
def numbers(s):
	return int(re.search(r"\d+", s).group(0))

#add necessary things to a nmap command
def parsenmap(input):
	if(args.fast):
		split = input.split(" ")
		split.insert(1, '--min-rate 10000')
		return ' '.join(split)
	else:
		return input


def printProgress(threads):
	debug2(f'{color_main}Threadinfo')
	debug1(f'')
	for thread in threads:
		if thread.is_alive():
			debug1(f'{color_main}{thread.name} is running')
		else:
			debug2(f'{color_info}{thread.name} is done')



def handleweb(port):
	debug2(f"handling web on port {port}...")

	threadinfo = f'{color_main}[{port},web]{color_reset}'
	threads = []

	nikto_t = Thread(target=runnikto, args=[port])
	nikto_t.daemon = True
	nikto_t.setName(f"nikto on port {port}")
	threads.insert(-1, nikto_t)
	threads[threads.index(nikto_t)].start()

	gobuster_t = Thread(target=rungobuster, args=[port])
	gobuster_t.daemon = True
	gobuster_t.setName(f"gobuster on port {port}")
	threads.insert(-1, gobuster_t)
	threads[threads.index(gobuster_t)].start()



	#waiting for threads to finish
	for thread in threads:
		thread.join()
		printProgress(threads)
	
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

				




#doing scripts for a port
def handleport(port):
	debug2(f"Starting handling on port {color_main}{port}")
	
	threads = []

	threadinfo = f'{color_main}[{port}]{color_reset}'

	#different commands for each verbosity
	nmapcmds = {
		0 : f"nmap -sC -sV  -p {port} {args.target}",
		1 : f"nmap -sC -sV  -p {port} {args.target}",
		2 : f"nmap -sC -sV -v -p {port} {args.target} | grep -vE '^\Host is up|Read data files from|Service detection performed|Initiating|Completed|adjust_timeouts2|Discovered open port'",
		3 : f"nmap -v -sC -sV -p {port} {args.target}"
	}
	
	cmd = parsenmap(nmapcmds.get(args.verbose))

	#running the commmands
	out_r, out_w = pty.openpty()
	debug3(f"Running command {cmd} ...\n")
	nmap_p1 = subprocess.Popen(cmd , shell=True, stdout=out_w)

	portinfo = "bm8k"

	portdetails = ''

	f = OutStream(out_r)
	line_is_service = False
	while True:
		lines, readable = f.read_lines()
		if not readable:
			break
		
		for line in lines:
			#if its the service line, save it and disable the variable
			if line_is_service:
				debug(threadinfo + color_bad + line)
				portinfo = line
				line_is_service = False
			
			elif line.startswith("|"):
				debug(threadinfo + line)
				portdetails += line

			#indicate whether the next line is the service line or not
			elif "PORT" in line and "STATE" in line and "SERVICE" in line:
				line_is_service = True
				debug(threadinfo + color_good + line)
			
			#end if the nmap done statement is in line
			elif "Nmap done:" in line:
				print(threadinfo + line)
				newline()
				break
			else:
				print(threadinfo + line)
		else:#else acts if the for loop hasnt been broke out of, so here it breaks out of both loops
			continue
		break
	
	#basic error handling
	if portinfo == "bm8k":
		debug(f"{color_bad}Port info wasnt able to be retrieved")
		return
	if 'unknown' in portinfo:
		debug(f"{color_bad}Port {port} wasn't able to be identified")
		return


	#identifying the service
	portinfo = re.sub(' +', ' ', portinfo)#removing double spaces for consistent service identification
	portsplit = portinfo.split(" ")

	#check wether a version has been identified or just a service and then select the right one
	if len(portsplit) > 3:
		service = ' '.join(portsplit[3: len(portsplit)])
	else:
		service = ' '.join(portsplit[2: len(portsplit)])
	
	
	debug1(f"{threadinfo}Searching after exploits for {service}...")
	
	version = ""

	#Identifiying services
	if " " in service: #sometimes service can be very simple just like only mysql so we check for that
		service_split = service.split(" ")
		service_split = list(filter(None, service_split))#remove emptys from list

		main_service = service_split[0]#first word is mostly the actual service

		#iterate through words and pick the first one containing a number as the version
		for word in service_split:
			for letter in word:
				try:
					import unicodedata
					unicodedata.numeric(letter)
					version = word
					break
				except (TypeError, ValueError):
					pass
		#this solution might break if a service is named g4ming or something like that

	else:
		main_service = service.replace("?", "")#nmap can be unsure of services, and marks that with ?. This could mess up our search so we remove it

	#handling websites
	if 'http' in portdetails.lower():
		thread = Thread(target=handleweb, args=[port])
		thread.daemon = True
		thread.setName(f"web on port {port}")
		threads.insert(-1, thread)
		threads[threads.index(thread)].start()
		#we dont need the variable anymore, its in the array
		del thread

	debug2(f"{threadinfo}Identified service: {main_service} {version}")

	#searching for exploits using searchsploit
	#theres lots of repetition here and im to lazy to fix
	if version is not "":
		debug(f"{threadinfo}{color_info}Duckduckgo search page: https://duckduckgo.com/?q={main_service}+{version}+vulnerability")

		debug3(f"{threadinfo}Running command 'searchsploit {main_service} -v {version}'....")
		expl_proc = subprocess.Popen(f"searchsploit {main_service} -v {version}", stdout=subprocess.PIPE, shell=True)

		(output, err) = expl_proc.communicate()

		expl_proc_status = expl_proc.wait()

		expl_count = 0

		for expl in output.decode().split("\n"):
			if not (" | " and "/" in expl):
				continue
			expl_count += 1

			debug(f'{threadinfo}{color_good}Exploit found: {expl}')

		if expl_count > 0:
			debug2(f"{threadinfo}{color_info}{expl_count} Exploits found")
		else:
			debug1(f"{threadinfo}{color_info}No exploits found")
	else:
		debug(f"{threadinfo}{color_info}Duckduckgo search page: https://duckduckgo.com/?q={main_service}+vulnerability")
		debug3(f"{threadinfo}Running command 'searchsploit {main_service}'....")

		expl_proc = subprocess.Popen(f"searchsploit '{main_service}'", stdout=subprocess.PIPE, shell=True)

		(output, err) = expl_proc.communicate()

		expl_proc_status = expl_proc.wait()

		expl_count = 0

		for expl in output.decode().split("\n"):
			if not (" | " and "/" in expl):
				continue
			expl_count += 1
			debug(f'{threadinfo}{color_info}Exploit found: {expl}')

		if expl_count > 0:
			debug2(f"{threadinfo}{color_info}{expl_count} Exploits found")
		else:
			debug1(f"{threadinfo}{color_info}No exploits found")

	#wait for threads to finish
	for thread in threads:
		thread.join()
		debug1(threadinfo + thread.getName() + ' Finished')
		printProgress(threads)


	return


def main():

	#dont clear if the argument is given
	if not args.noclear:
		os.system("clear")

	main_inf = f'{color_main}[main nmap]{color_reset}'

	threads = []

	debug(banner)

	#printing out all variables
	for arg in vars(args):
		if arg == 'wordlist' or arg.title == 'out':#paths have to be parsed differently
			debug2(f"{color_main}{arg} {color_reset}is set to {color_main}{getattr(args, arg).name}{color_reset}")
		else:
			debug2(f"{color_main}{arg} {color_reset}is set to {color_main}{getattr(args, arg)}{color_reset}")

	#rootcheck
	if os.geteuid() != 0:
		debug(f"{color_bad}You are not root or a privileged user. This doesn't let nmap analyze packets and can give worse results.\nIt is recommended to run with sudo or switch user")

	#getting url and ip of the target
	url = args.target
	try:
		ip = socket.gethostbyname(url)
	except socket.gaierror:
		debug(f"{color_bad}Host name or url not found!{color_reset}")
		sys.exit(1)


	#printing that info out
	ipinfostring = f"ip : {color_main}{ip}{color_reset}"
	urlinfostring = f"url: {color_main}{url}{color_reset}"

	os.system(f"toilet -f term -F border {ipinfostring}")
	os.system(f"toilet -f term -F border {urlinfostring}")



	debug1(f"Starting staged nmap scan on {ip} ...")
	newline(1)

	#different commands for each verbosity
	nmapverbositydict = {
		0 : f"nmap -sS -p- -v {ip} | grep -vE '^\Starting|Scanning|Completed|Initiating|is up|shown|report|Read|done|Raw packets sent'",
		1 : f"nmap -sS -p- -v {ip} | grep -vE '^\Starting|Scanning|Completed|Initiating|is up|shown|report|Read|done'",
		2 : f"nmap -sS -p- -v {ip} | grep -vE '^\Starting|Scanning|Completed|Initiating|shown|report|Read|done'",
		3 : f"nmap -sS -p- -v {ip}"
	}

	cmd = parsenmap(nmapverbositydict.get(args.verbose))

	#running the commands
	out_r, out_w = pty.openpty()
	debug3(f"Running command {cmd} ...\n")
	nmap_p1 = subprocess.Popen(cmd, shell=True, stdout=out_w)

	t_current_iterator = 0

	f = OutStream(out_r)
	while True:
		lines, readable = f.read_lines()
		if not readable:
			break
		for line in lines:
			if "Discovered" in line:
				debug(f"{main_inf}{color_good}{line}")
				port = numbers(line[21: 25: 1])

				#creating a thread
				t = Thread(target=handleport, args=[port])
				t.daemoen = True
				t.setName(f"Port {port}")
				threads.insert(t_current_iterator , t)
				threads[t_current_iterator].start()
				t_current_iterator += 1
			elif "down" in line:
				debug(main_inf + color_bad + line)
			elif "Raw packets sent:" in line:
				debug(f"{main_inf}{color_info}Done with scanning!\n{line}")
				break
			else:
				debug(main_inf + line)
		else:#else acts if the for loop hasnt been broke out of, so here it breaks out of both loops
			continue
		break

	for thread in threads:
		thread.join()
		debug(f"{color_good}{thread.getName()} Finished (main)")

		
		if args.verbose >= 1:#save a tiny bit of resources if debug is set to 0
			printProgress(threads=threads)
		
			

try:
	main()
except KeyboardInterrupt:
	debug(f"{color_main}See ya!")#always cool and needed
	try:
		sys.exit(0)
	except SystemExit:
		 os._exit(0)