from pydantic import BaseModel
from outlines import Generator, from_transformers
import transformers

# Define a Pydantic model for structured output
class BookRecommendation(BaseModel):
    title: str
    author: str
    year: int

# Initialize a model
model_name = "HuggingFaceTB/SmolLM2-135M-Instruct"
model = from_transformers(
    transformers.AutoModelForCausalLM.from_pretrained(model_name),
    transformers.AutoTokenizer.from_pretrained(model_name),
)

# Create a generator for JSON output
generator = Generator(model, BookRecommendation)

# Generate a book recommendation
result = generator("Recommend a science fiction book.")

# Parse the JSON result into a Pydantic model
book = BookRecommendation.model_validate_json(result)
print(f"{book.title} by {book.author} ({book.year})")
