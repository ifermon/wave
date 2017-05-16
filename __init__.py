"""
    Store module level imports, constants, and global variables
"""
from transaction_type import Trans_Type
from position import Position
from staffing_model import Staffing_Models
from sequence import Sequence
import logging

# Configure logging for everyone
logging.basicConfig(datefmt="%H:%M:%S", format="%(asctime)s %(message)s")
l = logging.getLogger()
l.setLevel(logging.CRITICAL)
debug = l.debug
info = l.info
error = l.error
stop_on_validation = False

# Unique id generators for worker and position
worker_seq = Sequence("worker")
position_seq = Sequence("position")

# NOTE: Key to the below is the sequence. This should match the
# relative sequence in the implementation suite
HIRE = Trans_Type("Hire", 1, ["Hire", "a-Hire"])
CHANGE_JOB = Trans_Type("Job Change", 2, ["Job Change", "d-Job Change", "d-Hjob Change"])
ORG_ASSN = Trans_Type("Assign Org", 3, ["g-Org Assignment", "Assign Org"])
EFFECTIVE_DATED_COMP = Trans_Type("Effective Dated Comp", 4, ["Effective Dated Comp"])
REQ_COMP_CHANGE = Trans_Type("Request Compensation Change", 5, ["Request Comp Change"])
LOA_START = Trans_Type("LOA Start", 6, ["LOA-START", "LOA Start"])
LOA_STOP = Trans_Type("LOA Stop", 7, ["LOA_RETURN", "LOA Stop"])
TERM = Trans_Type("Term", 8, ["Term", "z-Term"])

PRE_HIRE = Position("Pre-Hire", Staffing_Models.JOB_MGMT)
JOB_MGMT_POS = Position("Job Management Position", Staffing_Models.JOB_MGMT)
TERMED_EMP = Position("Terminated", Staffing_Models.JOB_MGMT)
DUMMY = Position("Dummy", Staffing_Models.JOB_MGMT)

JOB_MGMT = Staffing_Models.JOB_MGMT
POSITION_MGMT = Staffing_Models.POSITION_MGMT
