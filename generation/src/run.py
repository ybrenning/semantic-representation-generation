# src/run.py
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import itertools
from generation.src.utils import process_task
from generation.config.config import themes, numbers, tenses, prompts

def main():
    tasks = list(itertools.product(prompts.keys(), themes.keys(), numbers.keys(), tenses.keys()))
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(process_task, tasks)

if __name__ == "__main__":
    main()
