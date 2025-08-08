# Chewy Playback - Pet Personalization Platform

A comprehensive pet personalization platform that creates personalized experiences for Chewy customers based on their order history, reviews, and pet data. The platform includes a web interface, AI-powered pipeline, and intelligent agents for breed prediction, image generation, and narrative creation.

## 🎯 Overview

This project consists of two main components:

1. **Web Application** - Flask-based web interface for viewing and triggering personalized pet experiences
2. **AI Pipeline** - Python-based pipeline that processes customer data and generates personalized content

## 🏗️ Project Structure

```
chewy-playback/
├── app.py                          # Main Flask web application
├── run_app.py                      # Application launcher script
├── requirements.txt                # Python dependencies
├── package.json                    # Node.js dependencies (minimal)
├── templates/                      # HTML templates for web interface
├── static/                         # CSS, JS, and static assets
├── personalityzipped/              # Personality badge images
├── Final_Pipeline/                 # AI pipeline and agents
│   ├── chewy_playback_pipeline.py  # Main pipeline script
│   ├── snowflake_data_connector.py # Snowflake database connector
│   ├── customer_queries.json       # SQL query templates
│   ├── Agents/                     # AI agents
│   │   ├── Breed_Predictor_Agent/  # Dog breed prediction
│   │   ├── Image_Generation_Agent/ # DALL-E image generation
│   │   ├── Narrative_Generation_Agent/ # Story generation
│   │   └── Review_and_Order_Intelligence_Agent/ # Data analysis
│   └── Output/                     # Generated customer data
└── react-breed-component/          # React component (optional)
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (recommended: Python 3.11+)
- **Node.js 18+** (for optional React component)
- **OpenAI API key** (for AI features)
- **Snowflake credentials** (for customer data)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd chewy-playback

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (optional)
npm install
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```bash
# OpenAI API Key (required for AI features)
OPENAI_API_KEY="your-openai-api-key-here"

# Snowflake Credentials (required for customer data)
SNOWFLAKE_USER="your-snowflake-username"
SNOWFLAKE_ACCOUNT="your-snowflake-account"
SNOWFLAKE_WAREHOUSE="your-warehouse"
SNOWFLAKE_DATABASE="your-database"
SNOWFLAKE_SCHEMA="your-schema"
SNOWFLAKE_AUTHENTICATOR="externalbrowser"
```

### 4. Run the Application

#### Option A: Using the launcher script (Recommended)
```bash
python run_app.py
```

#### Option B: Direct Flask execution
```bash
python app.py
```

#### Option C: Flask development server
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

The web application will be available at: **http://localhost:5000**

## 🌐 Web Application Features

### Main Interface
- **Customer List**: View all processed customers
- **Experience Viewer**: View personalized pet experiences
- **Pipeline Trigger**: Manually trigger AI pipeline for specific customers
- **Real-time Status**: Check pipeline progress and status

### Key Pages
- `/` - Home page with customer overview
- `/customers` - List of all customers with data
- `/experience/<customer_id>` - Personalized experience for specific customer
- `/api/customer/<customer_id>` - JSON API for customer data
- `/api/trigger-pipeline/<customer_id>` - Trigger pipeline for customer

## 🤖 AI Pipeline Features

### Intelligent Agent System
- **Breed Predictor Agent**: Predicts dog breeds from images and descriptions
- **Image Generation Agent**: Creates personalized pet portraits using DALL-E
- **Narrative Generation Agent**: Generates personalized pet stories and letters
- **Review & Order Intelligence Agent**: Analyzes customer data and preferences

### Pipeline Capabilities
- **Automatic Detection**: Detects customers with/without reviews
- **Location Personalization**: ZIP code-based background personalization
- **Order Count Filtering**: Intelligent routing based on order history
- **Confidence Scoring**: Quality assessment of generated content
- **Generic Playback**: Fallback for customers with limited data

### Running the Pipeline

#### Single Customer
```bash
cd Final_Pipeline
python chewy_playback_pipeline.py --customers 1183376
```

#### Multiple Customers
```bash
cd Final_Pipeline
python chewy_playback_pipeline.py --customers 1183376 1317924 2209529
```

#### With Custom API Key
```bash
cd Final_Pipeline
python chewy_playback_pipeline.py --customers 1183376 --api-key "your-api-key"
```

## 📊 Data Processing

### Customer Data Types
1. **Order History**: Product purchases, frequencies, patterns
2. **Review Data**: Customer reviews and sentiment analysis
3. **Pet Information**: Breed, age, preferences
4. **Location Data**: ZIP code for regional personalization

### Output Structure
```
Final_Pipeline/Output/{customer_id}/
├── enriched_pet_profile.json      # Complete pet profiles
├── pet_letters.txt                # Personalized letters
├── visual_prompt.txt              # DALL-E prompts
├── personality_badge.json         # Assigned personality
├── zip_aesthetics.json           # Location aesthetics
├── images/
│   └── collective_pet_portrait.png # Generated images
├── predicted_breed.json          # Breed predictions
├── food_fun_fact.json            # Food consumption facts
└── [generic_data_files]          # For customers with <5 orders
```

## 🎨 Personalization Features

### Location-Based Personalization
- **ZIP Code Integration**: Extracts customer location from Snowflake
- **City-Specific Landmarks**: Space Needle (Seattle), Hollywood Sign (LA), etc.
- **State Backgrounds**: Mount Rainier (WA), Grand Canyon (AZ), etc.
- **Regional Aesthetics**: Location-driven color schemes and styles

### Personality Badges
- **Athlete**: Active, energetic pets
- **Cuddler**: Affectionate, loving pets
- **Explorer**: Curious, adventurous pets
- **Guardian**: Protective, loyal pets
- **Scholar**: Intelligent, trainable pets
- And more...

### Content Generation
- **Personalized Letters**: Pet-written letters to owners
- **Visual Prompts**: Location-aware DALL-E prompts
- **Food Fun Facts**: State-specific consumption analogies
- **Breed Predictions**: AI-powered breed identification

## 🔧 Configuration

### Environment Variables
All sensitive data should be stored in the `.env` file:

```bash
# Required for AI features
OPENAI_API_KEY="sk-..."

