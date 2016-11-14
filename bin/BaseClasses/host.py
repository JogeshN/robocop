from  harness import cli
from  robot.utils import asserts
import  logging 
#ch = logging.StreamHandler()
logger = logging.getLogger(__name__)
#logger.addHandler(ch)
from robot.libraries.BuiltIn import BuiltIn
c = BuiltIn()

def verify_hostname(name):
	""" verify hostname"""
	host = cli.sshAgent()
	logger.info('started ssh agetn %s' % host)
	result = host.connect()
	c.log_to_console("A1")
	logger.info('connected the ssh agent, result %s' %result)
	hostname = host.runCmdlines('hostname')
	c.log_to_console("A2")
	print hostname
	print name
	logger.info('the output of command is %s' %hostname)
	if hostname[0].strip() == name:
		print("passed")
		logger.info("Passed the testcase passed.")
	else :
		logger.error("The testcase failed.")
		asserts.fail("fail")

#verify_hostname('mininet')	
