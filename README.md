# Genit

Genit is a penetration testing tool that runs basic enumerations for you

This tool is made primarly for HackTheBox machines

## Installation

`git clone https://github.com/terpii/Genit.git`
`cd Genit`
`python3 genit.py --help`

On Kali Linux you should be able to run the tool right away

Otherwise run the builtin install.sh script:
`chmod +x install.sh`
`sudo ./install.sh`

## Usage

-h, --help            show this help message and exit

-t 127.0.0.1, --target 127.0.0.1 **(required)**
                        The target to scan
                     
-v 1, --verbose 1     a level of verbosity from 0 to 3, with 0 being very
                        quiet
                        
-noclear             will not clear your terminal on startup

-f, --fast            will try to focus on speed, faster but not as reliable

-w /usr/share/wordlists/rockyou.txt, --wordlist /usr/share/wordlists/rockyou.txt **(required)**
                        A wordlist to use when bruteforcing for directories on
                        websites
                        
-o path/to/outfile.txt, --output path/to/outfile.txt
                        A File to log all output to

example:
`python3 genit.py --target 127.0.0.1 --wordlist /home/terpi/wordlists/very-based-web-content-list.txt -o outlog.log`

If you're not sure which wordlist to use, https://github.com/danielmiessler/SecLists is a great source

## Contributions

This tool isn't even close to perfect and i will try to keep it updated
Pull requests are very welcome
