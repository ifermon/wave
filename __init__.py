"""
    Store module level imports, constants, and global variables
"""
from transaction_type import Trans_Type
from position import Position
from staffing_model import Staffing_Models
import logging

# Configure logging for everyone
logging.basicConfig(datefmt="%H:%M:%S", format="%(asctime)s %(message)s")
l = logging.getLogger()
l.setLevel(logging.CRITICAL)
debug = l.debug
info = l.info
error = l.error
stop_on_validation = False


# NOTE: Key to the below is the sequence. This should match the
# relative sequence in the implementation suite
HIRE = Trans_Type("Hire", 1, ["Hire", "a-Hire"])
CHANGE_JOB = Trans_Type("Job Change", 2, ["Job Change", "d-Job Change", "d-Hjob Change"])
ORG_ASSN = Trans_Type("Assign Org", 3, ["g-Org Assignment", "Assign Org"])
LOA_START = Trans_Type("LOA Start", 4, ["LOA-START", "LOA Start"])
LOA_STOP = Trans_Type("LOA Stop", 5, ["LOA_RETURN", "LOA Stop"])
TERM = Trans_Type("Term", 6, ["Term", "z-Term"])

PRE_HIRE = Position("Pre-Hire", Staffing_Models.JOB_MGMT)
JOB_MGMT_POS = Position("Job Management Position", Staffing_Models.JOB_MGMT)
TERMED_EMP = Position("Terminated", Staffing_Models.JOB_MGMT)
DUMMY = Position("Dummy", Staffing_Models.JOB_MGMT)

JOB_MGMT = Staffing_Models.JOB_MGMT
POSITION_MGMT = Staffing_Models.POSITION_MGMT
