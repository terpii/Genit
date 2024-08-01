from colorama import Fore, init
from colorama.ansi import Back
from lib.arg_init import args


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
	
	if args.output is not None:
		file = open(args.output.name, 'a')
		file.write(cmdoutput + color_reset + '\n')
		file.close()


color_main = Fore.MAGENTA;
color_reset = Fore.RESET + Back.RESET;
color_good = Fore.GREEN;
color_bad = Fore.RED;
color_info = Fore.LIGHTBLUE_EX;

