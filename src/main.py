from pymcmodel import PYMC
import dataloader
import argparse
import pandas as pd
import os
from pathlib import Path
import yaml

def main():
    models = ["pymc","meridian","metarobyn"]

    #do the arguments thing in the console
    parser = argparse.ArgumentParser(prog="MMM evaluation harness", description="evaluate different MMM frameworks")
    parser.add_argument("path", help="relative path to the database")
    parser.add_argument("-m", "--model", choices=models, help="which model do you want")
    args = parser.parse_args()

    #load config yaml (its in the root prj folder dont move it pls)
    cfgPath = Path(__file__).resolve()
    cfgPath = cfgPath.parent.parent
    cfgPath = cfgPath / "config.yaml"
    
    with open(cfgPath, 'r') as file:
        config = yaml.safe_load(file)


    #print(config["pymc"]["lamda"]) # this is how you can access them

    CHpath = Path(args.path)
    if not CHpath.is_absolute():
        CHpath = Path(os.getcwd()) / CHpath

    df = dataloader.load(args.model, CHpath, config)

    if args.model == "pymc":
        model = PYMC(df, config)
    elif args.model == "meridian":
        pass

if __name__ == "__main__":
    main()