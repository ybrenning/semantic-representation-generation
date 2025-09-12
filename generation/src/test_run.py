# src/run.py
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import itertools

from generation.src.utils import test_pipeline
from generation.config.config import themes, numbers, tenses, prompts


def main():
    test_pipeline(print_prompt=True)


if __name__ == "__main__":
    main()
