#!/usr/bin/pythom

import os
import paramiko
import time
import cmd

class sshAgent(cmd.Cmd):
	def __init__(self):
		""" intitalise the ssh Agent """
		self.ssh= paramiko.SSHClient()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

	def connect(self,hostname='127.0.0.1',port=22,username='mininet',password='mininet'):
		""" take hostname , username and password as arg """
		return self.ssh.connect(hostname,port,username,password)

	def runCmd(self,cmd,timeout=1):
		""" run command and return after timeout """
		stdin,stdout,stderr = self.ssh.exec_command("cmd")
		time.sleep(timeout)
		return None

	def runCmdlines(self,cmd,timeout=10):
		""" run command and get command output 
		    break after if output is not there or timeout occur
		"""
		out = None
		stdin,stdout,stderr = self.ssh.exec_command(cmd)	
		out = stdout.readlines()
		return out
	
	def close():
		""" close the ssh connection """
		self.ssh.close()
		

if __name__=='__main__':
	sshAgent().cmdloop()
