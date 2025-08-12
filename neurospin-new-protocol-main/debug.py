# test.py
import argparse
from src.utils import test_pipeline
from config.config import themes, numbers, tenses, prompts

def main():
    parser = argparse.ArgumentParser(description='Test the sentence generation pipeline')
    parser.add_argument('--theme', default='basic', choices=themes.keys(),
                        help='Theme for sentence generation')
    parser.add_argument('--number', default='singular', choices=numbers.keys(),
                        help='Number for sentence generation')
    parser.add_argument('--tense', default='present', choices=tenses.keys(),
                        help='Tense for sentence generation')
    parser.add_argument('--category', default='relatives', choices=prompts.keys(),
                        help='Category/prompt type for sentence generation')

    args = parser.parse_args()
    
    test_pipeline(
        theme=args.theme,
        number=args.number,
        tense=args.tense,
        category=args.category
    )

if __name__ == "__main__":
    main()