# Required for customer data
SNOWFLAKE_USER="username"
SNOWFLAKE_ACCOUNT="account"
SNOWFLAKE_WAREHOUSE="warehouse"
SNOWFLAKE_DATABASE="database"
SNOWFLAKE_SCHEMA="schema"
SNOWFLAKE_AUTHENTICATOR="externalbrowser"
```

### Pipeline Configuration
- **Minimum Orders**: 5 orders required for personalized playback
- **Confidence Threshold**: 0.6 minimum confidence score
- **Location API**: Uses zippopotam.us for ZIP code lookup
- **Image Generation**: DALL-E 3 for high-quality pet portraits

## 🐛 Troubleshooting

### Common Issues

#### 1. Flask Installation Issues
```bash
# If Flask isn't installing properly
pip install --upgrade pip
pip install Flask==2.3.3
```

#### 2. OpenAI API Issues
- Verify your API key is correct
- Check API key has sufficient credits
- Ensure API key has access to DALL-E 3

#### 3. Snowflake Connection Issues
- Verify credentials in `.env` file
- Check network connectivity
- Ensure proper permissions

#### 4. Pipeline Errors
```bash
# Check pipeline logs
cd Final_Pipeline
python chewy_playback_pipeline.py --customers 1183376 --verbose
```

### Debug Mode
```bash
# Enable debug mode for detailed logging
export FLASK_DEBUG=1
python app.py
```

## 📈 Performance

### Optimization Features
- **Data Caching**: Efficient data loading and caching
- **Background Processing**: Non-blocking pipeline execution
- **Error Isolation**: Customer-specific error handling
- **Progress Tracking**: Real-time pipeline status updates

### Scalability
- **Individual Processing**: Customers processed separately
- **Resource Management**: Efficient memory and API usage
- **Batch Processing**: Support for multiple customers
- **Error Recovery**: Graceful handling of failures

## 🔒 Security

### Data Protection
- **Environment Variables**: Sensitive data stored in `.env`
- **Git Ignore**: `.env` file automatically ignored
- **API Key Security**: Secure API key management
- **Data Validation**: Input validation and sanitization

### Access Control
- **Snowflake Authentication**: Secure database access
- **API Rate Limiting**: Respectful API usage
- **Error Handling**: Secure error messages

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Standards
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex logic
- Include error handling

## 📝 License

This project is proprietary and confidential. All rights reserved.

## 🆘 Support

### Getting Help
1. Check the troubleshooting section above
2. Review the pipeline logs for errors
3. Verify environment configuration
4. Test with a known working customer ID

### Contact
For technical support or questions, please contact the development team.

---

## 🎉 Quick Commands Reference

```bash
# Start the web application
python run_app.py

# Run pipeline for a customer
cd Final_Pipeline && python chewy_playback_pipeline.py --customers 1183376

# Check customer data
ls Final_Pipeline/Output/

# View logs
tail -f Final_Pipeline/Output/pipeline.log

# Install dependencies
pip install -r requirements.txt

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

**Happy coding! 🐕🐱** 