#!/usr/bin/env python3

"""
TODO:
1. Exceptions for login failure
2. Method to send lines of config

"""

from __future__ import print_function
import sys
import inspect
import re
import time
import datetime
import telnetlib
#from telnetlib import IAC, NOP

class IOSXR_rtelnet(object):
    def __init__(self, host=None, port=None, username=None, password=None, timeout=10, debug=False, code_debug=False):
        self.username = str(username)
        self.password = str(password)
        self.host = str(host)
        self.port = int(port)
        self.timeout = int(timeout)
        self.debug = bool(debug)
        self.code_debug = bool(code_debug)
        #self.is_login = False
        self.tn = telnetlib.Telnet()
        self.tnstore = []

    def open(self):
        """Open telnet connection to device"""
        try:
            self.tn.open(self.host, self.port, self.timeout)
        except Exception as err:
            print("ERROR: {0}".format(err))
        if self.debug:
            self.debug_on()
            self.code_debug = True
        return self.tn

    def close(self):
        """Close telnet connection to device"""
        self.tn.close()
        print("RTelnet connection closed")

    def check_alive(self):
        """Check if telnet connection is established to device; True=Connected, False=Disconnected"""
        try:
            if self.tn.sock:
                self.tn.sock.send(telnetlib.IAC + telnetlib.NOP)
                self.tn.sock.send(telnetlib.IAC + telnetlib.NOP)
                self.tn.sock.send(telnetlib.IAC + telnetlib.NOP)

                return True
            else:
                return False
        except:
            return False

    def debug_status(self):
        """Check if telnetlib debug is enabled, True = Enabled"""
        if self.debug:
            print("Debug is on")
        else:
            print("Debug is off")

    def debug_on(self):
        """Enable telnetlib debug: [set_debuglevel(100)]"""
        if not self.debug:
            self.tn.set_debuglevel(100)
            self.debug = True
            self.code_debug = True
            print("Debug is now enabled")
        else:
            print("Debug is already enabled")

    def debug_off(self):
        """ Disable telnetlib debug: [set_debuglevel(0)]"""
        self.tn.set_debuglevel(0)
        self.debug = False
        print("Debug is now disabled")

    def __bytedecode(self, byte):
        """ Decode Telnet read outputs as utf-8. By default telnetlib returns bytes. """
        self.byte = byte
        return self.byte.decode("utf-8")

    def __carriagereturn(self):
        """ Send a CR Enter """
        self.tn.write(b"\r\n")

    def read_last_line(self):
        """Read last line from Telnet"""
        RETRY = 5
        while RETRY > 0:
            tnread = self.__bytedecode(self.tn.read_very_eager())
            if tnread != "":
                self.tnstore.append(tnread)
            RETRY -= 1
        position = -1
        print(self.tnstore[-1])
        #split = re.split("\r*\n*", self.tnstore[-1])
        split = self.tnstore[-1].splitlines()
        while split[position] == "":
            print(position)
            position -= 1
        self.last_line = self.tnstore[-1].splitlines()[position]
        return self.last_line

    def __clearreadbuffer(self):
        """ Clear the Telnet session read buffer so that next read contains latest output """
        if self.code_debug:
            print("[DBEUG]: Entered __clearreadbuffer() method")
        RETRY = 5
        while RETRY > 0 and self.__bytedecode(self.tn.read_very_eager()) !="":#.decode("utf-8") != "":
            #self.tn.read_very_eager()
            self.read_last_line()
            RETRY -= 1
            #if RETRY < 0:
            #    break
            if self.code_debug:
                print("[DEBUG]: Telnet Read Buffer Cleared")
        #self.__carriagereturn()

    def login_status(self):
        self.is_login = False
        now = datetime.datetime.now()
        lastline = self.read_last_line()
        pattern = re.compile(r"^RP/\d/\d/CPU\d:\w+#")
        match = re.match(pattern, lastline)
        self.is_login = bool(match)
        return self.is_login

    def logged_in(self):
        """ Check if there is a login session to device. """
        if self.code_debug:
            print("[DEBUG]: Entered logged_in() method")
        self.is_login = False
        now = datetime.datetime.now()
        RETRY = 2
        #self.__clearreadbuffer()
        while RETRY > 0 and not self.is_login:

            tnread = self.__bytedecode(self.tn.read_until(b"#", timeout=2))
            #tnread = self.read_last_line()
            if tnread.strip().endswith("#") and ("RP" and "CPU" in tnread):
                self.is_login = True
            elif tnread.strip().endswith("Username:"):
                self.is_login = False
            else:
                self.__carriagereturn()
                self.is_login = False
            RETRY -= 1
        fname = inspect.currentframe().f_code.co_name
        print("%s: Finished in %s" %(fname,(datetime.datetime.now() - now)))
        return self.is_login

    def login(self):
        """Login to device console"""
        if self.code_debug:
            print("[DEBUG]: Running Login Method")
        now = datetime.datetime.now()
        RETRY = 5
        self.is_login = self.logged_in()

        self.__clearreadbuffer()
        while RETRY > 0 and not self.is_login:
            tnread = self.tn.read_until(b"Password:", timeout=2).decode("utf-8")
            if tnread.strip().endswith("Password:"):
                if self.code_debug:
                    print("[DEBUG]: login(PASSWORD)\n")                                   ###::: CODE DEBUG
                self.tn.write(self.password.encode('ascii') + b"\n")
                self.is_login = False
            elif tnread.strip().endswith("Username:"):
                if self.code_debug:
                    print("[DEBUG]: login(USERNAME)\n")                                   ###::: CODE DEBUG
                self.tn.write(self.username.encode('ascii') + b"\n")
                self.is_login = False
            elif ("RP" and "CPU") in tnread and tnread.strip().endswith("#"):
                self.is_login = True
                print("Login successful")
                if self.code_debug:                                      ###:: DEBUG
                    print("[DEBUG]: login(Logged In)\n")
                break
            else:
                if self.code_debug:
                    print("[DEBUG]: login(Not Logged In)\n")                                       ###::: CODE DEBUG
                self.tn.write(b"\r\n")
            RETRY -= 1
        else:
            print("An existing login session was detected")
        fname = inspect.currentframe().f_code.co_name
        print("%s: Finished in %s" %(fname,(datetime.datetime.now() - now)))
        #if self.is_login:
        #    print("Login successful")
        return self.is_login

    def logout(self):
        """ Logout from device. Reverse Telnet connection is still up and brings back to Authentication prompt"""
        self.tn.write(b"end\n\nexit\n\n")
        self.is_login = False
        print("Logged out of device")
        return self.is_login

    def cryptokeygen(self, overwrite=False):
        """ Generate the_default crypto keys to allow SSH connections etc. """
        now = datetime.datetime.now()
        command = str("crypto key generate rsa")
        if not self.logged_in():
            self.login()
        self.cryptokey_exist = False
        counter = 1
        while not self.cryptokey_exist:
            tnread = self.tn.read_until(b"#", timeout=2).decode("utf-8")
            if ("RP" and "CPU") in tnread and tnread.strip().endswith("#"):
                self.tn.write(command.encode('ascii') + b"\n")
                time.sleep(0.5)
                tnreadcrypto = self.tn.read_very_eager().decode("utf-8")
                if "replace" and "yes/no" in tnreadcrypto:
                    if overwrite:
                        print("OVERWRITING")                                ###::: CODE DEBUG
                        self.tn.write(b"yes\n")
                        time.sleep(0.1)
                        self.__carriagereturn()
                    else:
                        if self.code_debug:
                            print("\n[DEBUG]: QUIT OVERWRITE")
                        self.tn.write(b"no\n")
                else:
                    self.tn.write(b"\n")
                time.sleep(0.1)
                self.cryptokey_exist = True
            else:
                self.__carriagereturn()
            counter += 1
            if counter > 50:
                break
        fname = inspect.currentframe().f_code.co_name
        print("%s: Finished in %s" %(fname,(datetime.datetime.now() - now)))
        return self.cryptokey_exist

    def rootusercreate(self):
        """Create root-system user on IOSXR"""
        print("Running rootusercreate method")              ###:: CODE DEBUG
        now = datetime.datetime.now()
        #self.usercreated = False
        secretdone = False
        self.usercreated = self.login()
        if self.usercreated:
            print("ROOT SYSTEM USER ALREADY EXISTS")
        RETRY = 5

        self.__clearreadbuffer()
        while RETRY > 0 and not self.usercreated:

            tn_read = self.tn.read_until(b"Enter Secret Again:", timeout=2).decode("utf-8")
            #if "Enter secret again" in tn_read:
            if tn_read.strip().endswith("Enter secret again:"):
                print("SECRET AGAIN")                                     ###::: CODE DEBUG
                self.tn.write(self.password.encode('ascii') + b"\n")
                secretdone = True
                time.sleep(0.1)
            elif tn_read.strip().endswith("Enter secret:"):
                print("SECRET")                                             ###::: CODE DEBUG
                self.tn.write(self.password.encode('ascii') + b"\n")
            elif "root-system username:" in tn_read:
                print("ROOT-SYSTEM USERNAME")                               ###::: CODE DEBUG
                tn_read_new = tn_read
                if tn_read_new.strip().endswith("root-system username:"):
                    self.tn.write(self.username.encode('ascii') + b"\n")
                else:
                    self.__carriagereturn()
            elif tn_read.strip().endswith("Username:"):
                print("USERNAME detected")
                if secretdone:
                    print("ROOT-SYSTEM USER CREATED")
                else:
                    print("ROOT-SYSTEM USER ALREADY PRESENT")
                self.usercreated = True
            else:
                print("ELSE")
                self.__carriagereturn()
                time.sleep(0.1)
            RETRY -= 1
            print(RETRY)
        if self.logged_in():
            self.logout()
        fname = inspect.currentframe().f_code.co_name
        print("%s: Finished in %s" %(fname,(datetime.datetime.now() - now)))
        return self.usercreated

    def check_config_mode(self):
        """ Check if in config mode. """
        if self.code_debug:
            print("[DEBUG]: Entered check_config_mode() method")
        self.config_mode = False
        now = datetime.datetime.now()
        RETRY = 3
        #self.__clearreadbuffer()
        while RETRY > 0 and not self.config_mode:
            #tnread = self.__bytedecode(self.tn.read_until(b"#", timeout=2))
            tnread = self.read_last_line()
            if tnread.strip().endswith("#") and ("RP" and "CPU" and "config" in tnread):
                if self.code_debug:
                    print("[DEBUG]: check_config_mode(IF CONDITION)")
                self.config_mode = True
            else:
                if self.code_debug:
                    print("[DEBUG]: check_config_mode(ELSE CONDITION)")
                #self.__carriagereturn()
                self.config_mode = False
            RETRY -= 1
        fname = inspect.currentframe().f_code.co_name
        print("%s: Finished in %s" %(fname,(datetime.datetime.now() - now)))
        return self.config_mode

    def enter_config(self, exclusive=False):
        """Enter configuration mode"""
        self.config_mode = False
        if exclusive:
            cmd = str("configure exclusive")
        else:
            cmd = str("configure terminal")

        if not self.logged_in():
            print("User is not logged in. User needs to login first")
        elif self.check_config_mode():
            print("Already in config mode")
            self.config_mode = True
        else:
            print("Entering %s mode" %cmd)
            self.tn.write(cmd.encode('ascii') + b"\n")
            self.config_mode = True
        return self.config_mode

    def exit_config(self):
        """Exit configuration mode"""
        self.config_mode = self.check_config_mode()
        if self.config_mode:
            self.tn.write(b"end\n")
            time.sleep(0.5)
            last_line = self.read_last_line()
            if "cancel" in last_line:
                self.tn.write(b"no\n")
            self.config_mode = self.check_config_mode()
        else:
            print("Not in config mode")
        return self.config_mode

    def config_diff(self):
        """Show config diff: 'show commit changes diff' """
        self.config_mode = self.check_config_mode()
        cmd = str("show commit changes diff")
        if self.config_mode:
            self.__clearreadbuffer()
            self.tn.write(cmd.encode('ascii') + b"\n")
            time.sleep(0.5)
            tnread = self.__bytedecode(self.tn.read_very_eager())
            print(tnread)
        else:
            print("Not in config mode")
