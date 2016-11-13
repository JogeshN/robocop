#!/usr/bin/pythom

import os
import paramiko
import time
import cmd
from logging import debug, error , info , warn

class sshAgent(cmd.Cmd):
	def __init__(self):
		""" intitalise the ssh Agent """
		self.ssh= paramiko.SSHClient()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		info('The ssh agent is started !!')

	def connect(self,hostname='127.0.0.1',port=22,username='mininet',password='mininet'):
		""" take hostname , username and password as arg """
		info('connecting to ssh agent')
		return self.ssh.connect(hostname,port,username,password)

	def runCmd(self,cmd,timeout=1):
		""" run command and return after timeout """
		info('The command %s is being executed' %cmd)
		stdin,stdout,stderr = self.ssh.exec_command(cmd)
		info("Sleeping for the timeout %s" %timeout)
		time.sleep(timeout)
		return None

	def runCmdlines(self,cmd,timeout=10):
		""" run command and get command output 
		    break after if output is not there or timeout occur
		"""
		out = None
		info("the cmommand %s is executed on ssh expect" %cmd)
		stdin,stdout,stderr = self.ssh.exec_command(cmd)
		info("getting the output from ssh.")	
		out = stdout.readlines()
		return out
	
	def close():
		""" close the ssh connection """
		info("closing the ssh agent.")
		self.ssh.close()
		

if __name__=='__main__':
	sshAgent().cmdloop()
