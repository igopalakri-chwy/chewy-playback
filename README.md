# Chewy Playback 🐾📦

### Relive a Year of Wags, Purrs, and Treats with Your Furry Family

---

## 🌟 Overview

**Chewy Playback** is a personalized, end-of-year interactive recap designed for pet parents to celebrate their pets' lives and highlight their journey with Chewy. Inspired by the success of Spotify Wrapped, this experience is tailored for Gen Z and Millennial customers and built on **Agentic AI** architecture.

It not only drives engagement but also serves as a growth engine for mobile adoption, customer retention, and new user acquisition—**all while making pet parents feel seen, heard, and loved**.

---

## 💡 Key Features

### 👤 Two Playback Modes
- **Generalized Playback**: For customers with incomplete profiles
- **Personalized Playback**: For active users with complete pet profiles

### 🤖 Powered by Agentic AI
- Purchase Attribution Agent
- Review Intelligence Agent
- Narrative Generation Agent
- Image Generation Agent

### 🧠 Smart AI Outputs
- Pet Personality Traits & Behavioral Cues
- Review-Based Sentiment Analysis
- LLM-Generated Letters "From Your Pet"
- Breed and Health Predictions (Future Scope)
- Vision Model Artwork (e.g., Holiday cards, badges)

---

## 🧱 Architecture Building Blocks
As seen in the *architecture diagram on page 6*:
- **Order History**
- **Pet Profiles**
- **Product Metadata**
- **Customer Reviews**
- **Pet-to-Order Matching**

LLMs and vision models are used to create:
- Custom summaries
- Pet-specific art
- Emotionally engaging narratives 

---

## 📱 Mobile-First & Social-Ready
- Personalized and visual playback experiences designed for app UX
- Shareable moments for Instagram, TikTok, and Facebook
- 1% share rate → 30,000+ organic reposts projected

---

## 🔬 Use of AI

- **Narrative Agent**: LLMs generate pet-specific summaries and stories
- **Vision Agent**: Creates visual cards and banners featuring the pet
- **Review Agent**: NLP to extract behavioral insights
- **Breed Agent** *(Future Scope)*: Predicts breed using vet notes, images, order history

---

## 🎁 Example Output
As shown on *pages 8–11*:
- A letter from your pet
- Highlighted eating and playing habits
- AI-generated pet personality (e.g., "Joyful Explorer")
- Top products and treats of the year
- Savings from Autoship
- Fun badges and holiday cards

---

## 🚀 Timeline (10 Weeks)
As detailed on *page 17*:
- **Weeks 1–2**: Ideation & Mock-up
- **Weeks 3–4**: Architecture Implementation
- **Weeks 5–6**: Agent & AI Integration
- **Week 7**: Internal Testing
- **Week 8**: Mobile UX + Sharing Layer
- **Weeks 9–10**: Final Touches & Launch

---

## 📈 Business Impact

From *page 18–19*:
- **App Downloads**: 10,000+ (worth $550K in saved CAC)
- **Pet Profile Completion**: +660K new profiles
- **Social Reach**: 30K reposts → 396K shares → 20K unit sales
- **User Growth**: 5% referral conversion with no added ad spend

---

## 🎯 Target Audience

- Gen Z and Millennial pet parents
- Especially those with multiple pets or incomplete profiles

---

## 🔮 Future Scope

- **Breed Ancestry Prediction** (page 16): Without DNA, infer likely ancestry using AI
- **Vet Note NLP**: Extract care tips and behavior patterns
- **Interactive Voice Messages from Pets**
- **In-app Gifting and Holiday Cards**

---

## 🛠 Tech Stack

- **Frontend**: React + Tailwind
- **Backend**: Node.js, Flask (for AI microservices)
- **AI/ML**: OpenAI GPT-4, Custom Vision Models, Python NLP (spaCy, HuggingFace)
- **Data**: Snowflake, S3, Chewy Internal APIs
- **Deployment**: AWS + Vercel

---

## 📁 Project Structure

```
chewy-playback/
├── Agents/                          # AI Agent implementations
│   ├── Review_and_Order_Intelligence_Agent/
│   │   ├── review_order_intelligence_agent.py    # LLM-based review analysis
│   │   └── preprocess_data.py                    # Data preprocessing utilities
│   ├── Narrative_Generation_Agent/
│   │   └── letter_prompt_generation.py           # Pet letter generation
│   └── Image_Generation_Agent/
│       ├── letter_agent.py                       # Image generation for letters
│       └── run_letters.py                        # Letter execution script
├── Data/                            # Sample data files
│   ├── order_history.csv            # Customer order data
│   └── qualifying_reviews.csv       # Customer review data
├── FrontEnd/                        # Frontend application (React)
├── chewy_playback_pipeline.py       # Main pipeline orchestration
├── test_pipeline.py                 # Pipeline testing script
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

### 🤖 Agent Descriptions

- **Review & Order Intelligence Agent**: Analyzes customer reviews using OpenAI's GPT-4 to extract pet characteristics, personality traits, and behavioral insights. Outputs structured JSON with customer-centric pet profiles.

- **Narrative Generation Agent**: Creates personalized letters "from your pet" using LLM prompts that incorporate pet-specific details and behavioral patterns.

- **Image Generation Agent**: Generates visual content like pet letters and personalized artwork using AI vision models.

---

## 👥 Contributors

Built by the **Chewy AI Innovator Intern Team** as part of the Unbound Innovator's Arena Challenge 2025.

---

## 📄 License

Prototype project for internal use only. Not open-sourced.

---

> "Your pet's digital life, lovingly narrated." 🐶🐱
