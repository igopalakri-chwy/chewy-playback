# Chewy Playback Pipeline - Project Memory

## Project Overview
AI-powered pet intelligence pipeline that analyzes customer data to create personalized pet profiles and recommendations. Uses Snowflake database integration with LLM analysis for comprehensive pet insights.

## Architecture Overview

### Main Pipeline (`chewy_playback_pipeline.py`)
- **Entry Point**: Orchestrates entire pipeline execution
- **Database**: Connects to Snowflake for customer data retrieval
- **Caching System**: Single cache entry per customer with 10 optimized queries
- **Dual Agent Architecture**:
  - `ReviewOrderIntelligenceAgent`: For customers WITH reviews (enhanced pet detection)
  - `OrderIntelligenceAgent`: For customers WITHOUT reviews (order-only analysis)
- **Output**: Generates enriched pet profiles, letters, portraits, and metadata

### Agent Structure
```
Final_Pipeline/
├── chewy_playback_pipeline.py          # Main orchestrator
├── Agents/
│   ├── Review_and_Order_Intelligence_Agent/
│   │   └── review_order_intelligence_agent.py  # Enhanced LLM + pet detection
│   ├── Order_Intelligence_Agent/
│   │   └── order_intelligence_agent.py         # Order-only analysis
│   └── [Other specialized agents...]
├── Output/
│   └── [customer_id]/                          # Per-customer results
└── customer_queries.json                       # Snowflake query definitions
```

## Enhanced Pet Detection System (MAJOR RECENT UPDATE)

### Core Innovation: LLM + Hashmap Approach
Replaced hard-coded regex patterns with intelligent LLM analysis that detects three types of additional pets:

#### 1. Count-Based Detection
- **Scenario**: Customer has 2 cats in Snowflake, review says "my 3 cats"
- **Action**: Creates `Additional_Cat_1` 
- **Method**: `count_based_detection`

#### 2. Named Pet Detection  
- **Scenario**: Review mentions "Charlie loves this toy" but Charlie not in profiles
- **Action**: Creates pet profile named `Charlie` with detected species
- **Method**: `named_pet_detection`

#### 3. Unnamed Species Detection
- **Scenario**: Review says "my dog" but no dogs exist in profiles  
- **Action**: Creates `UNK_DOG` profile
- **Method**: `unnamed_species_detection`

### Key Methods (ReviewOrderIntelligenceAgent)
- `_detect_additional_pets_with_llm()`: Main detection orchestrator with order context
- `_analyze_pet_ownership_with_llm()`: GPT-4 analysis returning structured data with species inference
- `_infer_species_from_orders()`: NEW - Infers pet species from purchase history patterns
- `analyze_customer_with_cached_data()`: Pipeline integration point with enhanced detection

## File Structure & Common Paths

### Critical Files
- `/Users/ageng/chewy-playback/Final_Pipeline/chewy_playback_pipeline.py`
- `/Users/ageng/chewy-playback/Final_Pipeline/Agents/Review_and_Order_Intelligence_Agent/review_order_intelligence_agent.py`
- `/Users/ageng/chewy-playback/Final_Pipeline/customer_queries.json`
- `/Users/ageng/chewy-playback/Final_Pipeline/Output/[customer_id]/enriched_pet_profile.json`

### Output Structure Per Customer
```
Output/[customer_id]/
├── enriched_pet_profile.json      # Main pet profiles with detection metadata
├── pet_letters.txt                # Personalized letters
├── collective_pet_portrait.png    # AI-generated portrait
├── personality_badge.json         # Pet personality analysis
├── predicted_breed.json           # Breed prediction results
├── visual_prompt.txt              # Portrait generation prompt
└── zip_aesthetics.json           # Visual styling metadata
```

## Coding Conventions

### General Rules
- **NO COMMENTS**: Never add code comments unless explicitly requested by user
- **Concise Responses**: Keep explanations under 4 lines unless asked for detail
- **Existing Patterns**: Always check existing code patterns before implementing
- **Library Usage**: Never assume libraries are available - check imports/package.json first

### Error Handling Patterns
```python
try:
    # Main logic
    result = some_operation()
except Exception as e:
    logger.warning(f"Operation failed, using fallback: {e}")
    result = fallback_value
```

### LLM Integration Patterns
```python
# Standard LLM call structure
client = openai.OpenAI(api_key=self.openai_api_key)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[...],
    temperature=0.1,
    max_tokens=2000
)
```

