====================================================================
PROCENTRIC CYBER BANK LAB - STUDENT SETUP GUIDE
====================================================================

Prerequisites:
Make sure your Kali Linux/Parrot OS system is updated and connected to the internet.

Step-by-Step Installation:

Step 1: Open Terminal and Update System Package List
---------------------------------------------------
sudo apt update

Step 2: Install Git and Docker Infrastructure
--------------------------------------------
sudo apt install -y git docker.io

Step 3: Fix AppArmor Policies and Start Docker Service
-----------------------------------------------------
Kali Linux/Parrot OS may restrict container initialization. Run these commands to unmask and start Docker cleanly:
sudo systemctl unmask docker
sudo systemctl start docker
sudo systemctl enable docker

Step 4: Clone the Lab Repository
--------------------------------
git clone https://github.com/tibinjohn193-blip/procentric-cyber-bank.git

Step 5: Navigate Into the Project Directory
-------------------------------------------
cd procentric-cyber-bank

Step 6: Build the Future-Proof Docker Image
-------------------------------------------
Compile the lab environment (Do not forget the period "." at the end):
sudo docker build -t procentric-cyber-bank .

Step 7: Run the Cyber Bank Range Container
-----------------------------------------
Launch the container with continuous auto-restart safety parameters:
sudo docker run -d -p 5000:5000 --name cyber-bank-range --restart unless-stopped procentric-cyber-bank

--------------------------------------------------------------------
HOW TO ACCESS AND SOLVE THE LAB
--------------------------------------------------------------------
1. Open your Web Browser and go to: http://localhost:5000
2. Click "Open Account Online" to register your student profile, then log in.
3. Click on the "🎯 View Lab Challenges" button to see the 9 cybersecurity tasks.
