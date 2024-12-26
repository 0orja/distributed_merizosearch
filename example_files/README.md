# File Formats

This document describes the examples files

## test.pdb

A test input 3D Protein Structure in PDB format (see https://en.wikipedia.org/wiki/Protein_Data_Bank_(file_format))

## test_segment.tsv

The first of the pipeline output files. This file represents the output of a machine learning process that identifies unique protein domains within a Protein 3D Structure

## test_search.tsv

The second of the pipeline output files. This file represents the output of an optimised search of data embedding space and is used to annotate the names (CATH code) for each domain recognised in the prior step

## test.parsed

The third and final output of the analysis pipeline. This file summarises the 2 pieces of data the researchers want capture from their data analysis pipeline. They only capture data from the dom_plddt and  metdata columns in test_search.tsv

You have a comment line that identifies the name of the input file and the mean of all the dom_plddt in the test_search.tsv files. This is followed by CSV formatted data which lists the counts of the domains named by their CATH code.

## ecoli_cath_summary.csv and humman_cath_summary.csv

Theses are examples of two files you system must produce by collating the results present in ALL the .parsed files your system will produce. The header line indicates the column names (cath_id and count). The first column is the CATH code found in the .parsed file the second column is the sum of all the counts across all the .parsed files for the ID per organism. You will have one row for each unique CATH Code. Your file will be very much longer than the examples, there are currently 5,481 possible CATH codes. Human and ecoli will have some subset of this number

## plDDT_means.csv

Each .parsed file contains a mean plDDT value for that run of the analysis pipeline. You must produce a file that aggregates by taking the mean of all the plDDTs for each organism's input files. You should also calculate the Standard Deviation of these values per organism. The file must be a CSV where the columns are Organism shortname, mean plDDTs and standard deviation.
