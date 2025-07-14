# ZIP Code Visual Aesthetics Generator

A Python program that uses OpenAI's GPT-4 model to generate visual aesthetics for U.S. ZIP codes.

## Features

- Analyzes ZIP codes to determine regional visual characteristics
- Generates three aesthetic components: visual_style, color_texture, and art_style
- Handles API errors gracefully with fallback values
- Command-line interface for easy integration
- Programmatic API for use in other applications

## Requirements

- Python 3.7+
- OpenAI API key
- Required packages (already in requirements.txt):
  - `openai>=1.0.0`
  - `python-dotenv>=0.19.0`

## Installation

1. Ensure you have the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your OpenAI API key as an environment variable:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## Usage

### Command Line Interface

```bash
# Basic usage
python zip_visual_aesthetics.py 10001

# With custom API key
python zip_visual_aesthetics.py 90210 --api-key "your-api-key"

# Help
python zip_visual_aesthetics.py --help
```

### Programmatic Usage

```python
from zip_visual_aesthetics import ZIPVisualAestheticsGenerator

# Initialize the generator
generator = ZIPVisualAestheticsGenerator()

# Generate aesthetics for a ZIP code
aesthetics = generator.generate_aesthetics("10001")

# Access the results
print(aesthetics['visual_style'])    # e.g., "urban modern"
print(aesthetics['color_texture'])   # e.g., "smooth neutral"
print(aesthetics['art_style'])       # e.g., "contemporary minimal"
```

## Output Format

The program outputs exactly 3 lines in the specified format:

```
visual_style = "urban modern"
color_texture = "smooth neutral"
art_style = "contemporary minimal"
```

## Example Outputs

### New York (10001)
```
visual_style = "urban modern"
color_texture = "smooth neutral"
art_style = "contemporary minimal"
```

### Beverly Hills (90210)
```
visual_style = "luxury elegant"
color_texture = "rich warm"
art_style = "sophisticated refined"
```

### Miami Beach (33139)
```
visual_style = "tropical vibrant"
color_texture = "bright saturated"
art_style = "colorful energetic"
```

## Error Handling

The program handles various error scenarios:

- **Missing API Key**: Raises a clear error message
- **Invalid ZIP Code**: Validates 5-digit numeric format
- **API Errors**: Provides fallback aesthetics
- **Network Issues**: Graceful degradation with default values

## Testing

Run the test script to see the generator in action:

```bash
python test_zip_aesthetics.py
```

This will test multiple ZIP codes and demonstrate the functionality.

## Integration with Chewy Playback

This generator can be integrated into the Chewy Playback pipeline to provide region-specific visual aesthetics for personalized pet portraits and marketing materials.

## API Response Format

The OpenAI API is prompted to return responses in this exact format:

```
visual_style = "3-5 words describing visual style"
color_texture = "3-5 words describing color and texture"
art_style = "3-5 words describing art style"
```

## Fallback Values

When the API fails or returns unexpected results, the program uses these fallback aesthetics:

- **visual_style**: "modern clean"
- **color_texture**: "smooth neutral" 
- **art_style**: "contemporary minimal"

## License

This program is part of the Chewy Playback project and follows the same licensing terms. 