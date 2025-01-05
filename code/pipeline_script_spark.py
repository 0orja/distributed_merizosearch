import sys
from subprocess import Popen, PIPE
import glob
import os
from pyspark.sql import SparkSession
import gzip
import shutil
import io


"""
usage: python pipeline_script.py [INPUT DIR] [OUTPUT DIR]
approx 5seconds per analysis
"""

def run_parser(input_file, output_dir):
    """
    Run the results_parser.py over the hhr file to produce the output summary
    """
    search_file = input_file+"_search.tsv"
    print(search_file, output_dir)
    parser_path = os.path.join(os.getcwd(), "results_parser.py")
    cmd = ['python', parser_path, output_dir, search_file]
    print(f'STEP 2: RUNNING PARSER: {" ".join(cmd)}')
    try:
        p = Popen(cmd, stdin=PIPE,stdout=sys.stdout, stderr=sys.stderr)
        out, err = p.communicate()
        return out.decode("utf-8")
    except Exception as e:
        return f"Error: {e}"

def run_merizo_search(input_file, id, output_dir):
    """
    Runs the merizo domain predictor to produce domains
    """
    cmd = ['python3',
           '/home/almalinux/merizo_search/merizo_search/merizo.py',
           'easy-search',
           input_file,
           '/home/almalinux/cath_foldclassdb/cath-4.3-foldclassdb',
           output_dir+id,
           'tmp',
           '--iterate',
           '--output_headers',
           '-d',
           'cpu',
           '--threads',
           '1'
           ]
    print(f'STEP 1: RUNNING MERIZO: {" ".join(cmd)}')
    try:
        p = Popen(cmd, stdin=PIPE,stdout=sys.stdout, stderr=f)
        out, err = p.communicate()
        return out.decode("utf-8")
    except Exception as e:
        return f"Error: {e}"

# input_path = "hdfs://managernode:9000/ecoli_subset/AF-A0A385XJ53-F1-model_v4.pdb.gz"
# rdd = spark.sparkContext.textFile(input_path)

def read_dir(input_dir, spark_context):
    """
    Function reads a fasta formatted file of protein sequences
    """
    print(f"Getting file list from {input_dir}")
    files_rdd = spark_context.wholeTextFiles(input_dir+"*.gz")
    file_ids = files_rdd.map(lambda x: x[0]).collect()
    print("file ids:")
    print(file_ids)
    return(file_ids)

def decompress_and_copy(filepath, binary_file):
    with gzip.GzipFile(fileobj=io.BytesIO(binary_file)) as f:
        content = f.read().decode('utf-8')

    with open(filepath, 'w') as f:
        f.write(content)

def pipeline(filepath, id, content, outpath):
    print(f"unpacking gz file {id}")
    unpacked_file_name = id.rstrip('.gz')
    localpath = '/home/almalinux/' + unpacked_file_name
    decompress_and_copy(localpath, content)
    # STEP 1
    run_merizo_search(localpath, id, '/home/almalinux')
    # STEP 2
    run_parser(id, 'home/almalinux')
    #os.remove(unpacked_file)

def test_pipeline(x):
    print(f"processing {x}")
    return x

def process_file(file):
    try:
        print(f"processing file {file}")
        id = file.split("/")[-1]
        print(f"extracted id {id}")
        return id

    except Exception as e:
        print(f"error {e}")
        return None

if __name__ == "__main__":
    print(f"script name: {sys.argv[0]}")
    print(f"input dir: {sys.argv[1]}")
    output_dir = sys.argv[2]
    print(f"output dir: {output_dir}")
    spark = SparkSession.builder.appName("MerizoSearchPipeline").getOrCreate()
    sc = spark.sparkContext
    #pdbfiles = read_dir("hdfs://managernode:9000/ecoli_subset/")
    print("Parallelizing the data")
    rdd = sc.binaryFiles(sys.argv[1])
    test_rdd = sc.parallelize([1,2,3])
    if rdd.isEmpty():
        print("rdd is empty")
    else:
        #print(rdd.foreach(lambda x: process_file(x)))
        out_rdd = rdd.map(lambda x: pipeline(x[0], process_file(x[0]), x[1], output_dir))
        out_rdd.saveAsTextFile(output_dir)
       # print(processed_rdd.collect())
       # rdd.foreach(lambda x: open("/tmp/debug_worker_log.txt", "a").write(f"processed: {process_file(x)}"))
        #rdd.foreach(lambda x: test_pipeline(x))
    print("Done")
    spark.stop()