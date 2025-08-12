# src/run.py
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import itertools
from .utils import test_pipeline
from config.config import themes, numbers, tenses, prompts

def main():

    rst = test_pipeline()
    print(rst)

if __name__ == "__main__":
    main()