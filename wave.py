#!/usr/bin/env python
"""
    This is the controller for the module.
    Built using Python 2.7.3, but should work with 3.x
    Requires enum (either with 3.x or the backport for 2.7)

    Module level variables / constants are outlined in __init__.py

    This module takes a list of transactions as input files and generates
    the sequencing for loading those transactions into Workday.

    Overall flow:
    Process command line arguments
    Open the transaction file(s)
    As it reads the file, it maps the transaction type using _get_type()
    Read the data, creating Transaction objects for each line
        ** we break out the creation of Transactions from Workers and
        Positions for clarity, accepting the performance hit
        It would be faster to do it all at once

    Now loop through each transaction and create Workers and
    Positions as needed. add the Transaction to the Worker and
    Position objects

    Now that the Transactions, Workers and Postions are all created, go through
    and perform validations (e.g. filling in from_position, or making sure
    that a worker is hired before they have a job change)

    Now that we have all the required data, and we have removed invalid transactions,
    for each worker, start at top of stack transaction for each worker (most recent one)
    and derive the list of pre-requisites. This should get you pre-requisites
    for every valid transaction

    Finally, generate output as specified in the program invocation

    Files need to be in the following excel csv format:
    employee id, event date, position id, <unused>, transaction type

    TODO: Add ability to intake a unique id for each line to allow reference
        between generated files and source data
    TODO: Add ability to generate files by wave, type, or both
    TODO: Add a nice, indented output for all worker transactions for a given worker
    TODO: Add ability to include row headers in command line (which position)
    TODO: Fix print headers option
    TODO: Add a verbose option to print out progress
"""
import csv
import sys
import datetime as dt
import argparse
from worker import Worker
from transaction import Transaction
from __init__ import *

# Specify the indexed location for each field in input files:
# Ex: EMP_123, 3/4/2010, HIRE, POS_1, 12345
# EMP_123 is index 0, effective date is index 1, etc
EMP_ID_INDEX = 0
POSITION_ID_INDEX = 2
EFFECTIVE_DATE_INDEX = 1
TRANS_TYPE_INDEX = 4

def _get_type(type_str):
    """ Map values in file for transaction type to supported transactions """
    ret = Trans_Type.get_type(type_str)
    if ret == None:
        print("Error, unknown type {}".format(type_str))
        raise Exception
    return ret

if __name__ == "__main__":

    # Process command line arguments
    parser = argparse.ArgumentParser(description=("This module takes a list of transactions"
            " as input files and generates the sequencing for loading those "
            "transactions into Workday. \n"
            "Files need to be in the following excel csv format:"
            "employee id, event date, position id, <unused>, transaction type"))
    parser.add_argument("--print-header", action="store_true", help="Print out header column names", required=False)
    parser.add_argument("--ignore-rows", help="Ignore first n rows of input file")
    parser.add_argument("--indexes", action="store_true", help="Print out column indexes for csv files")
    parser.add_argument("-o", "--output_file", default="./output.csv")
    parser.add_argument("-t", "--test", action="store_true", help="Print out first line of file with field mapping")
    parser.add_argument("-i", "--input_file", action="append", default=["./combined.csv",],
            help="Input file - multiple files may be specified")
    mgroup = parser.add_mutually_exclusive_group()
    mgroup.add_argument("-w", "--worker", help="Output only transactions required for specified worker (employee id)",
            action="append", required=False)
    mgroup.add_argument("-s", "--sequence", help="Output only workers w max sequence > value", type=int)
    args = parser.parse_args()

    # Print out index positions
    if args.indexes:
        d = dict((name, eval(name)) for name in ["EMP_ID_INDEX", "POSITION_ID_INDEX",
                "EFFECTIVE_DATE_INDEX", "TRANS_TYPE_INDEX"])
        print("Field indexes:")
        for name, value in d.items():
            print("\t{} = {}".format(name, value))
        sys.exit(0)

    # Print out the Headers from Transaction
    if args.print_header:
        print(Transaction.header())
        sys.exit(0)

    trans_list = []
    ctr = 0
    for fname in args.input_file:
        with open(fname,"rU") as csvfile:
            reader = csv.reader(csvfile)

            # Skip first n rows
            if args.ignore_rows is not None:
                for i in range(args.ignore_rows):
                    reader.next()

            for row in reader:
                ctr += 1

                d = dt.datetime.strptime(row[EFFECTIVE_DATE_INDEX], "%m/%d/%Y").date()
                ttype = _get_type(row[TRANS_TYPE_INDEX])

                t = Transaction(d, ttype, row[EMP_ID_INDEX], row[POSITION_ID_INDEX], ctr)
                trans_list.append(t)

                if args.test:
                    print(row)
                    print(t.test_str())
                    sys.exit(0)

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

