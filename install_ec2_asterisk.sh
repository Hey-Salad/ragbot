#!/bin/bash
###############################################################################
# Automated Asterisk Installation Script for AWS EC2
# Run this on your EC2 instance after launching
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Asterisk VoIP Server Installation for EC2     ║${NC}"
echo -e "${GREEN}║   Optimized for Voice AI Integration            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

ASTERISK_SIP_PASSWORD="${ASTERISK_SIP_PASSWORD:-$(openssl rand -hex 12)}"
ASTERISK_AMI_PASSWORD="${ASTERISK_AMI_PASSWORD:-$(openssl rand -hex 12)}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Get EC2 public IP
echo -e "${YELLOW}[1/10] Getting EC2 instance details...${NC}"
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
PRIVATE_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)
echo -e "${GREEN}✓ Public IP: $PUBLIC_IP${NC}"
echo -e "${GREEN}✓ Private IP: $PRIVATE_IP${NC}"

# Update system
echo -e "${YELLOW}[2/10] Updating system packages...${NC}"
apt-get update -qq
apt-get upgrade -y -qq
echo -e "${GREEN}✓ System updated${NC}"

# Install prerequisites
echo -e "${YELLOW}[3/10] Installing prerequisites...${NC}"
apt-get install -y -qq \
    build-essential \
    wget \
    libssl-dev \
    libncurses5-dev \
    libnewt-dev \
    libxml2-dev \
    linux-headers-$(uname -r) \
    libsqlite3-dev \
    uuid-dev \
    git \
    subversion \
    ffmpeg \
    python3-pip \
    python3-dev \
    fail2ban \
    ufw
echo -e "${GREEN}✓ Prerequisites installed${NC}"

# Download Asterisk
echo -e "${YELLOW}[4/10] Downloading Asterisk 20 LTS...${NC}"
cd /usr/src
if [ ! -f "asterisk-20-current.tar.gz" ]; then
    wget -q https://downloads.asterisk.org/pub/telephony/asterisk/asterisk-20-current.tar.gz
fi
tar -xzf asterisk-20-current.tar.gz
cd asterisk-20.*/
echo -e "${GREEN}✓ Asterisk downloaded${NC}"

# Install Asterisk dependencies
echo -e "${YELLOW}[5/10] Installing Asterisk dependencies...${NC}"
contrib/scripts/install_prereq install -y > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Configure Asterisk
echo -e "${YELLOW}[6/10] Configuring Asterisk...${NC}"
./configure --with-jansson-bundled > /dev/null 2>&1
echo -e "${GREEN}✓ Configured${NC}"

# Compile Asterisk
echo -e "${YELLOW}[7/10] Compiling Asterisk (this takes 10-15 minutes)...${NC}"
make -j$(nproc) > /dev/null 2>&1
echo -e "${GREEN}✓ Compiled${NC}"

# Install Asterisk
echo -e "${YELLOW}[8/10] Installing Asterisk...${NC}"
make install > /dev/null 2>&1
make samples > /dev/null 2>&1
make config > /dev/null 2>&1
ldconfig
echo -e "${GREEN}✓ Installed${NC}"

# Install audio files
echo -e "${YELLOW}[9/10] Installing audio files...${NC}"
apt-get install -y -qq \
    asterisk-core-sounds-en-wav \
    asterisk-core-sounds-en-gsm \
    asterisk-moh-opsound-wav
echo -e "${GREEN}✓ Audio files installed${NC}"

# Configure firewall
echo -e "${YELLOW}[10/10] Configuring firewall...${NC}"
ufw --force enable
ufw allow 22/tcp comment "SSH"
ufw allow 5060/udp comment "SIP"
ufw allow 10000:20000/udp comment "RTP"
echo -e "${GREEN}✓ Firewall configured${NC}"

# Create basic configuration
echo -e "${YELLOW}Creating basic Asterisk configuration...${NC}"

# SIP configuration
cat > /etc/asterisk/sip.conf <<EOF
[general]
context=default
allowguest=no
udpbindaddr=0.0.0.0:5060
tcpenable=yes
tcpbindaddr=0.0.0.0:5060

; NAT settings for AWS
nat=force_rport,comedia
externip=$PUBLIC_IP
localnet=172.31.0.0/16

; Security
alwaysauthreject=yes
allowoverlap=no
dtmfmode=rfc2833