### Data Structure Conventions
```python
# Pet profile structure with detection metadata
pet_profile = {
    "PetName": "string",
    "PetType": "string", 
    "DetectionSource": "review_analysis",      # For detected pets
    "DetectionMethod": "count_based_detection", # Specific detection type
    "DetectionType": "count_based"             # Category of detection
}
```

## Pipeline-Specific Terminology

### Detection Methods
- **count_based_detection**: Detected from quantity mentions ("my 3 cats")
- **named_pet_detection**: Detected from specific names ("Charlie loves this")  
- **unnamed_species_detection**: Detected from species mentions ("my dog")

### Pet Types & Naming
- **Additional_[Species]_[Number]**: Count-based additional pets (e.g., `Additional_Cat_1`)
- **UNK_[SPECIES]**: Unnamed species pets (e.g., `UNK_DOG`)
- **[Name]**: Named pets detected from reviews (e.g., `Charlie`)

### Data Flow Terms
- **Snowflake Cache**: Single optimized data fetch per customer (10 queries)
- **Known Pet Profiles**: Pets from Snowflake database
- **Additional Pets**: Pets detected from review analysis
- **Enhanced Pet Detection**: The complete LLM + hashmap system

### Agent Types
- **ReviewOrderIntelligenceAgent**: For customers with reviews (enhanced detection)
- **OrderIntelligenceAgent**: For customers without reviews (order-only)

## Recent Major Changes Completed

### 1. Enhanced Pet Detection Implementation
- Completely rewrote `detect_additional_pets_from_reviews` method
- Replaced regex patterns with GPT-4 LLM analysis
- Added hashmap comparison of known vs detected pet counts
- Implemented three distinct detection scenarios with proper metadata

### 2. Code Cleanup & Organization  
- Removed dead code (`_select_priority_reviews` method)
- Added comprehensive documentation and section headers
- Extracted constants (`PRIORITY_REVIEW_KEYWORDS`)
- Improved error handling consistency across all methods
- Streamlined method organization and data flow

### 3. Pipeline Integration
- Enhanced `analyze_customer_with_cached_data()` method
- Added detection metadata to output profiles
- Implemented proper review filtering for different pet types
- Added comprehensive logging for detection results

### 4. Species Inference Enhancement (LATEST UPDATE - CURRENT STATE)
- **Problem Solved**: Handle pet names mentioned in reviews without explicit species
- **New Method**: `_infer_species_from_orders()` - analyzes order history for species clues
- **Enhanced LLM Prompt**: Now accepts "unknown" species and tries context inference
- **Smart Confidence Scoring**:
  - Named pet with known/inferred species: `0.8` confidence
  - Named pet with unknown species: `0.5` confidence (adjusted for uncertainty)
- **Order-Based Inference**: Uses cat litter, dog treats, bird seed patterns to infer species
- **Updated Validation**: Added "unknown" as valid species type in processing logic
- **Enhanced Data Flow**: All detection methods now pass order context for better species inference

## Current Implementation Status
- ✅ **Enhanced pet detection system**: Fully implemented and production-ready
- ✅ **Species inference system**: Complete with order-based inference and confidence scoring
- ✅ **Code cleanup**: All dead code removed, documentation comprehensive
- ✅ **Pipeline integration**: All agents working with cached Snowflake data
- 🔄 **Ready for testing**: New species inference logic ready for validation

## Development Guidelines

### When Working on This Project
1. **Check existing patterns** before implementing new features
2. **Use the enhanced pet detection system** for any review analysis
3. **Follow the dual agent architecture** - don't mix review and order-only logic
4. **Maintain Snowflake caching** - use `_get_all_customer_data()` method
5. **Include detection metadata** for any additional pets created
6. **Test with real customer data** from the Output directory examples

### Testing & Verification
- Use `test_enhanced_pet_detection.py` for pet detection testing
- Check Output directory for real customer examples
- Verify Snowflake queries work with existing cache structure
- Ensure LLM analysis handles edge cases gracefully

## Environment Requirements
- **OpenAI API Key**: Required for LLM analysis (`OPENAI_API_KEY`)
- **Snowflake Connection**: Database credentials for customer data
- **Python Dependencies**: pandas, openai, snowflake-connector-python

This pipeline represents a significant evolution from simple pattern matching to intelligent AI-powered pet detection that dramatically improves data quality and customer profile completeness.