#tools that can be installed via apt
sudo apt install python3 nmap nikto gobuster

cd /opt/
sudo git clone https://github.com/offensive-security/exploit-database
export PATH=/opt/exploit-database/:"${PATH}"