import sys
from subprocess import Popen, PIPE
import os
from pyspark.sql import SparkSession
import gzip
import io
from datetime import date

"""
usage: python pipeline_script_spark.py [INPUT HDFS DIR] [OUTPUT HDFS DIR]
approx 5seconds per analysis
"""
# use virtual environment
python_path = "/home/almalinux/merizosearch_env/bin/python"
os.environ["PYSPARK_PYTHON"] = python_path
os.environ["PYSPARK_DRIVER_PYTHON"] = python_path


def run_parser(input_file, output_dir):
    """
    Run the results_parser.py over the hhr file to produce the output summary
    """
    search_file = input_file+"_search.tsv"
    print(search_file, output_dir)
    cmd = [python_path, 'results_parser.py', output_dir, search_file]
    print(f'STEP 2: RUNNING PARSER: {" ".join(cmd)}')
    with open("/home/almalinux/debug_worker_log.txt", "a") as f:
        f.write(f"parsing: {search_file}\n")
        try:
            p = Popen(cmd, stdin=PIPE,stdout=f, stderr=f)
            out, err = p.communicate()
            if out:
                f.write(f'output: {out.decode("utf-8")}\n')
            if err:
                f.write(f'p error: {err.decode("utf-8")}\n')
        except Exception as e:
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
        f.write(f"running merizo on {id}\n")
        print(f'STEP 1: RUNNING MERIZO: {" ".join(cmd)}')
        try:
            p = Popen(cmd, stdin=PIPE,stdout=f, stderr=f)
            out, err = p.communicate()
        except Exception as e:
            f.write(f"error: {e}\n")
            raise e


def write_to_hdfs(local_path, id, hdfs_dir):
    # hdfs://managernode:9000/ecoli_subset_out
    for ext in [".parsed", "_search.tsv", "_segment.tsv"]:
        filename = id + ext
        hdfs_path = "/".join(["",hdfs_dir.split("/")[-1],filename])
        cmd = ['hdfs', 'dfs', '-copyFromLocal', local_path+filename, hdfs_path]
        with open("/home/almalinux/debug_worker_log.txt", "a") as f:
            f.write("writing to hdfs:\n")
            f.write(local_path+filename+"\n")
            f.write(hdfs_path+"\n")
            print(f'WRITING TO HDFS: {" ".join(cmd)}')
            try:
                p = Popen(cmd, stdin=PIPE,stdout=f, stderr=f)
                out, err = p.communicate()
                if out:
                    f.write(f'h output: {out.decode("utf-8")}\n')
                if err:
                    f.write(f'h error: {err.decode("utf-8")}\n')
                os.remove(local_path+filename) # remove results files
                os.remove("/home/almalinux/"+id) # remove .pdb file
            except Exception as e:
                if "No such file or directory" in str(e):
                    f.write(f"file not found: {filename}, skiping\n")
                else:
                    f.write(f"error hdfs: {e}\n")
                    raise e


# decompress binary .gz file and copy to local disk
def decompress_and_copy(filepath, binary_file):
    with gzip.GzipFile(fileobj=io.BytesIO(binary_file)) as f:
        content = f.read().decode('utf-8')
    with open(filepath, 'w') as f:
        f.write(content)


def pipeline(filepath, id, content, outpath):
    # use virtual environment
    os.environ["PYSPARK_PYTHON"] = "/home/almalinux/merizosearch_env/bin/python"
    os.environ["PYSPARK_DRIVER_PYTHON"] = "/home/almalinux/merizosearch_env/bin/python"
    
    # check if file has already been parsed before
    hdfs_path = "/" + outpath.split("/")[-1] + "/" + id.rstrip('.gz') + ".parsed"
    cmd = ['hdfs', 'dfs', '-test', '-e', hdfs_path]
    try:
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        p.communicate()
        if p.returncode == 0:
            print(f"{hdfs_path} already processed, skipping processing.")
            return
    except Exception as e:
        with open("/home/almalinux/debug_worker_log.txt", "a") as f:
            f.write(f"error checking hdfs path: {e}\n")
            raise e
    with open("/home/almalinux/debug_worker_log.txt", "a") as f:
        f.write(f"processing {id}\n")
    print(f"unpacking gz file {id}")
    unpacked_id = id.rstrip('.gz')
    localpath = '/home/almalinux/' + unpacked_id # copy file from hdfs into here
    decompress_and_copy(localpath, content)
    local_outpath = '/home/almalinux/spark_out/' # directory for intermediate files
    # STEP 1
    run_merizo_search(localpath, unpacked_id, local_outpath)
    # STEP 2
    run_parser(unpacked_id, local_outpath)
    # STEP 3
    hdfs_path = "/" + outpath.split("/")[-1]
    write_to_hdfs(local_outpath, unpacked_id, hdfs_path) # copy from local to hdfs
    prefix = id.split('.')[0] 
    return (local_outpath+prefix+'.parsed', local_outpath+prefix+'_search.tsv', local_outpath+prefix+'_segment.tsv')


def get_file_id(file):
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
    app_name = "-".join(["MerizoSearch",sys.argv[1].split("/")[-2],str(date.today())])
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    sc = spark.sparkContext
    print("Parallelizing the data")
    rdd = sc.binaryFiles(sys.argv[1])
    rdd = rdd.repartition(18).cache() # force repartition to 9 
    print("partitions:", rdd.getNumPartitions())
    if rdd.isEmpty():
        print("rdd is empty")
    else:
        out_rdd = rdd.foreach(lambda x: pipeline(x[0], get_file_id(x[0]), x[1], output_dir))
    print("Done")
    spark.stop()
