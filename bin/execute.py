import xml.etree.ElementTree as ET
import signal
import re
import datetime
import os,time,shutil,sys,fnmatch
import robot
from robot import libraries
from robot import robot_imports
import ConfigParser
from robot.api import ExecutionResult
from robot.api import TestData

def signal_handler(signal, frame):
    print 'You pressed Ctrl+C!'
    print 'check the precheck logs st precheck.html file on latest log in log folder.'
    sys.exit(0)

def _move_logs(testlistfile):
    testlistfile = os.path.basename(testlistfile).replace('.txt','')
    finallogpath = "%s-%s" % (testlistfile, time.strftime("%d%B%Y.%I%M%S"))
    print "finallogpath: %s" %finallogpath
    src = os.path.join(tr,'AutoBot\\Logs\\latest')
    dst = os.path.join(os.path.join(tr,'AutoBot\\Logs'),finallogpath)
    try:
        shutil.copytree(src, dst)
    except OSError as exc: # python >2.5
        print "Error copying/archiving logs..."
        
    return 1

def dump_suite_result():
    #filelist=re.findall(r"[\w.]+", testfilename)
    #testfilename=filelist[len(filelist)-2]
    src = os.path.join(tr,'AutoBot\\Logs\\latest')
    #dst = os.path.join(src,'')
    xmlfilepath=os.path.join(src,'output.xml')
    result = ExecutionResult(xmlfilepath)
    #result.configure(stat_config={'suite_stat_level': 2,'tag_stat_combine': 'tagANDanother'})
    stats = result.statistics
    print stats.total.critical.failed
    if stats.total.critical.failed>0:
        filepath=os.path.join(src,'jenkinsresult')
        file=open(filepath,'w')
        file.write('FAIL')
    else:
        filepath=os.path.join(src,'jenkinsresult')
        file=open(filepath,'w')
        file.write('PASS')

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

    (options, args) = parser.parse_args()
    print options
#     print options.testexcludetags
    print "testincludetags: %s" %options.testincludetags
    if not options.testlist and options.testplan:
        print "updating results"
        update_results(options.testplan)
        sys.exit()

    global tr
    tr = os.environ["TESTROOT"].replace('\\', '/')

    if not options.browser:
        browser = "ff"
    else:
        browser  = options.browser.lower()
#     server = resource_dict.get('server')
    if options.precheck:
        precheck_manager(options.testlist, type=options.precheck ,browser=browser)


    pybotcmd = "pybot -d " + os.path.join(tr,'Logs/latest')  

    runoptions = {}
    runoptions['outputdir'] = os.path.join(tr,'Logs/latest')

    # cleanup latest log folder
    try:
        shutil.rmtree(runoptions['outputdir'], ignore_errors=True)
        print "Cleanup latest log folder successful..."
    except:
        print "Warning: Cleanup latest log folder failed..."
    if not os.path.exists(runoptions['outputdir']):
        time.sleep(1)
        os.makedirs(runoptions['outputdir'])


    if not options.runsuitesetup:
        run_suite = 1
        pybotcmd = pybotcmd + "-vrun_suite:1 "
    else:
        run_suite  = options.runsuitesetup
        print "run_suite",run_suite
        pybotcmd = pybotcmd + "-vrun_suite:" + run_suite + " "

    if options.testincludetags:
        itags = ''
        ritags = ''
        if '[' in options.testincludetags:
            tags = options.testincludetags
            tags = tags.replace('[','')
            tags = tags.replace(']','')
            alltags = tags.split(',')
            for tag in alltags:
                itags = "-i " + tag + " "
                pybotcmd = pybotcmd + itags
                ritags = ritags + tag + 'OR'
            ritags = ritags[:-2]
        else:
            pybotcmd = pybotcmd + "-i " + options.testincludetags + " "
            ritags = options.testincludetags

    if options.testexcludetags:
        etags = ''
        retags = ''
        if '[' in options.testexcludetags:
            tags = options.testexcludetags
            tags = tags.replace('[','')
            tags = tags.replace(']','')
            alltags = tags.split(',')
            for tag in alltags:
                etags = "-e " + tag + " "
                pybotcmd = pybotcmd + etags
                retags = retags + tag + 'OR'
            retags = retags[:-2]
        else:
            pybotcmd = pybotcmd + "-e " + options.testexcludetags + " "
            retags = options.testexcludetags

    if options.rungiventests:
        tests = ''
        if '[' in options.rungiventests:
            giventests = options.rungiventests
            giventests = giventests.replace('[','')
            giventests = giventests.replace(']','')
            alltests = giventests.split(',')
            for t in alltests:
                tests = "-t " + '"%s"' %t + " "
                pybotcmd = pybotcmd + tests
            runmultiple = True
        else:
            pybotcmd = pybotcmd + "-t " + '"%s"' %options.rungiventests + " "
            runmultiple = False

    if options.runrandomize:
        pybotcmd = pybotcmd + "--randomize tests "

    if options.exitonfailure:
        pybotcmd = pybotcmd + "--exitonfailure "

    run_cmd = pybotcmd + options.testlist
#     print run_cmd
#     print tr
#     os.system(run_cmd)

    ### Uncomment the above two lines and comment the below code till robot.run() if you want to run using pybot

    if options.testincludetags:
        runoptions['include'] = ritags
    if options.testexcludetags:
        runoptions['exclude'] = retags
    if options.exitonfailure:
        runoptions['exitonfailure'] = options.exitonfailure
    if options.runrandomize:
        runoptions['randomize'] = 'tests'
    if options.debugfile:
        runoptions['debugfile'] = os.path.join(tr, 'robotdebug.log')
    if options.rungiventests and not runmultiple:
        runoptions['test'] = options.rungiventests
    
    if options.test_name:
        runoptions['name'] = options.test_name
        
    if options.metadata:
        runoptions['metadata'] = options.metadata
    
    try:
        os.system("regsvr32 /s tools/AutoItX3_x64.dll")
    except:
        pass
    #sys.path.insert(0, os.path.join(os.path.dirname(inSyncQA.__file__), "AutoBot", "Modules"))
    print "\nrunoptions for robot.run:\n%s" %runoptions
    robot.run(options.testlist, variable=['run_suite:%s' %run_suite], **runoptions)
    
    dump_suite_result()
    
    time.sleep(5)
    print "TESTRUN COMPLETED"
    print "Trying to copy/archive logs..."
    _move_logs(options.testlist)

    if options.testplan:
        update_results(options.testplan)

if __name__ == "__main__":
    main() 
