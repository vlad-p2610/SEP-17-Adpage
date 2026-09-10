from pymcmodel import PYMC
import dataloader
import argparse
import pandas as pd
import os
from pathlib import Path

def main():
    models = ["pymc","meridian","metarobyn"]

    parser = argparse.ArgumentParser(prog="MMM evaluation harness", description="evaluate different MMM frameworks")
    parser.add_argument("path", help="relative path to the database")
    parser.add_argument("-m", "--model", choices=models, help="which model do you want")
    args = parser.parse_args()

    

    CHpath = Path(args.path)
    if not CHpath.is_absolute():
        CHpath = Path(os.getcwd()) / CHpath

    df = dataloader.load(args.model, CHpath)

    if args.model == "pymc":
        model = PYMC(df)
    elif args.model == "meridian":
        pass

if __name__ == "__main__":
    main()