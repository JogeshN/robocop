import robot
from robot import libraries
from robot import robot_imports
from robot.api import ExecutionResult
from robot.api import TestData

def main():
    #Push required data in builtins
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option("-t", "--test", dest="testlist", help="Specify file path of TestList to be executed", metavar="path-to-file")
    parser.add_option("-b", "--browser", action="store", dest="browser")
    parser.add_option("-i", "--includetag", dest="testincludetags", default=False, help="Run tests of given tag only")
    parser.add_option("-e", "--excludetag", dest="testexcludetags", default=False, help="Exclude tests of given tag")
    parser.add_option("-r", "--rungiventests", dest="rungiventests", default=False, help="Execute only given test case from suite")
    parser.add_option("-m", "--randomize",action="store_true", dest="runrandomize", default=False, help="Randomizes the test execution order")
    parser.add_option("-f", "--exitonfailure",action="store_true", dest="exitonfailure", default=False, help="Exit suite if test failed")
    parser.add_option("-s", "--runsuite", action="store", dest="runsuitesetup", help="Run suite setup")
    parser.add_option("-g", "--debugfile", action="store_true", dest="debugfile", default=False, help="Create debug log file")
    parser.add_option("-u", "--baseurl", action="store", dest="baseurl")
    
    parser.add_option("-n", "--TestName", action="store", dest="test_name")
    parser.add_option("-M", "--MetaData", action="store", dest="metadata")
#     parser.add_option("-a", "--abortonfailure", action="store_true", dest="abortonfailure", default=False, help="Abort suite on first test failure ")

    global tr
    tr = os.environ["TESTROOT"].replace('\\', '/')

    from robot import pythonpathsetter
    pythonpathsetter.add_path(additional_python_path)
    robot.run(options.testlist,**runoptions)
    
    
if __name__ == "__main__":
    main() 
