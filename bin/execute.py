from inSyncLib import sfips #it will do initialisation required for FIPS

from inSyncQALib import ResMan
from inSyncQALib import QASuite
from inSyncQA import AutoBot
from inSyncQA.AutoBot import Modules
#from inSyncQA.AutoBot.Modules import Modules
from inSyncQA.AutoBot.Modules import Modules as m
from inSyncQA.TestModules import testraillib
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
# import AutoItLibrary

from inSyncQA.AutoBot.Modules.Resource import inSyncQAlogger, QAXMLRPC, config

# pybot akgsT$d Logs\latest -vbrowser:gc -vbaseurl:https://127.0.0.1/admin Tests\test_storage.txt
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

def update_results(testplan):
    try:
        t = testraillib.TestRail(project_name="Automation- inSyncQA")
        #tp = "Test_plan_5.6_CU_6"
        #run_name  = "test_backup_restore_non_data_driven_suite.txt"

        # find suite name from results, suite name should match a run in testrail
        tr = os.environ["TESTROOT"].replace('\\', '/')
        result_file = os.path.join(tr, 'Autobot', 'Logs','latest','output.xml')
        tree = ET.parse(result_file)
        parent = tree.getroot()
        # extract testname and results from output.xml
        tests = parent.findall(".//test")
        results = []
        for tst in tests:
            end_time = time.mktime(datetime.datetime.strptime(tst.find("status").attrib['endtime'], "%Y%m%d %H:%M:%S.%f").timetuple())
            starrt_time = time.mktime(datetime.datetime.strptime(tst.find("status").attrib['starttime'], "%Y%m%d %H:%M:%S.%f").timetuple())
            elapsed_time = int(end_time) - int(starrt_time)
            if elapsed_time == 0:
                elapsed_time = 1
            results.append((tst.attrib['name'],tst.find("status").attrib['status'],str(elapsed_time)+"s",tst.find("status").text))

        # extract suite name from output.xml
        s = parent.find(".//suite").attrib['source']
        suitename = os.path.basename(s)

        # find testrail run_id for this suite
        planid = t.get_plan_by_name(testplan)
        if not planid:
            print "No plan with name "+testplan+" in testrail "
            return
        plan_details =  t.get_plan_details(planid)
        runs = plan_details['entries']
        if len(runs)  == 0:
            print "No runs in test plan "+testplan+" in testrail "
            return
        rid = None
        for run in runs:
            if suitename in run['name']:
                #print len(run['runs'])
                rid = run['runs'][0]['id']
        if rid:
            # form a dictionary of test name and test id in given testrun
            tests_dict = t.get_test_dict(rid)

            # update results in testrail
            for test, result, elapsed,reason in results:
                print tests_dict[test], test, result, elapsed,reason
                t.update_test_result(tests_dict[test], result, elapsed,reason)
        else:
            print "No run with name "+suitename+" found in testrail"

    except Exception, fault:
        import traceback as tb
        print tb.print_exc()

def get_prerequisite_path(pattern):
    path, file = os.path.split(pattern)
    return os.path.join(path,'__prerequisites__.conf.sample')

def precheck(filename, tc, browser, fd):
    #print "Option parsed."
    from inSyncQA.AutoBot.Modules.Resource import Validateprerequisite
    obj = Validateprerequisite()

    #start a config parser
    Config = ConfigParser.ConfigParser()
    #Read the prerequisite file
    file_to_read = os.path.join(tr, filename)
    file_to_read = file_to_read.replace('\\', '/')
    #file_to_read = filename
    #print "file_to_read: %s" %str(file_to_read)
    Config.read(file_to_read)
    at=Config.sections()
    #print "at: %s" %str(at)
    d={}
    tc_dict={}
    for i in at:
        d[i]=dict((x,eval(y)) for x,y in Config.items(i))
    #print "d: %s" %str(d)
    #print "tc: %s" %str(tc)
    tc_dict = d.get(tc)
    #print "tc_dict: %s" %str(tc_dict)

    if tc_dict.get('testdata'):
        try:
            cp = ConfigParser.ConfigParser()
            path =  os.path.join(tr,'inSyncQAConfig/data_checksum.conf')
            cp.read(path)
            test_data_val = tc_dict.get('testdata')
            print test_data_val
            test_datas =  test_data_val.split(',')
            for test_data_folder in test_datas:
                #test_data_folder,test_data_client = retval.split(':')
                src_chksum = cp.get('md5',test_data_folder).strip()
                #print test_data_folder,test_data_client,src_chksum
                obj.validateTestdata(test_data_folder,src_chksum)
        except ValueError:
            print "[FAIL]  : The data is not clearly defined in data_checksum.comf file. Please add its md5 details."
            obj.error_list.append("* The data %s is not clearly defined in data_checksum.comf file. Please add its md5 details. *" %test_data_val)

    if tc_dict.get('syncsharecleanup'):
        #print "in Share cleanup"
        obj.syncShareCleanup()

    if tc_dict.get('minspacerequirementforlog'):
        obj.minSpaceRequirementForLog(tc_dict.get('minspacerequirementforlog'),tr)

    if tc_dict.get('proxyverification'):
        retval = obj.getProxyParameters()
        #print retval

    if tc_dict.get('browsercheck'):
        obj.browserVersionCheck(browser)

    if tc_dict.get('validatesportalcheck'):
        list_to_check = tc_dict.get('validatesportalcheck').split(',')
        obj.validateSportalCheck(list_to_check)

    if tc_dict.get('changecachecfgaddurl'):
        obj.ChangeCacheCfgAddUrl()

    if tc_dict.get('alreadycustomeroncloudcheck'):
        obj.alreadyCustomerOnCloudCheck(tc_dict.get('alreadycustomeroncloudcheck'))

    if tc_dict.get('desktopdatafoldercleanup'):
        obj.desktopDataFolderCleanup()

    if tc_dict.get('numdevices'):
        obj.validateClients(tc_dict.get('numdevices'))

    if tc_dict.get('numusersessions'):
        obj.validateUserSession(tc_dict.get('numusersessions'))

    if tc_dict.get('adconnector'):
        obj.validateADConnector()

    if tc_dict.get('cacheserver'):
        obj.validateCacheserver()

    if tc_dict.get('validatelicense'):
        list_to_check = tc_dict.get('validatelicense').split(',')
        obj.validateLicense(list_to_check)

    if tc_dict.get('mapi'):
        obj.validateMapi()

    if tc_dict.get('imd'):
        obj.validateIMD()

    if tc_dict.get('validateprofile'):
        for profile in tc_dict.get('validateprofile').split(','):
            obj.validateProfile(profile)

    if tc_dict.get('useremailmaxalias'):
        obj.validateUserEmailMaxAlias(tc_dict['useremailmaxalias'])

    if tc_dict.get('guestemailmaxalias'):
        obj.validateGuestEmailMaxAlias(tc_dict['guestemailmaxalias'])

    if tc_dict.get('adminemailmaxalias'):
        obj.validateAdminEmailMaxAlias(tc_dict['adminemailmaxalias'])

    if tc_dict.get('validatemapiprofile'):
        obj.validateMapiProfile('outlook')


    fd.write("<html><body>\n")
    if len(obj.pass_list) > 0:
        fd.write("######################################################\n")
        fd.write("<h2>Following Checks are passed Sucessfully.</h2>")
        fd.write('\n'.join(map(lambda i:"<li><font color='green'>"+i+"</font>",obj.pass_list)))

    if len(obj.error_list) > 0:
        print "\n\n"
        print "#########"
        print "Please fix following issues before retrying execution."
        print '\n'.join(map(lambda i:"<li><font color='red'>"+i+"</font>",obj.error_list))
        fd.write('\n')
        fd.write("<h2>Please fix following issues before retrying execution.</h2>")
        fd.write('\n'.join(map(lambda i:"<li><font color='red'>"+i+"</font>",obj.error_list)))
        fd.write('\n')


