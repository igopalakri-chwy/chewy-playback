from chewy_playback_pipeline import ChewyPlaybackPipeline

pipeline = ChewyPlaybackPipeline()
agent = pipeline.review_agent
orders_df = pipeline._get_cached_customer_orders_dataframe('887148270')
reviews_df = pipeline._get_cached_customer_reviews_dataframe('887148270')
pets_df = pipeline._get_cached_customer_pets_dataframe('887148270')

print('pets_df columns:', pets_df.columns.tolist())

pet_names = pets_df['PetName'].unique()

for pet in pet_names:
    # Get structured pet data for this pet
    pet_profile_row = pets_df[pets_df['PetName'] == pet].iloc[0] if not pets_df[pets_df['PetName'] == pet].empty else None
    
    structured_pet_data = {}
    if pet_profile_row is not None:
        structured_pet_data = {
            'PetType': pet_profile_row.get('PetType', 'UNK'),
            'PetBreed': pet_profile_row.get('PetBreed', 'UNK'),
            'Gender': pet_profile_row.get('Gender', 'UNK'),
            'PetAge': pet_profile_row.get('PetAge', 'UNK'),
            'Weight': pet_profile_row.get('Weight', 'UNK'),
            'SizeCategory': 'UNK'  # Not available in current Snowflake data
        }
    
    # For each pet, get reviews mentioning the pet name (case-insensitive)
    pet_reviews = reviews_df[reviews_df['ReviewText'].str.contains(pet, case=False, na=False)]
    
    # Test the new context preparation with structured data
    context = agent._prepare_llm_context(pet_reviews, orders_df, pet, structured_pet_data)
    print(f'Pet: {pet} | Context length (chars): {len(context)} | Context length (words): {len(context.split())}')
    print('---')
    print(context[:1000])
    print('...')
    print('---\n') 