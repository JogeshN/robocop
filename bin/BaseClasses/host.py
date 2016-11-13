from  harness import cli
from  robot.utils import asserts
from  logging import debug, error, info, warn

def verify_hostname(name):
	""" verify hostname"""
	host = cli.sshAgent()
	print "A"
	info('started ssh agetn %s' % host)
	result = host.connect()
	print "A1"
	info('connected the ssh agent, result %s' %result)
	hostname = host.runCmdlines('hostname')
	print "A2"
	print hostname
	print name
	info('the output of command is %s' %hostname)
	if hostname[0].strip() == name:
		print("passed")
		info("Passed the testcase passed.")
	else :
		error("The testcase failed.")
		asserts.fail("fail")

#verify_hostname('mininet')	