def precheck_manager(testlist,type,browser):
    signal.signal(signal.SIGINT, signal_handler)
    try:
        precheck_filepath = tr + "\\AutoBot\\Logs\\latest\\"
        precheck_file = precheck_filepath+'precheck.html'
        fp = open(precheck_file,'w')
        #The type of prequisite checks are required.
        if type == "SUITE":
            tc = os.path.basename(testlist)
            #find the root path for the testlist suite
            filename = get_prerequisite_path(testlist)
            #print filename,tc
            fp.write("<h2> %s precheck logs</h2>" %tc)
            precheck(filename,tc,browser,fp)
            fp.close()

        elif type == "FILE":
            #precheck(tc)
            fd = open(testlist, 'r')
            for line in fd.readlines():
                line = line.strip()
                #print "line : %s" %line
                filename = get_prerequisite_path(line)
                tc = os.path.basename(line)
                #print filename,tc
                fp.write("<h2> %s precheck logs</h2>" %tc)
                precheck(filename,tc,browser,fp)
            fp.close()
            sys.exit(1)

        else :
            pass

    except KeyboardInterrupt:
            print "Please check precheck.html for report."
            print "TESTRUN COMPLETED"
    finally:
        fp.close()


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
    parser.add_option("-c", "--prerequisite",action="store",dest="precheck", help="Verifies all prerequisites for test suite.")
    parser.add_option("-u", "--baseurl", action="store", dest="baseurl")
    parser.add_option("-p", "--testplan", action="store", dest="testplan")
    
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

    qasuite = QASuite.Suite("stress")
    server = qasuite.resman.allocateHost(ResMan.OS_ANY,
                                         ResMan.SERVER,
                                         mode = ResMan.ALLOC_SHR)

    if not options.browser:
        browser = "ff"
    else:
        browser  = options.browser.lower()
#     server = resource_dict.get('server')

    if server.server.getEdition().lower() == 'cloud':
        baseurl = "https://" + str(server.server.get_cloud_master_ip())
    else:
        baseurl  = "https://" + str(server.ip)

    print baseurl

    if options.precheck:
        precheck_manager(options.testlist, type=options.precheck ,browser=browser)


    #server = resource_dict.get('server')
    pybotcmd = "pybot -d " + os.path.join(tr,'AutoBot/Logs/latest') + " -vbrowser:" + browser + " -vbaseurl:" + baseurl + " "

    runoptions = {}
    runoptions['outputdir'] = os.path.join(tr,'AutoBot/Logs/latest')

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
    import inSyncQA
    sys.path.insert(0, os.path.join(os.path.dirname(inSyncQA.__file__), "AutoBot", "Modules"))
    print "\nrunoptions for robot.run:\n%s" %runoptions
    robot.run(options.testlist, variable=['baseurl:%s' %baseurl, 'browser:%s' %browser, 'run_suite:%s' %run_suite], **runoptions)
    
    dump_suite_result()
    
    time.sleep(5)
    print "TESTRUN COMPLETED"
    print "Trying to copy/archive logs..."
    _move_logs(options.testlist)

    if options.testplan:
        update_results(options.testplan)

if __name__ == "__main__":
    main() 
