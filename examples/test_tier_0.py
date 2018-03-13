import os
from pygama.processing import process_tier_0

def main():
    mjd_data_dir = os.path.join(os.getenv("DATADIR", "."), "mjd")
    raw_data_dir = os.path.join(mjd_data_dir,"raw")

    runList = [11510]

    process_tier_0(raw_data_dir, runList, output_dir="", chanList=[600,626,672])

if __name__=="__main__":
    main()
