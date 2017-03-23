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
import csv
import sys
import datetime as dt
from transaction_type import Trans_Type
from worker import Worker
from transaction import Transaction
from position import Position
from __init__ import *

def get_type(type_str):
    if type_str == "LOA-START":
        ret = LOA_START
    elif type_str == "Hire":
        ret = HIRE
    elif type_str == "LOA_RETURN":
        ret = LOA_STOP
    elif type_str == "Term":
        ret = TERM
    elif type_str == "Job Change":
        ret = CHANGE_JOB
    elif type_str == "Assign Org":
        ret = ORG_ASSN
    else:
        print("Error, unknown type {}".format(type_str))
        raise Exception
    return ret

if __name__ == "__main__":

    trans_list = []

    with open("./combined.csv","r") as csvfile:
        ctr = 0
        reader = csv.reader(csvfile)
        for row in reader:
            print row
            ctr += 1

            d = dt.datetime.strptime(row[1], "%m/%d/%y").date()
            t = get_type(row[4])

            trans_list.append(Transaction(d, t, row[0], row[2], ctr))
            if ctr > 180:
                break

        # Create my various lists / dicts
        worker_dict = {}
        position_dict = {}
        change_job_waves = []
        org_assignment_waves = []
        hire_waves = []
        termination_waves = []
        loa_waves = []

        print
        print Transaction.header()
        """
            Now that we have a list of transactions sorted by date / type
            we can go out and build out the extra data needed including:
                Worker objects
                Position objects
                from_position
            """
        for i in range(20):
            print trans_list[i]
            row = trans_list[i]

            # Employee should always exist, check
            if row.emp == "":
                print("Missing employee id")
                print(row)
                raise Exception
            elif row.emp not in worker_dict:
                worker_dict[row.emp] = Worker(row.emp)

            # Add the transaction to the worker, and the worker to the trans
            worker = worker_dict[row.emp]
            row.worker = worker
            worker.add_transaction(row)

            # Now check position
            if row.position_id == "" and row.ttype in [
                        HIRE, CHANGE_JOB, ORG_ASSN]:
                    print("Missing position ID where required")
                    print(row)
                    raise Exception
            # LOAs, TERMS don't have positions, we'll fix later
            elif row.position_id != "":
                if row.position_id not in position_dict:
                    position_dict[row.position] = Position(row.position)

                # Add the position to the transaction and the transaction to the
                # position
                position = position_dict[row.position]
                row.to_position = position
                position.add_transaction(row)

        """
            Now we have a full list of positions, workers and transactions.
            Go through each worker and fill in missing data:
                from_position for transactions
                to_position/from for LOA and TERM transactions
        """
        for i in range(20):
            w = trans_list[i].worker
            w.validate()

            print trans_list[i]

        sys.exit()


        for row in trans_list:
            # If no position, find it
            if row[2] == "":
                print("No position")

