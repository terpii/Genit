#!/bin/python3

import argparse
import errno
import os
import pty
import re
import requests
import socket
import subprocess
import sys
from threading import Thread
from urllib.parse import urlparse

from lib.debugging import *
from lib.arg_init import *
from lib.add_to_host import *
from lib.outstream import *
from lib.port_tools.web import *


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



def handleweb(port, protocol):
	debug2(f"handling web on port {port}...")

	threadinfo = f'{color_main}[{port},web]{color_reset}'
	threads = []
	
	# check hostname for htb and add it to the hostfile
	hasdomain = False
	response = requests.get(f'{protocol}://{args.target}:{port}', allow_redirects=False)
	try:
		domain = response.headers['Location']

		if 'https' in domain:#incase it redirects from http to https
			protocol = 'https'
		domain = re.search(fr'{protocol}://(.*)/', domain).group(1)
		debug(f'{threadinfo}Found domain {domain}, adding to /etc/hosts')
		add_to_host_file(args.target, domain)
		hasdomain = True
	except KeyError:
		domain = args.target

	nikto_t = Thread(target=runnikto, args=[domain,port])
	nikto_t.daemon = True
	nikto_t.name = f"nikto on port {port}"
	threads.insert(-1, nikto_t)
	threads[threads.index(nikto_t)].start()

	gobuster_t = Thread(target=rungobuster, args=[protocol,domain,port])
	gobuster_t.daemon = True
	gobuster_t.name = f"gobuster on port {port}"
	threads.insert(-1, gobuster_t)
	threads[threads.index(gobuster_t)].start()
	
	if hasdomain:
		subdomain_t = Thread(target=enum_subdomains, args=[protocol,domain,port])
		subdomain_t.daemon = True
		subdomain_t.name = f"gobuster on port {port}"
		threads.insert(-1, subdomain_t)
		threads[threads.index(subdomain_t)].start()

	#waiting for threads to finish
	for thread in threads:
		thread.join()
		printProgress(threads)
	

#doing scripts for a port
def handleport(port):
	debug2(f"Starting handling on port {color_main}{port}")
	
	threads = []

	threadinfo = f'{color_main}[{port}]{color_reset}'

	#different commands for each verbosity
	nmapcmds = {
		0 : f"nmap -sC -sV  -p {port} {args.target}",
		1 : f"nmap -sC -sV  -p {port} {args.target}",
		2 : f"nmap -sC -sV -v -p {port} {args.target} | grep -vE '^\\Host is up|Read data files from|Service detection performed|Initiating|Completed|adjust_timeouts2|Discovered open port'",
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
					version = version.replace('(','').replace(')','')#fixes issue with openssh version string
					break
				except (TypeError, ValueError):
					pass
		#this solution might break if a service is named g4ming or something like that

	else:
		main_service = service.replace("?", "")#nmap can be unsure of services, and marks that with ?. This could mess up our search so we remove it

	#handling websites
	if 'http' in portdetails.lower():
		protocol = 'http'
		if 'https' in portdetails.lower():
			protocol = 'https'
		thread = Thread(target=handleweb, args=[port,protocol])
		thread.daemon = True
		thread.name = f"web on port {port}"
		threads.insert(-1, thread)
		threads[threads.index(thread)].start()
		#we dont need the variable anymore, its in the array
		del thread

	debug2(f"{threadinfo}Identified service: {main_service} {version}")

	#searching for exploits using searchsploit
	#theres lots of repetition here and im too lazy to fix
	if version != "":
		debug(f"{threadinfo}{color_info}Duckduckgo search page: https://duckduckgo.com/?q={main_service}+{version}+vulnerability")

		debug3(f"{threadinfo}Running command 'searchsploit {main_service} -v {version}'....")
		expl_proc = subprocess.Popen(f"searchsploit {main_service} -v {version}", stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True)

		(output, err) = expl_proc.communicate()

		expl_proc_status = expl_proc.wait()

		expl_count = 0

		for expl in output.decode().split("\n"):
			if not (" | " and "/" in expl):
				continue
			expl_count += 1
			
			if expl_count > 5:#concat to only 5 exploits
				continue

			debug(f'{threadinfo}{color_good}Exploit found: {expl}')

		if expl_count > 0:
			debug1(f"{threadinfo}{color_info}{expl_count} Exploits found, 5 have been shown")
		else:
			debug1(f"{threadinfo}{color_info}No exploits found")
	else:
		debug(f"{threadinfo}{color_info}Duckduckgo search page: https://duckduckgo.com/?q={main_service}+vulnerability")
		debug3(f"{threadinfo}Running command 'searchsploit {main_service}'....")

		expl_proc = subprocess.Popen(f"searchsploit '{main_service}'", stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True)

		(output, err) = expl_proc.communicate()

		expl_proc_status = expl_proc.wait()

		expl_count = 0

		for expl in output.decode().split("\n"):
			if not (" | " and "/" in expl):
				continue
			expl_count += 1

			if expl_count > 5:#concat to only 5 exploits
				continue

			debug(f'{threadinfo}{color_info}Exploit found: {expl}')

		if expl_count > 0:
			debug1(f"{threadinfo}{color_info}{expl_count} Exploits found, 5 have been shown")
		else:
			debug1(f"{threadinfo}{color_info}No exploits found")

	#wait for threads to finish
	for thread in threads:
		thread.join()
		debug1(threadinfo + thread.name + ' Finished')
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
		0 : f"nmap -sS -p- -v {ip} | grep -vE '^\\Starting|Scanning|Completed|Initiating|is up|shown|report|Read|done|Raw packets sent'",
		1 : f"nmap -sS -p- -v {ip} | grep -vE '^\\Starting|Scanning|Completed|Initiating|is up|shown|report|Read|done'",
		2 : f"nmap -sS -p- -v {ip} | grep -vE '^\\Starting|Scanning|Completed|Initiating|shown|report|Read|done'",
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
				t.name = f"Port {port}"
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
		debug(f"{color_good}{thread.name} Finished (main)")

		
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
