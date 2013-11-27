#!/bin/python
#  Datamonkey - An API for comparative analysis of sequence alignments using state-of-the-art statistical models.
#
#  Copyright (C) 2013
#  Sergei L Kosakovsky Pond (spond@ucsd.edu)
#  Steven Weaver (sweaver@ucsd.edu)
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the
#  "Software"), to deal in the Software without restriction, including
#  without limitation the rights to use, copy, modify, merge, publish,
#  distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so, subject to
#  the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import subprocess
import shutil
import argparse
import csv
import os
import uuid
from itertools import chain
import json

CONFIG_PATH = os.path.dirname(os.path.realpath(__file__)) + '/../config.json'
config = json.loads(open(CONFIG_PATH).read())

#These should come from config
PYTHON=config.get('python')
BEALIGN=config.get('bealign')
BAM2MSA=config.get('bam2msa')
TN93DIST=config.get('tn93dist')
HIVNETWORKCSV=config.get('hivnetworkcsv')
LANL_FASTA=config.get('lanl_fasta')
LANL_TN93OUTPUT_CSV=config.get('lanl_tn93output_csv')
HXB2_FASTA=config.get('hxb2_fasta')
HXB2_LINKED_LANL=config.get('hxb2_linked_lanl')


def update_status(status, status_file):
    with open(status_file, 'a') as status_f:
        status_f.write(status + '\n')

def flag_duplicates(fasta_fn):
    return

def concatenate_data(output, reference_fn, pairwise_fn, user_fn):
    #cp LANL_TN93OUTPUT_CSV USER_LANL_TN93OUTPUT
    shutil.copyfile(reference_fn, output)

    with open(output, 'a') as f:
        fwriter = csv.writer(f, delimiter=',', quotechar='|')
        prependid = lambda x : [x[0], x[1], x[2]]
        # Read pairwise results
        #tail -n+2 OUTPUT_USERTOLANL_TN93_FN >> USER_LANL_TN93OUTPUT
        with open(pairwise_fn) as pairwise_f:
            preader = csv.reader(pairwise_f, delimiter=',', quotechar='|')
            preader.__next__()
            rows = [prependid(row) for row in preader]
            fwriter.writerows(rows)

        # Read user_results, preprend ids
        #tail -n+2 OUTPUT_TN93_FN >> USER_LANL_TN93OUTPUT
        prependuid = lambda x : [x[0], x[1], x[2]]
        with open(user_fn) as user_f:
            ureader = csv.reader(user_f, delimiter=',', quotechar='|')
            ureader.__next__()
            rows = [prependuid(row) for row in ureader]
            fwriter.writerows(rows)

    f.close()
    return


def create_filter_list(tn93_fn, filter_list_fn) :
    # tail -n+2 OUTPUT_TN93_FN | awk -F , '{print 1"\n"2}' | sort -u >
    # USER_FILTER_LIST
    with open(filter_list_fn, 'w') as f:

        ids = lambda x : [x[0], x[1]]

        with open(tn93_fn) as tn93_f:
            tn93reader = csv.reader(tn93_f, delimiter=',', quotechar='|')
            tn93reader.__next__()
            rows = [ids(row) for row in tn93reader]
            #Flatten list
            rows = list(set(list(chain.from_iterable(rows))))
            [f.write(row + '\n') for row in rows]
    return


def annotate_with_hxb2(hxb2_links_fn, hivcluster_json_fn):

    # Read hxb2 links
    with open(hxb2_links_fn) as hxb2_fh:
        hxb2_reader = csv.reader(hxb2_fh, delimiter=',', quotechar='|')
        hxb2_reader.__next__()
        hxb2_links  = [row[0].strip() for row in hxb2_reader]

    # Load hivcluster json
    with open(hivcluster_json_fn) as hivcluster_fh:
        hivcluster_json = json.loads(hivcluster_fh.read())

    nodes = hivcluster_json.get('Nodes')

    #for each link in hxb2, get id in json object and add attribute
    ids = filter(lambda x: x['id'] in hxb2_links, nodes)

    [id.update({'hxb2_linked': True}) for id in ids]

    #Save nodes to file
    with open(hivcluster_json_fn, 'w') as json_fh:
        json.dump(hivcluster_json, json_fh)

    return


