#!/usr/bin/env python -B
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

    Next loop through each transaction and create Workers and
    Positions as needed. add the Transaction to the Worker and
    Position objects

    Once the Transactions, Workers and Postions are all created, go through
    and perform validations (e.g. filling in from_position, or making sure
    that a worker is hired before they have a job change)

    Once we have all the required data, and we have removed invalid transactions,
    for each worker, start at top of stack transaction for each worker (most recent one)
    and derive the list of pre-requisites. This should get you pre-requisites
    for every valid transaction

    Finally, generate output as specified in the program invocation

    Files need to be in the following excel csv format:
    record id, employee id, event date, position id, <unused>, transaction type
    
    Valid Transaction Types:
        Hire
        Job Change
        Assign Org
        LOA Start
        LOA Stop
        Term
        ** Note - we need both loa start and stop at this point
    
    --errored-record-file option is used for debugging sequence issues. It takes two arguments,
    the first is the transaction type (e.g. HIRE, TERM, etc), and the second is a file name
    containing a list of record ids. These are the same record ids that correspond to the input file 
    (matches both type and record number). The program then builds an output file containing only 
    those transactions needed to build out those selected records, it looks up the related 
     workers and positions and gets all the required transactions based on that data
     - it should include all dependent records.

    TODO: Add ability to include row headers in command line (which position)
    TODO: Add ability to take in staffing model (job mgmt)
    TODO: Add errored-record-file option
    TODO: Clean up logging / messaging between debug and verbose
    TODO: Add guide to adding transaction types (what methods you need to look at
"""
import csv
import sys
import time
import datetime as dt
import os.path
import argparse
from collections import OrderedDict
from worker import Worker
from transaction import Transaction
from __init__ import *

# Specify the indexed location for each field in input files:
# Ex: EMP_123, 3/4/2010, HIRE, POS_1, 12345
# EMP_123 is index 0, effective date is index 1, etc
RECORD_ID = 0
EMP_ID_INDEX = 1
EFFECTIVE_DATE_INDEX = 2
POSITION_ID_INDEX = 3
TRANS_TYPE_INDEX = 4

def pager(page_size, iterable):
    """ Helper function to easily page through iterables """
    page = []
    for i in iterable:
        page.append(i)
        if len(page) == page_size:
            yield page
            page = []
    yield page

def _get_type(type_str):
    """ Map values in file for transaction type to supported transactions """
    ret = Trans_Type.get_type(type_str)
    if ret is None:
        print("Error, unknown type {}".format(type_str))
        raise Exception
    return ret

def parse_command_line():
    """ Process command line arguments """
    parser = argparse.ArgumentParser(
        description=("This module takes a list of transactions" 
                     " as input files and generates the sequencing for loading those " 
                     "transactions into Workday. \n" 
                     "Files need to be in the following csv format:" 
                     "employee id, event date, position id, <unused>, transaction type"))
    parser.add_argument("input_file", metavar="Input File", nargs="+",
                        help="Input file - multiple files may be specified")
    parser.add_argument("-i", "--ignore-rows", type=int, help="Ignore first n rows of input file")
    parser.add_argument("-o", "--output_file", default="./output.csv")
    parser.add_argument("--final-term-file", action="store_true",
                        help="Hold \"final\" terms for the last term file")
    parser.add_argument("--file-by-type", action="store_true",
                        help=("Generate output files by transaction type."
                              " Designed to be inserted directly into excel "
                              "master file. Output is orded by record id if available, "
                              "otherwise order by load order. Output files are put in "
                              "current directory, and named <type>.<timestamp>.csv."))
    parser.add_argument("--errored-records-file", nargs=2, help=("Transaction type string and file name. File "
                                                                 "contains list of errored records. Generates "
                                                                 "output file containing on transactions related to "
                                                                 "those records"))
    parser.add_argument("--stop-on-validation", action="store_true", help="Dump validation messages to screen and exit")
    parser.add_argument("--page-size", type=int, default=5000,
                        help="Number of transactions to process prior to printing out status message")
    parser.add_argument("-t", "--test", action="store_true", help="Print out first line of file with field mapping")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("--stats", action="store_true", help="Return statistics about transaction numbers and types")
    parser.add_argument("--indexes", action="store_true", help="Print out column indexes for csv files")
    parser.add_argument("--print-header", action="store_true", help="Print out header column names", required=False)
    parser.add_argument("--dump-worker", action="append", help="Dump transaction list for worker with worker id")
    parser.add_argument("--dump-position", action="append", help="Dump transaction list for position with worker id")
    parser.add_argument("--dump-transaction", action="append", help="Dump transaction list for transaction with lineno")
    mgroup = parser.add_mutually_exclusive_group()
    mgroup.add_argument("-p", "--position", help="Output only transactions with specified position (position id)",
                        action="append", required=False)
    mgroup.add_argument("-w", "--worker", help="Output only transactions with specified worker (employee id)",
                        action="append", required=False)
    mgroup.add_argument("-s", "--sequence", help="Output only workers w max sequence > value", type=int)
    return parser.parse_args()


if __name__ == "__main__":

    args = parse_command_line()

    # Set logging
    if args.verbose:
        l.setLevel(logging.INFO)
    if args.debug:
        l.setLevel(logging.DEBUG)
    info("Starting program.")

    # Set global logging values
    if not args.stop_on_validation:
        stop_on_validation = True

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

    # Check for debugging sequence issues
    if args.errored_records_file:
        # Arg 1 should be trans type, arg 2 should be file name, check to see if valid
        type_str = args.errored_records_file[0]
        try:
            _get_type(type_str)
        except:
            error("Invalid type passed to errored-records-file option of {}".format(
                    type_str))
            error("Valid values are:")
            for t in Trans_Type.all_types():
                print("\t{}".format(t))
            raise
        file = args.errored_recoreds_file[1]
        if not os.path.isfile(file):
            error("File {} does not exist.".format(file))
            raise Exception



    """ Start processing files """
    trans_list = []
    ctr = 0
    transaction_dict = {}
    file_row_cnt = 0
    for fname in args.input_file:
        info("Opening {}".format(fname))
        with open(fname,"rU") as csvfile:
            reader = csv.reader(csvfile)

            # Skip first n rows
            if args.ignore_rows is not None:
                for i in range(args.ignore_rows):
                    reader.next()

            for row in reader:
                try:
                    ctr += 1

                    d = dt.datetime.strptime(row[EFFECTIVE_DATE_INDEX], "%m/%d/%Y").date()
                    ttype = _get_type(row[TRANS_TYPE_INDEX])

                    t = Transaction(d, ttype, row[EMP_ID_INDEX], row[POSITION_ID_INDEX], ctr, row[RECORD_ID])
                    trans_list.append(t)
                    ttype.add_transaction(t)
                    transaction_dict[str(ctr)] = t

                    if args.test:
                        print(row)
                        print(t.test_str())
                        sys.exit(0)
                except:
                    error("Exception reading row")
                    error(row)
                    error("From file {}".format(fname))
                    raise
            file_row_cnt = ctr - file_row_cnt
        info("Finished reading {} lines from {}".format(file_row_cnt, fname))

    if args.stats:
        print("Total transaction count: {}".format(len(trans_list)))
        for tt in Trans_Type.all_types():
            print("Type: {}".format(tt.ttype))
            print("\tTotal Transaction Count: {}".format(tt.total_count))
            print("\tGood Transaction Count: {}".format(tt.good_count))
            print("\tBad Transaction Count: {}".format(tt.bad_count))

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
    info("Building data structures")
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
    info("Validating worker data")
    for w in worker_dict.values():
        w.validate()

    info("Validating position data")
    for p in position_dict.values():
        p.validate()


    """
        We now have a full set of data. Any logical checks have been performed, added data
        (e.g. from_position) has been added as applicable.
        Below this point we now use the data to generate the requested output
    """

    # Go through each transaction and get pre-reqs
    info("Calculating dependencies")
    if not args.worker and not args.position:
        for p in pager(args.page_size, worker_dict.values()):
            for w in p:
                    if not w.valid:
                        continue
                    t = w.top_of_stack()
                    if not t:
                        continue
                    t.return_pre_reqs()
            info("Processed pre-reqs for {} workers.".format(len(p)))
        for p in pager(args.page_size, worker_dict.values()):
            for w in p:
                if not w.valid:
                    continue
                t = w.top_of_stack()
                if not t:
                    continue
                t.get_seq()
            info("Processed sequences for {} workers".format(len(p)))
        if args.final_term_file:
            # Push all top of stack terms to final wave
            seq = Transaction._max_seq
            for w in worker_dict.values():
                if not w.valid:
                    continue
                if w.top_of_stack().ttype is TERM:
                    w.top_of_stack().set_final_term_seq()
    elif args.worker: # Only calc for worker(s) (and related workers as needed)
        for emp_id in args.worker:
            if emp_id not in worker_dict:
                print("Worker with employee id = {} does not exist.".format(emp_id))
                raise Exception
            t = worker_dict[emp_id].top_of_stack()
            sub_list = t.return_pre_reqs()
            # Now we get all the workers in the list and print out all their transactions
            worker_set = set()
            for t in sub_list:
                worker_set.add(t.worker)
            trans_list = []
            for w in worker_set:
                trans_list += w.get_transactions()
    elif args.position:  # Only calc for position(s)
        for pos_id in args.position:
            if pos_id not in position_dict:
                print("Position {} does not exist in input file".format(pos_id))
                sys.exit(1)
            t = position_dict[pos_id].top_of_stack()
            sub_list = t.return_pre_reqs()
            position_set = set()
            for p in sub_list:
                position_set.add(t.position)
            trans_list = []
            for p in position_set:
                trans_list += p.get_transactions()

    info("Max sequence is {}".format(Transaction._max_seq))

    """ 
        Dump specific workers or positions for use in debugging
        if specified on command line
    """
    if args.debug:
        print("Dumping max sequence transaction\n{}".format(Transaction._max_seq_t))
        print(Transaction._max_seq_t.dump())
    if args.dump_worker:
        for w in args.dump_worker:
            if w not in worker_dict:
                print("Employee id {} not found in data file".format(w))
            else:
                print(worker_dict[w].dump())
    if args.dump_position:
        for p in args.dump_position:
            if p not in position_dict:
                print("Position id {} not found in data file".format(p))
            else:
                print(position_dict[p].dump())
    if args.dump_transaction:
        for t in args.dump_transaction:
            if t not in transaction_dict:
                print("Transaction lineno {} not found in data file".format(t))
            else:
                print(transaction_dict[t].dump())

    info("Calculating statistics")
    master_list = []
    for i in range(Transaction._max_seq + 1):
        master_list.append(OrderedDict([(key, []) for key in Trans_Type.all_types()]))
    for t in trans_list:
        if not t.valid:
            continue
        i = t.seq
        tt = t.ttype
        master_list[i][tt].append(t)
    if args.stats:
        file_ctr = 0
        file_stats = OrderedDict.fromkeys(Trans_Type.all_types(), 0)
        for i in range(Transaction._max_seq + 1):
            print("Wave {}".format(i))
            for k, v in master_list[i].iteritems():
                if v:
                    file_ctr += 1
                    file_stats[k] += 1
                    print("\t{} has {} transactions.".format(k, len(v)))
        print("A total of {} files will have to be loaded".format(file_ctr))
        for tt, ct in file_stats.iteritems():
            print("\t{} file(s) of type {}".format(ct, tt))
    """
    for t in master_list[0][HIRE]:
        if t.worker.flag:
            print("Duplicate worker in wave 0: {}".format(w))
        t.worker.flag = True
    print(master_list[1][HIRE][:5])
    """


    info("Generating output")
    # Let's find some complicated worker transactions if requested
    if args.sequence is not None:
        for w in worker_dict.values():
            if w.max_seq >= args.sequence:
                t = w.top_of_stack()
                print("Found top-level worker transaction w seq > {}".format(args.sequence))
                print("Pre-reqs for {}".format(t))
                for ts in t.return_pre_reqs():
                    print("\t{}".format(ts))

    # Generate output files
    if args.file_by_type:
        timestamp = time.strftime("%Y-%m-%d_%H%M%S")
        for tt in Trans_Type.all_types():
            fname = "{}.{}.csv".format(str(tt.ttype).replace(" ", "_"), timestamp)
            with open(fname, "w") as f:
                f.write(Transaction.header() + "\n")
                for t in tt.get_ordered_transactions():
                    f.write(t.output() + "\n")
    else:
        with open(args.output_file, "w") as f:
            f.write(Transaction.header() + "\n")
            for t in trans_list:
                f.write(t.output() + "\n")
    info("Done")

