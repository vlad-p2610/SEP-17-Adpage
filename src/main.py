from pymcmodel import PYMC
import dataloader
import argparse
import pandas as pd

def main():
    models = ["pymc","meridian","metarobyn"]

    parser = argparse.ArgumentParser(prog="MMM evaluation harness", description="evaluate different MMM frameworks")
    parser.add_argument("path", help="path to the database")
    parser.add_argument("-m", "--model", choices=models, help="which model do you want")
    args = parser.parse_args()

    df = dataloader.load(args.model)

    if args.model == "pymc":
        model = PYMC(df)
    elif args.model == "meridian":
        pass

if __name__ == "__main__":
    main()