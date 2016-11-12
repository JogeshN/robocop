*** Settings ***
Metadata	Version		2.0
Metadata	More Info	Ashish
Metadata	Executed At	${HOST}
Documentation 		Example suite
...			need to give some comments.

Library		OperatingSystem

Test Setup		Do Something		${MESSAGE}
Force Tags		example
Library			SomeLibrary
Test Timeout		2 minutes

*** Variables  ***
${MESSAGE}		Hello, world!

*** Test Cases  ***
Step 1. Add two numbers
	[Documentation]		Given I have Calculaator open
	...			When I add 2 and 40
	...			Then result should be 42

Step 2. Add Negative numbers
	[Documentation]	Given I have Calculator open
	...		When I add  1 and -2
	...		Then result should be 42


*** Keywords ***
Do Something
    [Arguments]		${args}
    Log 	"Today !!"   

