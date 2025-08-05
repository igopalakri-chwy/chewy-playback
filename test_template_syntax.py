#!/usr/bin/env python3

from flask import Flask, render_template_string

app = Flask(__name__)

# Test the template syntax
test_template = """
{% set test_breeds = {'goldenRetriever': 25, 'frenchBulldog': 30, 'labradorRetriever': 20} %}
{% set breeds_list = test_breeds.items() | list %}
First 2 breeds: {{ breeds_list[:2] | length }}
Third breed: {{ breeds_list[2] if breeds_list | length > 2 else 'None' }}
"""

try:
    result = render_template_string(test_template)
    print("✅ Template syntax is valid!")
    print("Result:", result)
except Exception as e:
    print("❌ Template syntax error:", e) 