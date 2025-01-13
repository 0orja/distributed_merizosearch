import os
import sys
import csv
from collections import defaultdict
import statistics

def aggregate_counts(input_dirs: list[str]):
    if not os.path.exists("/home/almalinux/data/plDDT_means.csv"): # only create file if it doesn't exist to avoid overwriting previous datasets
        with open("/home/almalinux/data/plDDT_means.csv", 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['organism', 'mean_plddt', 'plddt std'])
    for input_dir in input_dirs:
        print(input_dir.split("/")[-1])
        organism = input_dir.split("/")[-1].replace("_output","")
        output_file = f"/home/almalinux/data/{organism}_summary.csv"
        cath_counts = defaultdict(int) # store counts for each CATH code
        plddt_scores = []

        # go through all .parsed files in the specified directory
        for filename in os.listdir(input_dir):
            if filename.endswith(".pdb.parsed"):
                filepath = os.path.join(input_dir, filename)
                with open(filepath, 'r') as file:
                    reader = csv.reader(file)
                    # extract mean plDDT from first row
                    firstline = next(reader)
                    mean_plddt = float(firstline[0].split("mean plddt:")[1].strip())
                    plddt_scores.append(mean_plddt)
                    next(reader)  # Skip the second header row
                    for row in reader:
                        cath_code, count = row
                        cath_counts[cath_code] += int(count)

        # write aggregated counts to output csv
        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['cath_code', 'count'])
            for cath_code, count in cath_counts.items():
                writer.writerow([cath_code, count])
        # calculate mean and std of plddt scores
        if plddt_scores:
            mean_plddt = round((sum(plddt_scores) / len(plddt_scores)), 3)
            std = round(statistics.stdev(plddt_scores), 3)
        else:
            mean_plddt = 0
            std = 0
        with open("/home/almalinux/data/plDDT_means.csv", 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([organism, mean_plddt, std])

if __name__ == "__main__":
    input_directories = sys.argv[1:]
    print(input_directories)
    aggregate_counts(input_directories)
