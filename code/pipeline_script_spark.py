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
python_path = "/home/almalinux/merizosearch_env/bin/python"

os.environ["PYSPARK_PYTHON"] = python_path
os.environ["PYSPARK_DRIVER_PYTHON"] = python_path

# activate_env = os.path.expanduser("/home/almalinux/merizosearch_env/bin/activate")
# exec(open(activate_env).read(), dict(__file__=activate_env))

def run_parser(input_file, output_dir):
    """
    Run the results_parser.py over the hhr file to produce the output summary
    """
    search_file = input_file+"_search.tsv"
    print(search_file, output_dir)
    #parser_path = os.path.join(os.getcwd(), "results_parser.py")


    cmd = [python_path, 'results_parser.py', output_dir, search_file]
    print(f'STEP 2: RUNNING PARSER: {" ".join(cmd)}')
    with open("/home/almalinux/debug_worker_log.txt", "a") as f:
        f.write("parser\n")
        #f.write(parser_path+"\n")
        f.write(output_dir+"\n")
        f.write(search_file+"\n")
        try:
            p = Popen(cmd, stdin=PIPE,stdout=f, stderr=f)
            out, err = p.communicate()
            # with open("/home/almalinux/debug_worker_log.txt", "a") as f:
            if out:
                f.write(f'output: {out.decode("utf-8")}\n')
            if err:
                f.write(f'p error: {err.decode("utf-8")}\n')
        except Exception as e:
            #with open("/home/almalinux/debug_worker_log.txt", "a") as f:
            f.write(f"error: {e}\n")
            raise e

def run_merizo_search(input_file, id, output_dir):
    """
    Runs the merizo domain predictor to produce domains
    """
    cmd = [python_path,
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
    with open("/home/almalinux/debug_worker_log.txt", "a") as f:
        f.write("merizo\n")
        f.write(input_file+"\n")
        f.write(output_dir+"\n")
        f.write(id+"\n")
        print(f'STEP 1: RUNNING MERIZO: {" ".join(cmd)}')
        try:
            p = Popen(cmd, stdin=PIPE,stdout=f, stderr=f)
            out, err = p.communicate()
        except Exception as e:
            # with open("/home/almalinux/debug_worker_log.txt", "a") as f:
            f.write(f"error: {e}\n")
            raise e
    
# input_path = "hdfs://managernode:9000/ecoli_subset/AF-A0A385XJ53-F1-model_v4.pdb.gz"
# rdd = spark.sparkContext.textFile(input_path)
def write_to_hdfs(local_path, id, hdfs_dir):
    # hdfs://managernode:9000/ecoli_subset_out
    for ext in [".parsed", "_search.tsv", "_segment.tsv"]:
        filename = id + ext
        hdfs_path = "/".join(["",hdfs_dir.split("/")[-1],filename])
        cmd = ['hdfs', 'dfs', '-copyFromLocal', local_path+filename, hdfs_dir]
        with open("/home/almalinux/debug_worker_log.txt", "a") as f:
            f.write("writing to hdfs:\n")
            f.write(local_path+"\n")
            f.write(filename+"\n")
            f.write(hdfs_dir+"\n")
            print(f'WRITING TO HDFS: {" ".join(cmd)}')
            try:
                p = Popen(cmd, stdin=PIPE,stdout=f, stderr=f)
                out, err = p.communicate()
                if out:
                    f.write(f'h output: {out.decode("utf-8")}\n')
                if err:
                    f.write(f'h error: {err.decode("utf-8")}\n')
                os.remove(local_path+filename)
            except Exception as e:
                #with open("/home/almalinux/debug_worker_log.txt", "a") as f:
                if "No such file or directory" in str(e):
                    f.write(f"file not found: {filename}, skiping\n")
                else:
                    f.write(f"error hdfs: {e}\n")
                    raise e
            

def decompress_and_copy(filepath, binary_file):
    with gzip.GzipFile(fileobj=io.BytesIO(binary_file)) as f:
        content = f.read().decode('utf-8')
    
    with open(filepath, 'w') as f:
        f.write(content)

def pipeline(filepath, id, content, outpath):
    os.environ["PYSPARK_PYTHON"] = "/home/almalinux/merizosearch_env/bin/python"
    os.environ["PYSPARK_DRIVER_PYTHON"] = "/home/almalinux/merizosearch_env/bin/python"
    with open("/home/almalinux/debug_worker_log.txt", "a") as f:
        f.write(f"processing {id}\n")
        f.write(f"env: {os.environ['PYSPARK_PYTHON']}\n")
    print(f"unpacking gz file {id}")
    unpacked_id = id.rstrip('.gz')
    localpath = '/home/almalinux/' + unpacked_id
    decompress_and_copy(localpath, content)
    local_outpath = '/home/almalinux/spark_out/'
    # STEP 1
    run_merizo_search(localpath, unpacked_id, local_outpath)
    # STEP 2
    run_parser(unpacked_id, local_outpath)
    # STEP 3
    hdfs_path = "/" + outpath.split("/")[-1]
    write_to_hdfs(local_outpath, unpacked_id, hdfs_path)

    prefix = id.split('.')[0] 
    return (local_outpath+prefix+'.parsed', local_outpath+prefix+'_search.tsv', local_outpath+prefix+'_segment.tsv')
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
    rdd = sc.binaryFiles(f"{sys.argv[1]}*.pdb.gz")
    test_rdd = sc.parallelize([1,2,3])
    if rdd.isEmpty():
        print("rdd is empty")
    else:
        #print(rdd.foreach(lambda x: process_file(x)))
        out_rdd = rdd.foreach(lambda x: pipeline(x[0], process_file(x[0]), x[1], output_dir))
        #out_rdd.saveAsTextFile(output_dir)
       # print(processed_rdd.collect())
       # rdd.foreach(lambda x: open("/tmp/debug_worker_log.txt", "a").write(f"processed: {process_file(x)}"))
        #rdd.foreach(lambda x: test_pipeline(x))
    print("Done")
    spark.stop()
