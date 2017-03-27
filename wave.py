#!/usr/bin/env python
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

    It is assumed that all transactions MUST occur between an
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
import argparse
from transaction_type import Trans_Type
from worker import Worker
from transaction import Transaction
from position import Position
from __init__ import *

def get_type(type_str):
    if type_str == "LOA-START":
        ret = LOA_START
    elif type_str in ["Hire", "a-Hire"]:
        ret = HIRE
    elif type_str == "LOA_RETURN":
        ret = LOA_STOP
    elif type_str in ["Term", "z-Term"]:
        ret = TERM
    elif type_str in ["Job Change", "d-Job Change", "d-Hjob Change"]:
        ret = CHANGE_JOB
    elif type_str in ["g-Org Assignment", "Assign Org"]:
        ret = ORG_ASSN
    else:
        print("Error, unknown type {}".format(type_str))
        raise Exception
    return ret

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--header", action="store_true", help="Print out header column names", required=False)
    parser.add_argument("-o", "--output_file", default="./output.csv")
    parser.add_argument("-i", "--input_file", default="./combined.csv")
    mgroup = parser.add_mutually_exclusive_group()
    mgroup.add_argument("-w", "--worker", help="Output only transactions required for specified worker (employee id)",
            action="append", required=False)
    mgroup.add_argument("-s", "--sequence", help="Output only workers w max sequence > value", type=int)
    args = parser.parse_args()

    if args.header:
        print(Transaction.header())
        sys.exit(0)

    trans_list = []

    with open(args.input_file,"rU") as csvfile:
        ctr = 0
        reader = csv.reader(csvfile)
        for row in reader:
            #print row
            ctr += 1

            d = dt.datetime.strptime(row[1], "%m/%d/%Y").date()
            t = get_type(row[4])

            trans_list.append(Transaction(d, t, row[0], row[2], ctr))

        # Create my various lists / dicts
        worker_dict = {}
        position_dict = {}

        """
            Now that we have a list of transactions sorted by date / type
            we can go out and build out the extra data needed including:
                Worker objects
                Position objects
                from_position
            """
        for row in trans_list:

            # Employee should always exist, check
            if row.emp_id == "":
                print("Missing employee id")
                print(row)
                raise Exception
            elif row.emp_id not in worker_dict:
                worker_dict[row.emp_id] = Worker(row.emp_id)

            # Add the transaction to the worker, and the worker to the trans
            worker = worker_dict[row.emp_id]
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
                    if row.position_id == "Pre_Conversion":
                        position_dict[row.position_id] = Position(row.position_id, JOB_MGMT)
                    else:
                        position_dict[row.position_id] = Position(row.position_id)

                # Add the position to the transaction and the transaction to the
                # position
                position = position_dict[row.position_id]
                row.to_position = position
                position.add_transaction(row)

        """
            Now we have a full list of positions, workers and transactions.
            Go through each worker and fill in missing data:
                from_position for transactions
                to_position/from for LOA and TERM transactions
        """
        for w in worker_dict.values():
            w.validate()

        # Now go through each transaction and get pre-reqs
        if args.worker is None:
            for w in worker_dict.values():
                t = w.top_of_stack()
                if t is None:
                    continue
                t.return_pre_reqs()
        else: # Only calc for worker(s) (and related workers as needed) 
            for emp_id in args.worker:
                if emp_id not in worker_dict:
                    print("Worker with employee id = {} does not exist.".format(args.worker))
                    sys.exit(1)
                t = worker_dict[emp_id].top_of_stack()
                sub_list = t.return_pre_reqs()
                # Now we get all the workers in the list and print out all their transactions
                worker_set = set()
                for t in sub_list:
                    worker_set.add(t.worker)
                trans_list = []
                for w in worker_set:
                    trans_list += w.get_transactions()

        # Let's find some complicated worker transactions
        if args.sequence is not None:
            for w in worker_dict.values():
                if w.max_seq >= args.sequence:
                    t = w.top_of_stack()
                    print("Found top-level worker transaction w seq > {}".format(args.sequence))
                    print("Pre-reqs for {}".format(t))
                    for ts in t.return_pre_reqs():
                        print("\t{}".format(ts))

        with open(args.output_file, "w") as f:
            for t in trans_list:
                if t.valid:
                    f.write(t.output() + "\n")
            
