from  harness import cli
from  robot.utils import asserts

def verify_hostname(name):
	""" verify hostname"""
	host = cli.sshAgent()
	print "A"
	host.connect()
	print "A1"
	hostname = host.runCmdlines('hostname')
	print "A2"
	print hostname
	print name
	if hostname[0].strip() == name:
		print("passed")
	else :
		asserts.fail("fail")

#verify_hostname('mininet')	
