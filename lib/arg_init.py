import argparse


parser = argparse.ArgumentParser("A startup enumeration tool for penetration testing purposes")
parser.add_argument("-t", '--target' , metavar='127.0.0.1', help="The target to scan", dest="target", required=True)
parser.add_argument("-v", '--verbose', metavar='1', default="1" , help="a level of verbosity from 0 to 3, with 0 being very quiet", choices=range(4), type=int, dest="verbose")
parser.add_argument('--noclear', action='store_true', dest='noclear', help="will not clear your terminal on startup")
parser.add_argument("-f", "--fast", action='store_true', dest='fast', help="will try to focus on speed, faster but not as reliable")
parser.add_argument('-w', '--wordlist', metavar='/usr/share/wordlists/rockyou.txt', dest='wordlist', help='A wordlist to use when bruteforcing for directories on websites' , required=True , type=argparse.FileType('r'))
parser.add_argument('-o', '--output', metavar='path/to/outfile.txt', dest='output', help='A File to log all output to', type=argparse.FileType('w', encoding='UTF-8'))

args = parser.parse_args()


