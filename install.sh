#tools that can be installed via apt
sudo apt install nmap
sudo apt install nikto
sudo apt install gobuster

cd /opt/
sudo git clone https://github.com/offensive-security/exploit-database
export PATH=/opt/exploit-database/:"${PATH}"