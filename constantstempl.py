ANNDIR = 'LDC2017E08-1/'
TOTAL_FILES = 10
DEV_FRACTION = 100

EVENTTYPES = {'Business' : 0,
         'Conflict' : 1,
         'Contact': 2,
         'Manufacture': 3,
         'Life' : 4,
         'Movement' : 5,
         'Personnel' : 6,
         'Justice' : 7,
         'Transaction' : 8,
         }

EVENTSUBTYPES = [['Start-Org', 'End-Org', 'Declare-Bankruptcy', 'Merge-Org'],
            ['Attack', 'Demonstrate'],
            ['Meet', 'Correspondence', 'Broadcast', 'Contact'],
            ['Artifact'],
            ['Be-Born', 'Marry', 'Divorce', 'Injure', 'Die'],
            ['Transport-Person', 'Transport-Artifact'],
            ['Start-Position', 'End-Position', 'Nominate', 'Elect'],
            ['Arrest-Jail', 'Release-Parole', 'Trial-Hearing', 'Sentence', 'Fine', 'Charge-Indict', 'Sue', 'Extradite', 'Acquit', 'Convict', 'Appeal', 'Execute', 'Pardon'],
            ['Transfer-Ownership', 'Transfer-Money', 'Transaction'],]