
BREED PREDICTOR DATA CLEANING REPORT
====================================

SUMMARY STATISTICS:
- Total Customers: 50
- Total Pets: 50
- Pets Successfully Cleaned: 47
- Total Purchases Analyzed: 937
- Contaminated Purchases Removed: 229
- Contamination Rate: 24.4%

CONTAMINATION BREAKDOWN:
- Cat Products: 123 purchases (53.7%)
- Fish Products: 33 purchases (14.4%)
- Reptile Products: 28 purchases (12.2%)
- Bird Products: 27 purchases (11.8%)
- Small Animal Products: 15 purchases (6.6%)
- Farm Animal Products: 3 purchases (1.3%)

HEAVILY CONTAMINATED PETS (17):
==================================================

Pet: Buddy (ID: Buddy_229099)
Customer: 229099
Contamination: 52.9%
Types: {'reptile_products': 9}
------------------------------

Pet: Charlee (ID: Charlee_4868964)
Customer: 4868964
Contamination: 48.6%
Types: {'fish_products': 12, 'small_animal_products': 3, 'cat_products': 2}
------------------------------

Pet: Pickles (ID: Pickles_13384731)
Customer: 13384731
Contamination: 34.0%
Types: {'fish_products': 11, 'bird_products': 7}
------------------------------

Pet: Cookie (ID: Cookie_16860194)
Customer: 16860194
Contamination: 55.0%
Types: {'cat_products': 10, 'reptile_products': 1}
------------------------------

Pet: Lady (ID: Lady_29187421)
Customer: 29187421
Contamination: 53.8%
Types: {'bird_products': 7}
------------------------------

Pet: Louys (ID: Louys_41297152)
Customer: 41297152
Contamination: 40.0%
Types: {'fish_products': 1, 'cat_products': 2, 'farm_animal_products': 1, 'reptile_products': 2}
------------------------------

Pet: Piper (ID: Piper_41426204)
Customer: 41426204
Contamination: 61.1%
Types: {'small_animal_products': 11}
------------------------------

Pet: Kona Simmons (ID: Kona Simmons_44619050)
Customer: 44619050
Contamination: 100.0%
Types: {'cat_products': 10}
------------------------------

Pet: Bubba (ID: Bubba_45899526)
Customer: 45899526
Contamination: 72.7%
Types: {'reptile_products': 8}
------------------------------

Pet: Agapi  (ID: Agapi _47929006)
Customer: 47929006
Contamination: 69.2%
Types: {'cat_products': 9}
------------------------------

Pet: Louie (ID: Louie_54090927)
Customer: 54090927
Contamination: 46.2%
Types: {'cat_products': 6}
------------------------------

Pet: Marley (ID: Marley_54727260)
Customer: 54727260
Contamination: 40.0%
Types: {'farm_animal_products': 1, 'fish_products': 7, 'cat_products': 3, 'reptile_products': 1}
------------------------------

Pet: moxie (ID: moxie_58396643)
Customer: 58396643
Contamination: 100.0%
Types: {'cat_products': 10}
------------------------------

Pet: Luke (ID: Luke_64943164)
Customer: 64943164
Contamination: 38.5%
Types: {'reptile_products': 5}
------------------------------

Pet: Thor (ID: Thor_76918953)
Customer: 76918953
Contamination: 57.1%
Types: {'cat_products': 6, 'small_animal_products': 1, 'reptile_products': 1}
------------------------------

Pet: Willow Reign (ID: Willow Reign_84404526)
Customer: 84404526
Contamination: 56.2%
Types: {'cat_products': 8, 'fish_products': 1}
------------------------------

Pet: BEAR (ID: BEAR_87480723)
Customer: 87480723
Contamination: 100.0%
Types: {'cat_products': 16}
------------------------------

RECOMMENDATIONS:
1. Review heavily contaminated pets - may be multi-pet households
2. Consider additional data validation rules
3. Monitor for new contamination patterns in future data
4. Re-train breed model with cleaned data

NEXT STEPS:
1. Update predictor to use cleaned data file
2. Re-train statistical breed model
3. Test predictions on cleaned data
4. Compare accuracy before/after cleaning
