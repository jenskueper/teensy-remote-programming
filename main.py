# lib from https://sourceforge.net/projects/pywin32/ or pip instal pypiwin32
# code originally from http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html

import os
import re
import win32file
import win32con
import pysftp # https://pypi.python.org/pypi/pysftp or pip install pysftp
import paramiko
import time

# arduino build path
# see here for how to change build path: http://forum.arduino.cc/index.php?topic=114503.msg905040#msg905040 
BUILD_PATH = "J:\\Desktop\\teensy\\builds\\"
ARDUINO_REGEX = '^.*\.ino\.hex$'
MCU = 'mk20dx256' # Teensy 3.1/3.2, see https://www.pjrc.com/teensy/loader_cli.html for all mcu types

# ssh settings
HOST = '192.168.178.30'
USERNAME = 'pi'
PASSWORD = 'x'
REMOTE_PATH = '/home/pi/teensy_loader_cli-master/'
HEX_LOCATION = '/home/pi/teensy_loader_cli-master/hex_files/'

hex_pattern = re.compile(ARDUINO_REGEX)

# Thanks to Claudio Grondi for the correct set of numbers
FILE_LIST_DIRECTORY = 0x0001
BUILD_PATH = "J:\\Desktop\\teensy\\builds\\"

hDir = win32file.CreateFile (
  BUILD_PATH,
  FILE_LIST_DIRECTORY,
  win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
  None,
  win32con.OPEN_EXISTING,
  win32con.FILE_FLAG_BACKUP_SEMANTICS,
  None
)
while 1:

  # only watch for last_write changes to avoid multiple events for the same file
  results = win32file.ReadDirectoryChangesW (
    hDir,
    1024,
    True,
     win32con.FILE_NOTIFY_CHANGE_LAST_WRITE,
    None,
    None
  )
  for action, file in results:
    full_filename = os.path.join (BUILD_PATH, file)
    if(hex_pattern.match(file) and action == 3): # check if file was updated

      # upload .hex file to pi
      filename = 'upload_' + str(int(time.time() * 100.0)) + '.hex'
      with pysftp.Connection(HOST, username=USERNAME, password=PASSWORD) as sftp:
        sftp.put(full_filename, HEX_LOCATION + filename)
      sftp.close()

      # execute teensy_loader_cli remotely to flash hex to teensy
      client = paramiko.SSHClient()
      client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      client.connect(HOST, username=USERNAME, password=PASSWORD)
      # sudo (root) is required!
      stdin, stdout, stderr = client.exec_command('sudo ' + REMOTE_PATH + 'teensy_loader_cli -s -mmcu=' + MCU + ' ' + HEX_LOCATION + filename)
      client.close()