def lanl_annotate_with_hxb2(lanl_hxb2_fn, lanl_hivcluster_json_fn, threshold):

    # Read hxb2 from generate lanl file
    with open(lanl_hxb2_fn) as lanl_hxb2_fh:
        lanl_hxb2_reader = csv.reader(lanl_hxb2_fh, delimiter=',', quotechar='|')
        lanl_hxb2_reader.__next__()

        #filter hxb2 links based on threshold
        lanl_hxb2_links = list(filter(lambda x: x[2]<threshold, lanl_hxb2_reader))
        lanl_hxb2_links = [l[0] for l in lanl_hxb2_links]

    # Load hivcluster json
    with open(lanl_hivcluster_json_fn) as lanl_hivcluster_json_fh:
        lanl_json = json.loads(lanl_hivcluster_json_fh.read())

    nodes = lanl_json.get('Nodes')

    #for each link in hxb2, get id in json object and add attribute
    ids = filter(lambda x: x['id'] in lanl_hxb2_links, nodes)
    [id.update({'hxb2_linked': True}) for id in ids]

    #Save nodes to file
    with open(lanl_hivcluster_json_fn, 'w') as json_fh:
        json.dump(lanl_json, json_fh)

    return

def id_to_attributes(fasta_fn, attribute_map):
    ''' Change id to uuid '''
    id_dict={}

    # Just keep it in memory
    ATTRIBUTE_FILE = fasta_fn + '.attr'

    # Create a tmp file
    copy_fn = fasta_fn + '.tmp'

    # The attribute filed in hivclustercsv is unsatisfactory
    # Create dictionary from ids with each getting a new uuid
    # [{'uuid': {'a1': '', 'a2': '', ... , 'a3': ''}}, ...]
    with open(copy_fn, 'w') as copy_f:
        with open(fasta_fn) as fasta_f:
            lines = fasta_f.readlines()
            for line in lines:
                ids = filter(lambda x: x.startswith('>'), lines)
                if line.startswith('>'):
                    oldid = line.strip('\n>')
                    newid = str(uuid.uuid4())
                    line = line.replace(oldid, newid)

                    #Parse just the filename from fasta_fn
                    source=os.path.basename(fasta_fn)
                    attr = [source]
                    attr.extend(oldid.split('_'))
                    id_dict.update({newid : dict(zip(attribute_map, attr))})
                copy_f.write(line)

    #Overwrite existing file
    shutil.move(copy_fn, fasta_fn)
    return id_dict

def annotate_attributes(trace_json_fn, attributes):
    trace_json_cp_fn = trace_json_fn + '.tmp'

    with open(trace_json_fn) as json_fh:
        trace_json = json.loads(json_fh.read())
        nodes = trace_json.get('Nodes')
        [node.update({'attributes' : attributes[node['id']]}) for node in nodes]
        with open(trace_json_cp_fn, 'w') as copy_f:
            json.dump(trace_json, copy_f)

    shutil.move(trace_json_cp_fn, trace_json_fn)

    return


