🏛️ Cyber Banking Lab — Student Setup
Guide
This guide will help you set up and run the Procentric Cyber Bank vulnerability range on
your local Kali Linux machine using Docker.
📋 Prerequisites
Make sure your Kali Linux system is updated and connected to the internet. Since we are
using Docker, you do not need to manually install Python, Flask, or any database packages on
your host machine. 🛠️
Step-by-Step Installation
Step 1: Open the Terminal and Update Packages
Open your terminal in Kali Linux and run the following command to update your system's
package list:
sudo apt update
Step 2: Install Git and Docker
If you do not have Git or Docker installed on your system yet, run this command to install
both:
sudo apt install -y git docker.io
Step 3: Start the Docker Service
Kali Linux does not automatically start background services by default. Start Docker and
enable it to run using these commands:
sudo systemctl start docker
sudo systemctl enable docker
Step 4: Clone the Lab Repository
Download the lab codebase from GitHub directly to your machine:
git clone https://github.com/tibinjohn193-blip/procentric-cyber-bank.git
Step 5: Move Into the Project Directory
Navigate into the newly created folder:
cd procentric-cyber-bank
Step 6: Build the Docker Image
Compile the lab environment. CRITICAL: Do not forget the space and the period (.) at the
very end of this command. The dot tells Docker to look inside your current directory for the
setup files.
sudo docker build -t procentric-cyber-bank .
(Note: This process may take 1–3 minutes during the first setup while Docker downloads the
secure Python environment baseline.)
Step 7: Run the Cyber Bank Container
Launch the cyber range container in the background and map it to your local port 5000:
sudo docker run -d -p 5000:5000 --name cyber-bank-range procentric-cyber-
bank
🎯 How to Access the Lab
Once the container is running, open your web browser (Firefox/Chrome) inside Kali Linux
and go to the following URL:
👉 http://localhost:5000
From here, you can click "Open Account Online" to register your hacker profile, log in, and
view the 9 lab challenges!
🔄 Turning the Lab On/Off Later
If you close your machine or power down your VM, the lab will turn off. You do not need to
re-run the entire build process. Simply open your terminal and use these quick controls:
• To start the lab again:
sudo docker start cyber-bank-range
• To stop the lab temporarily:
sudo docker stop cyber-bank-range
• To check if the lab is currently running:
sudo docker ps