; Codecs
disallow=all
allow=ulaw
allow=alaw
allow=gsm

; RTP settings
rtpstart=10000
rtpend=20000

; Test extension
[1000]
type=friend
secret=$ASTERISK_SIP_PASSWORD
host=dynamic
context=voice-ai-agent
EOF

# Dialplan configuration
cat > /etc/asterisk/extensions.conf <<EOF
[general]
static=yes
writeprotect=no

[voice-ai-agent]
exten => 1000,1,NoOp(Voice AI Agent)
    same => n,Answer()
    same => n,Wait(0.5)
    same => n,Playback(beep)
    same => n,Set(RECORDING_FILE=/var/spool/asterisk/recording/\${UNIQUEID}.wav)
    same => n,Record(\${RECORDING_FILE},3,60,q)
    same => n,NoOp(Recording saved to \${RECORDING_FILE})
    same => n,Playback(beep)
    same => n,Goto(1000,1)

; Echo test
exten => 9999,1,Answer()
    same => n,Playback(demo-echotest)
    same => n,Echo()
    same => n,Hangup()
EOF

# Manager interface
cat > /etc/asterisk/manager.conf <<EOF
[general]
enabled = yes
port = 5038
bindaddr = 0.0.0.0

[admin]
secret = $ASTERISK_AMI_PASSWORD
read = all
write = all
EOF

# HTTP server
cat > /etc/asterisk/http.conf <<EOF
[general]
enabled=yes
bindaddr=0.0.0.0
bindport=8088
enablestatic=yes
EOF

# Create recording directory
mkdir -p /var/spool/asterisk/recording
chown -R asterisk:asterisk /var/spool/asterisk/recording
chmod 755 /var/spool/asterisk/recording

# Configure Fail2Ban
cat > /etc/fail2ban/jail.local <<EOF
[asterisk]
enabled = true
port = 5060
protocol = udp
filter = asterisk
logpath = /var/log/asterisk/full
maxretry = 5
bantime = 3600
EOF

systemctl restart fail2ban

# Start Asterisk
echo -e "${YELLOW}Starting Asterisk...${NC}"
systemctl enable asterisk
systemctl start asterisk
sleep 3
echo -e "${GREEN}✓ Asterisk started${NC}"

# Install Python dependencies for AGI
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip3 install -q requests asterisk-ami
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Create info file
cat > /root/asterisk_info.txt <<EOF
╔══════════════════════════════════════════════════╗
║        Asterisk Installation Complete!           ║
╚══════════════════════════════════════════════════╝

Server Details:
--------------
Public IP:  $PUBLIC_IP
Private IP: $PRIVATE_IP

SIP Configuration:
-----------------
Server:   $PUBLIC_IP
Port:     5060
Username: 1000
Password: $ASTERISK_SIP_PASSWORD

Manager Interface (AMI):
-----------------------
Host:     $PUBLIC_IP
Port:     5038
Username: admin
Password: $ASTERISK_AMI_PASSWORD

Test Extensions:
---------------
1000 - Voice AI Agent (with recording)
9999 - Echo test

Useful Commands:
---------------
# Asterisk console
sudo asterisk -rvvv

# Reload config
sudo asterisk -rx "core reload"

# Show SIP peers
sudo asterisk -rx "sip show peers"

# Show channels
sudo asterisk -rx "core show channels"

# View logs
tail -f /var/log/asterisk/full

# Restart Asterisk
sudo systemctl restart asterisk

Next Steps:
----------
1. Test SIP connection with credentials above
2. Configure Raspberry Pi integration
3. Add SIP trunk for incoming calls
4. Set up AGI scripts for AI processing

Documentation:
-------------
/home/admin/ragbot/EC2_ASTERISK_SETUP.md
EOF

# Display info
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Installation Complete! ✓                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
cat /root/asterisk_info.txt
echo ""
echo -e "${YELLOW}Installation details saved to: /root/asterisk_info.txt${NC}"
echo ""
echo -e "${GREEN}Test your setup:${NC}"
echo -e "1. Configure SIP client with above credentials"
echo -e "2. Call extension 1000"
echo -e "3. Test echo: call 9999"
echo ""
echo -e "${YELLOW}Monitor:${NC} sudo asterisk -rvvv"
echo ""
