"""
    Store module level imports, constants, and global variables
"""
from transaction_type import Trans_Type
from position import Position
from staffing_model import Staffing_Models

# NOTE: Key to the below is the sequqnce. This should match the
# relative sequqnce in the implementation suite
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