def hivtrace(input, threshold, min_overlap, compare_to_lanl,
             status_file):

    #Convert to Python
    REFERENCE='HXB2_prrt'
    SCORE_MATRIX='HIV_BETWEEN_F'
    OUTPUT_FORMAT='csv'
    SEQUENCE_ID_FORMAT='plain'
    AMBIGUITY_HANDLING='average'

    BAM_FN=input+'_output.bam'
    OUTPUT_FASTA_FN=input+'_output.fasta'
    OUTPUT_TN93_FN=input+'_user.tn93output.csv'
    JSON_TN93_FN=input+'_user.tn93output.json'
    JSON_HXB2_TN93_FN=input+'_user.hxb2linked.json'
    HXB2_LINKED_OUTPUT_FASTA_FN=input+'_user.hxb2linked.csv'
    OUTPUT_CLUSTER_JSON=input+'_user.trace.json'
    STATUS_FILE=input+'_status'

    LANL_OUTPUT_CLUSTER_JSON=input+'_lanl_user.trace.json'
    OUTPUT_USERTOLANL_TN93_FN=input+'_usertolanl.tn93output.csv'
    USER_LANL_TN93OUTPUT=input+'_userlanl.tn93output.csv'
    USER_FILTER_LIST=input+'_user_filter.csv'

    # PHASE 1
    update_status("Aligning", status_file)
    subprocess.check_call([PYTHON, BEALIGN, '-r', REFERENCE, '-m', SCORE_MATRIX, '-R', input, BAM_FN])

    # PHASE 2
    update_status("Converting to FASTA", status_file)
    subprocess.check_call([PYTHON, BAM2MSA, BAM_FN, OUTPUT_FASTA_FN])

    # Ensure unique ids
    # Just warn of duplicates (by giving them an attribute)
    # rename_duplicates(OUTPUT_FASTA_FN)
    attribute_map = ('SOURCE', 'SUBTYPE', 'COUNTRY', 'ACCESSION_NUMBER', 'YEAR_OF_SAMPLING')
    id_dict = id_to_attributes(OUTPUT_FASTA_FN, attribute_map)

    # PHASE 3
    update_status("TN93 Analysis", status_file)
    tn93_fh = open(JSON_TN93_FN, 'w')
    subprocess.check_call([TN93DIST, '-o', OUTPUT_TN93_FN, '-t',
                           threshold, '-a', AMBIGUITY_HANDLING, '-l',
                           min_overlap, '-f', OUTPUT_FORMAT, OUTPUT_FASTA_FN],
                           stdout=tn93_fh)
    tn93_fh.close()

    # PHASE 3b
    # Flag HXB2 linked sequences
    tn93_hxb2_fh = open(JSON_HXB2_TN93_FN, 'w')
    subprocess.check_call([TN93DIST, '-o', HXB2_LINKED_OUTPUT_FASTA_FN, '-t',
                           threshold, '-a', AMBIGUITY_HANDLING, '-l',
                           min_overlap, '-f', OUTPUT_FORMAT, '-s', HXB2_FASTA,
                           OUTPUT_FASTA_FN],
                           stdout=tn93_hxb2_fh)
    tn93_hxb2_fh.close()

    # PHASE 4
    update_status("HIV Network Analysis", status_file)
    output_cluster_json_fh = open(OUTPUT_CLUSTER_JSON, 'w')
    subprocess.check_call([PYTHON, HIVNETWORKCSV, '-i', OUTPUT_TN93_FN, '-t',
                           threshold, '-f', SEQUENCE_ID_FORMAT, '-j', '-n',
                           'report'], stdout=output_cluster_json_fh)

    output_cluster_json_fh.close()

    # Add hxb2_link attribute to each node that is shown to be linked by way of
    # PHASE 3b
    annotate_with_hxb2(HXB2_LINKED_OUTPUT_FASTA_FN, OUTPUT_CLUSTER_JSON)

    annotate_attributes(OUTPUT_CLUSTER_JSON, id_dict)

    if compare_to_lanl:

      # PHASE 5
      #lanl_id_dict = id_to_attributes(LANL_FASTA, attribute_map)

      update_status("Public Database TN93 Analysis", status_file)
      subprocess.check_call([TN93DIST, '-o', OUTPUT_USERTOLANL_TN93_FN, '-t',
                             threshold, '-a', AMBIGUITY_HANDLING,
                             '-f', OUTPUT_FORMAT, '-l', min_overlap, '-s',
                             OUTPUT_FASTA_FN, LANL_FASTA])

      #Perform concatenation
      #This is where reference annotation becomes an issue
      concatenate_data(USER_LANL_TN93OUTPUT, LANL_TN93OUTPUT_CSV,
                       OUTPUT_USERTOLANL_TN93_FN, OUTPUT_TN93_FN)

      # Create a list from TN93 csv for hivnetworkcsv filter
      create_filter_list(OUTPUT_TN93_FN, USER_FILTER_LIST)

      # PHASE 6
      update_status("Public Database HIV Network Analysis", status_file)
      lanl_output_cluster_json_fh = open(LANL_OUTPUT_CLUSTER_JSON, 'w')


      subprocess.check_call([PYTHON, HIVNETWORKCSV, '-i', USER_LANL_TN93OUTPUT, '-t',
                            threshold, '-f', SEQUENCE_ID_FORMAT, '-j', '-n',
                            'report', '-k', USER_FILTER_LIST],
                            stdout=lanl_output_cluster_json_fh)

      lanl_output_cluster_json_fh.close()

    # Add hxb2_link attribute to each lanl node that is shown to be linked based
    # off a supplied file, but based on the user supplied threshold.
    #lanl_annotate_with_hxb2(HXB2_LINKED_LANL, USER_LANL_TN93OUTPUT, threshold)

    # Adapt ids to attributes
    #annotate_attributes(LANL_OUTPUT_CLUSTER_JSON, lanl_id_dict)
    update_status("Completed", status_file)


def main():
    parser = argparse.ArgumentParser(description='HIV TRACE')

    parser.add_argument('-i', '--input', help='Input CSV file with inferred genetic links (or stdin if omitted). Must be a CSV file with three columns: ID1,ID2,distance.')
    parser.add_argument('-t', '--threshold', help='Only count edges where the distance is less than this threshold')
    parser.add_argument('-m', '--minoverlap', help='Minimum Overlap')
    parser.add_argument('-c', '--compare', help='Compare to LANL', action='store_true')

    args = parser.parse_args()

    FN=args.input
    ID=os.path.basename(FN)
    DISTANCE_THRESHOLD=args.threshold
    MIN_OVERLAP=args.minoverlap
    COMPARE_TO_LANL=args.compare
    STATUS_FILE=FN+'_status'

    hivtrace(FN, DISTANCE_THRESHOLD, MIN_OVERLAP, COMPARE_TO_LANL, STATUS_FILE, ID)

if __name__ == "__main__":
    main()
