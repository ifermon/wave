"""
    This program reads a simple csv files containing the following fields:
        date, employee id, type, position id

    Types are the following:
        Job Change
        Org Assignment
        Hire
        LOA Start
        LOA Return
        Terminate

    It is assumed that all transactions MUST occurr between an 
    Hire and Termination event for any given employee

    If position id does not exist the program will look up the last 
    position for that employee and raise an exception if no position is found

    Go through file
    sort by date
    for each record
    if employee doesn't exist, create it
    if position doesn't exist, create it

"""
from transaction_type import Trans_Type
from position import Position
from staffing_model import Staffing_Models

HIRE = Trans_Type("Hire", 1)
CHANGE_JOB = Trans_Type("Job Change", 2)
ORG_ASSN = Trans_Type("Assign Org", 3)
LOA_START = Trans_Type("LOA Start", 4)
LOA_STOP = Trans_Type("LOA Stop", 5)
TERM = Trans_Type("Term", 6)


PRE_HIRE = Position("Pre-Hire", Staffing_Models.JOB_MGMT)
JOB_MGMT_POS = Position("Pre-Hire Job Management Position", Staffing_Models.JOB_MGMT)
TERMED_EMP = Position("Terminated", Staffing_Models.JOB_MGMT)

JOB_MGMT = Staffing_Models.JOB_MGMT
POSITION_MGMT = Staffing_Models.POSITION_MGMT
