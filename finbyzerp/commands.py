# import click, os, sys, shlex
# import subprocess
# from subprocess import STDOUT, check_call, CalledProcessError

# @click.command('install-whatsapp')
# def install_whatsapp():
#     # cur_dir = os.getcwd() + "/../apps/finbyzerp/finbyzerp/webwhatsapi"
#     # os.chdir(cur_dir)

#     # os.system('sudo su')    
#     os.system("sudo apt  install firefox")
#     os.system("export GECKO_DRIVER_VERSION='v0.29.0'")
#     os.system("wget https://github.com/mozilla/geckodriver/releases/download/$GECKO_DRIVER_VERSION/geckodriver-$GECKO_DRIVER_VERSION-linux64.tar.gz")
#     os.system("tar -xvzf geckodriver-$GECKO_DRIVER_VERSION-linux64.tar.gz")
#     os.system("rm geckodriver-$GECKO_DRIVER_VERSION-linux64.tar.gz")
#     os.system("sudo cp geckodriver /usr/local/bin/")
#     os.system("chmod +x /usr/local/bin/geckodriver")
#     # os.system('sudo curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add')
#     # os.system('sudo echo "deb [arch=amd64]  http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list')
#     # os.system('sudo apt-get -y update')
#     # os.system('wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb')
#     # os.system('sudo apt install ./google-chrome-stable_current_amd64.deb')
#     # os.system('sudo wget https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip')
#     # os.system('sudo unzip chromedriver_linux64.zip')
#     # os.system('sudo mv chromedriver /usr/local/bin/chromedriver')
#     # os.system('sudo chown root:root /usr/local/bin/chromedriver')
#     # os.system("sudo rm chromedriver_linux64.zip")
#     # os.system('sudo chmod +x /usr/local/bin/chromedriver')


# commands = [install_whatsapp]
