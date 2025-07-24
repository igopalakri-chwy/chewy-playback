#!/usr/bin/env python3
"""
Location Background Generator
Generates location-specific background descriptions for personalized pet images.
"""

import requests
from typing import Dict, Tuple, Optional, List
import json


class LocationBackgroundGenerator:
    """Generate location-specific background descriptions for personalized images."""
    
    def __init__(self):
        # Major cities with iconic landmarks
        self.major_cities = {
            'New York': {
                'landmarks': ['Empire State Building', 'Statue of Liberty', 'Brooklyn Bridge', 'Times Square'],
                'backgrounds': [
                    'New York City skyline with the Empire State Building in the background',
                    'Brooklyn Bridge spanning the East River',
                    'Times Square with bright neon lights',
                    'Central Park with city skyline visible'
                ]
            },
            'Los Angeles': {
                'landmarks': ['Hollywood Sign', 'Griffith Observatory', 'Santa Monica Pier', 'Venice Beach'],
                'backgrounds': [
                    'Hollywood Sign on the hillside',
                    'Santa Monica Pier with Pacific Ocean',
                    'Venice Beach boardwalk',
                    'Griffith Observatory overlooking the city'
                ]
            },
            'Chicago': {
                'landmarks': ['Willis Tower', 'Millennium Park', 'Navy Pier', 'Cloud Gate'],
                'backgrounds': [
                    'Chicago skyline with Willis Tower',
                    'Millennium Park with Cloud Gate sculpture',
                    'Navy Pier extending into Lake Michigan',
                    'Chicago River with city architecture'
                ]
            },
            'Miami': {
                'landmarks': ['South Beach', 'Art Deco District', 'Biscayne Bay', 'Vizcaya Museum'],
                'backgrounds': [
                    'South Beach with palm trees and ocean',
                    'Art Deco buildings on Ocean Drive',
                    'Biscayne Bay with Miami skyline',
                    'Tropical beach scene with turquoise water'
                ]
            },
            'Las Vegas': {
                'landmarks': ['Bellagio Fountains', 'Stratosphere Tower', 'Fremont Street', 'Red Rock Canyon'],
                'backgrounds': [
                    'Las Vegas Strip with Bellagio Fountains',
                    'Fremont Street Experience',
                    'Red Rock Canyon desert landscape',
                    'Neon lights and casino architecture'
                ]
            },
            'Seattle': {
                'landmarks': ['Space Needle', 'Pike Place Market', 'Mount Rainier', 'Puget Sound'],
                'backgrounds': [
                    'Space Needle with Seattle skyline',
                    'Pike Place Market with waterfront',
                    'Mount Rainier visible through window',
                    'Puget Sound with ferry boats'
                ]
            },
            'San Francisco': {
                'landmarks': ['Golden Gate Bridge', 'Alcatraz', 'Fisherman\'s Wharf', 'Coit Tower'],
                'backgrounds': [
                    'Golden Gate Bridge spanning the bay',
                    'San Francisco skyline with Coit Tower',
                    'Fisherman\'s Wharf with sea lions',
                    'Alcatraz Island in the bay'
                ]
            },
            'Austin': {
                'landmarks': ['Texas State Capitol', 'Lady Bird Lake', 'Barton Springs', 'Mount Bonnell'],
                'backgrounds': [
                    'Texas State Capitol building',
                    'Lady Bird Lake with downtown skyline',
                    'Barton Springs Pool',
                    'Mount Bonnell overlooking the city'
                ]
            },
            'Nashville': {
                'landmarks': ['Parthenon', 'Broadway', 'Ryman Auditorium', 'Country Music Hall of Fame'],
                'backgrounds': [
                    'Parthenon replica in Centennial Park',
                    'Broadway with neon music signs',
                    'Ryman Auditorium',
                    'Country Music Hall of Fame'
                ]
            },
            'New Orleans': {
                'landmarks': ['French Quarter', 'Jackson Square', 'Garden District', 'Mississippi River'],
                'backgrounds': [
                    'French Quarter with wrought iron balconies',
                    'Jackson Square with St. Louis Cathedral',
                    'Garden District mansions',
                    'Mississippi River with steamboats'
                ]
            },
            'Portland': {
                'landmarks': ['Powell\'s Books', 'Forest Park', 'Mount Hood', 'Willamette River'],
                'backgrounds': [
                    'Powell\'s Books iconic building',
                    'Forest Park with lush greenery',
                    'Mount Hood visible in distance',
                    'Willamette River with bridges'
                ]
            },
            'Denver': {
                'landmarks': ['Red Rocks Amphitheatre', 'Rocky Mountains', 'Union Station', 'Denver Art Museum'],
                'backgrounds': [
                    'Red Rocks Amphitheatre',
                    'Rocky Mountains with snow-capped peaks',
                    'Union Station with historic architecture',
                    'Denver skyline with mountains'
                ]
            },
            'Phoenix': {
                'landmarks': ['Camelback Mountain', 'Desert Botanical Garden', 'Papago Park', 'South Mountain'],
                'backgrounds': [
                    'Camelback Mountain silhouette',
                    'Desert Botanical Garden with cacti',
                    'Papago Park red rock formations',
                    'South Mountain with desert landscape'
                ]
            },
            'San Diego': {
                'landmarks': ['Balboa Park', 'Coronado Bridge', 'La Jolla Cove', 'Gaslamp Quarter'],
                'backgrounds': [
                    'Balboa Park with Spanish architecture',
                    'Coronado Bridge spanning the bay',
                    'La Jolla Cove with Pacific Ocean',
                    'Gaslamp Quarter historic district'
                ]
            },
            'Boston': {
                'landmarks': ['Fenway Park', 'Freedom Trail', 'Boston Harbor', 'Beacon Hill'],
                'backgrounds': [
                    'Fenway Park with Green Monster',
                    'Freedom Trail with historic buildings',
                    'Boston Harbor with sailboats',
                    'Beacon Hill with cobblestone streets'
                ]
            },
            'Philadelphia': {
                'landmarks': ['Liberty Bell', 'Independence Hall', 'Rocky Steps', 'Reading Terminal Market'],
                'backgrounds': [
                    'Liberty Bell with Independence Hall',
                    'Philadelphia Museum of Art steps',
                    'Reading Terminal Market',
                    'Philadelphia skyline'
                ]
            },
            'Washington': {
                'landmarks': ['White House', 'Lincoln Memorial', 'Capitol Building', 'National Mall'],
                'backgrounds': [
                    'White House with Washington Monument',
                    'Lincoln Memorial reflecting pool',
                    'Capitol Building dome',
                    'National Mall with cherry blossoms'
                ]
            },
            'Atlanta': {
                'landmarks': ['Centennial Olympic Park', 'Stone Mountain', 'Atlanta BeltLine', 'Fox Theatre'],
                'backgrounds': [
                    'Centennial Olympic Park fountains',
                    'Stone Mountain with carving',
                    'Atlanta BeltLine with murals',
                    'Fox Theatre marquee'
                ]
            },
            'Dallas': {
                'landmarks': ['Reunion Tower', 'Dallas Arboretum', 'Deep Ellum', 'White Rock Lake'],
                'backgrounds': [
                    'Reunion Tower with Dallas skyline',
                    'Dallas Arboretum gardens',
                    'Deep Ellum with street art',
                    'White Rock Lake with city view'
                ]
            },
            'Houston': {
                'landmarks': ['Space Center Houston', 'Museum District', 'Buffalo Bayou', 'Rice University'],
                'backgrounds': [
                    'Space Center Houston with rockets',
                    'Museum District with cultural buildings',
                    'Buffalo Bayou Park',
                    'Rice University campus'
                ]
            },
            'Orlando': {
                'landmarks': ['Walt Disney World', 'Universal Studios', 'Lake Eola', 'International Drive'],
                'backgrounds': [
                    'Cinderella Castle at Disney World',
                    'Universal Studios entrance',
                    'Lake Eola with swan boats',
                    'International Drive attractions'
                ]
            }
        }
        
        # State landmarks for when city is not in major cities list
        self.state_landmarks = {
            'CA': {
                'landmarks': ['Golden Gate Bridge', 'Yosemite National Park', 'Redwood Forest', 'Big Sur'],
                'backgrounds': [
                    'Golden Gate Bridge spanning San Francisco Bay',
                    'Yosemite Valley with Half Dome',
                    'Redwood Forest with towering trees',
                    'Big Sur coastline with Pacific Ocean'
                ]
            },
            'NY': {
                'landmarks': ['Statue of Liberty', 'Niagara Falls', 'Adirondack Mountains', 'Finger Lakes'],
                'backgrounds': [
                    'Statue of Liberty in New York Harbor',
                    'Niagara Falls with mist',
                    'Adirondack Mountains with lakes',
                    'Finger Lakes with vineyards'
                ]
            },
            'TX': {
                'landmarks': ['Alamo', 'Big Bend National Park', 'Padre Island', 'Palo Duro Canyon'],
                'backgrounds': [
                    'Alamo Mission in San Antonio',
                    'Big Bend National Park desert',
                    'Padre Island National Seashore',
                    'Palo Duro Canyon red rocks'
                ]
            },
            'FL': {
                'landmarks': ['Everglades', 'Key West', 'Daytona Beach', 'Crystal River'],
                'backgrounds': [
                    'Everglades with alligators',
                    'Key West sunset',
                    'Daytona Beach with racing heritage',
                    'Crystal River with manatees'
                ]
            },
            'CO': {
                'landmarks': ['Rocky Mountains', 'Garden of the Gods', 'Mesa Verde', 'Great Sand Dunes'],
                'backgrounds': [
                    'Rocky Mountains with snow-capped peaks',
                    'Garden of the Gods red rocks',
                    'Mesa Verde cliff dwellings',
                    'Great Sand Dunes National Park'
                ]
            },
            'WA': {
                'landmarks': ['Mount Rainier', 'Olympic National Park', 'Mount St. Helens', 'San Juan Islands'],
                'backgrounds': [
                    'Mount Rainier with wildflowers',
                    'Olympic National Park rainforest',
                    'Mount St. Helens volcano',
                    'San Juan Islands with orcas'
                ]
            },
            'OR': {
                'landmarks': ['Crater Lake', 'Columbia River Gorge', 'Cannon Beach', 'Mount Hood'],
                'backgrounds': [
                    'Crater Lake with blue water',
                    'Columbia River Gorge waterfalls',
                    'Cannon Beach with Haystack Rock',
                    'Mount Hood with Timberline Lodge'
                ]
            },
            'AZ': {
                'landmarks': ['Grand Canyon', 'Sedona Red Rocks', 'Saguaro National Park', 'Antelope Canyon'],
                'backgrounds': [
                    'Grand Canyon with Colorado River',
                    'Sedona red rock formations',
                    'Saguaro cacti in desert',
                    'Antelope Canyon slot canyon'
                ]
            },
            'UT': {
                'landmarks': ['Arches National Park', 'Zion National Park', 'Bryce Canyon', 'Salt Lake'],
                'backgrounds': [
                    'Arches National Park with Delicate Arch',
                    'Zion National Park with red cliffs',
                    'Bryce Canyon hoodoos',
                    'Great Salt Lake with mountains'
                ]
            },
            'NV': {
                'landmarks': ['Las Vegas Strip', 'Red Rock Canyon', 'Lake Tahoe', 'Valley of Fire'],
                'backgrounds': [
                    'Las Vegas Strip with neon lights',
                    'Red Rock Canyon desert',
                    'Lake Tahoe with mountains',
                    'Valley of Fire red sandstone'
                ]
            },
            'MT': {
                'landmarks': ['Glacier National Park', 'Yellowstone National Park', 'Big Sky', 'Flathead Lake'],
                'backgrounds': [
                    'Glacier National Park with glaciers',
                    'Yellowstone with geysers',
                    'Big Sky mountain resort',
                    'Flathead Lake with mountains'
                ]
            },
            'WY': {
                'landmarks': ['Yellowstone National Park', 'Grand Teton National Park', 'Devils Tower', 'Bighorn Mountains'],
                'backgrounds': [
                    'Yellowstone with Old Faithful',
                    'Grand Teton peaks',
                    'Devils Tower monolith',
                    'Bighorn Mountains with wildflowers'
                ]
            },
            'ID': {
                'landmarks': ['Craters of the Moon', 'Sawtooth Mountains', 'Shoshone Falls', 'Sun Valley'],
                'backgrounds': [
                    'Craters of the Moon lava fields',
                    'Sawtooth Mountains with lakes',
                    'Shoshone Falls on Snake River',
                    'Sun Valley ski resort'
                ]
            },
            'AK': {
                'landmarks': ['Denali', 'Glacier Bay', 'Northern Lights', 'Kenai Fjords'],
                'backgrounds': [
                    'Denali (Mount McKinley)',
                    'Glacier Bay with icebergs',
                    'Northern Lights in night sky',
                    'Kenai Fjords with glaciers'
                ]
            },
            'HI': {
                'landmarks': ['Diamond Head', 'Waikiki Beach', 'Volcanoes National Park', 'Na Pali Coast'],
                'backgrounds': [
                    'Diamond Head crater',
                    'Waikiki Beach with palm trees',
                    'Volcanoes National Park with lava',
                    'Na Pali Coast cliffs'
                ]
            },
            'LA': {
                'landmarks': ['French Quarter', 'Bourbon Street', 'Mississippi River', 'Bayou Country'],
                'backgrounds': [
                    'French Quarter with jazz music',
                    'Bourbon Street with balconies',
                    'Mississippi River with steamboats',
                    'Bayou with cypress trees'
                ]
            },
            'TN': {
                'landmarks': ['Great Smoky Mountains', 'Nashville Music Row', 'Graceland', 'Dollywood'],
                'backgrounds': [
                    'Great Smoky Mountains with mist',
                    'Nashville Music Row with guitars',
                    'Graceland mansion',
                    'Dollywood theme park'
                ]
            },
            'NC': {
                'landmarks': ['Blue Ridge Mountains', 'Outer Banks', 'Biltmore Estate', 'Great Smoky Mountains'],
                'backgrounds': [
                    'Blue Ridge Parkway with mountains',
                    'Outer Banks with lighthouses',
                    'Biltmore Estate mansion',
                    'Great Smoky Mountains with waterfalls'
                ]
            },
            'SC': {
                'landmarks': ['Myrtle Beach', 'Charleston Historic District', 'Hilton Head', 'Table Rock'],
                'backgrounds': [
                    'Myrtle Beach with boardwalk',
                    'Charleston with historic homes',
                    'Hilton Head Island beaches',
                    'Table Rock Mountain'
                ]
            },
            'GA': {
                'landmarks': ['Stone Mountain', 'Savannah Historic District', 'Okefenokee Swamp', 'Blue Ridge Mountains'],
                'backgrounds': [
                    'Stone Mountain with carving',
                    'Savannah with oak trees',
                    'Okefenokee Swamp with alligators',
                    'Blue Ridge Mountains with trails'
                ]
            },
            'AL': {
                'landmarks': ['Gulf Shores', 'Birmingham Civil Rights District', 'Huntsville Space Center', 'Mobile Bay'],
                'backgrounds': [
                    'Gulf Shores white sand beaches',
                    'Birmingham Civil Rights Institute',
                    'Huntsville Space Center rockets',
                    'Mobile Bay with sunset'
                ]
            },
            'MS': {
                'landmarks': ['Gulf Coast', 'Vicksburg National Military Park', 'Natchez Trace', 'Mississippi River'],
                'backgrounds': [
                    'Gulf Coast with casinos',
                    'Vicksburg battlefield',
                    'Natchez Trace Parkway',
                    'Mississippi River with steamboats'
                ]
            },
            'AR': {
                'landmarks': ['Hot Springs National Park', 'Buffalo National River', 'Crater of Diamonds', 'Ozark Mountains'],
                'backgrounds': [
                    'Hot Springs National Park',
                    'Buffalo National River',
                    'Crater of Diamonds State Park',
                    'Ozark Mountains with lakes'
                ]
            },
            'OK': {
                'landmarks': ['Oklahoma City Memorial', 'Tulsa Art Deco District', 'Wichita Mountains', 'Route 66'],
                'backgrounds': [
                    'Oklahoma City Memorial',
                    'Tulsa Art Deco buildings',
                    'Wichita Mountains Wildlife Refuge',
                    'Route 66 historic highway'
                ]
            },
            'KS': {
                'landmarks': ['Flint Hills', 'Kansas Cosmosphere', 'Tallgrass Prairie', 'Monument Rocks'],
                'backgrounds': [
                    'Flint Hills with tallgrass',
                    'Kansas Cosmosphere space museum',
                    'Tallgrass Prairie National Preserve',
                    'Monument Rocks chalk formations'
                ]
            },
            'NE': {
                'landmarks': ['Chimney Rock', 'Scotts Bluff', 'Sandhills', 'Platte River'],
                'backgrounds': [
                    'Chimney Rock landmark',
                    'Scotts Bluff National Monument',
                    'Sandhills with prairie grass',
                    'Platte River with sandhill cranes'
                ]
            },
            'SD': {
                'landmarks': ['Mount Rushmore', 'Badlands', 'Black Hills', 'Crazy Horse Memorial'],
                'backgrounds': [
                    'Mount Rushmore with presidents',
                    'Badlands National Park',
                    'Black Hills with pine trees',
                    'Crazy Horse Memorial'
                ]
            },
            'ND': {
                'landmarks': ['Theodore Roosevelt National Park', 'Fargo', 'Missouri River', 'International Peace Garden'],
                'backgrounds': [
                    'Theodore Roosevelt National Park',
                    'Fargo downtown',
                    'Missouri River with plains',
                    'International Peace Garden'
                ]
            },
            'MN': {
                'landmarks': ['Boundary Waters', 'Mall of America', 'Lake Superior', 'Minneapolis Skyway'],
                'backgrounds': [
                    'Boundary Waters Canoe Area',
                    'Mall of America',
                    'Lake Superior with cliffs',
                    'Minneapolis skyline with skyways'
                ]
            },
            'IA': {
                'landmarks': ['Field of Dreams', 'Iowa State Fair', 'Mississippi River', 'Loess Hills'],
                'backgrounds': [
                    'Field of Dreams baseball field',
                    'Iowa State Fairgrounds',
                    'Mississippi River bluffs',
                    'Loess Hills with prairie'
                ]
            },
            'MO': {
                'landmarks': ['Gateway Arch', 'Branson', 'Lake of the Ozarks', 'Kansas City Jazz'],
                'backgrounds': [
                    'Gateway Arch in St. Louis',
                    'Branson entertainment district',
                    'Lake of the Ozarks',
                    'Kansas City jazz district'
                ]
            },
            'IL': {
                'landmarks': ['Chicago Skyline', 'Shawnee National Forest', 'Mississippi River', 'Starved Rock'],
                'backgrounds': [
                    'Chicago skyline with Willis Tower',
                    'Shawnee National Forest',
                    'Mississippi River with bluffs',
                    'Starved Rock State Park'
                ]
            },
            'IN': {
                'landmarks': ['Indiana Dunes', 'Indianapolis Motor Speedway', 'Brown County', 'Ohio River'],
                'backgrounds': [
                    'Indiana Dunes on Lake Michigan',
                    'Indianapolis Motor Speedway',
                    'Brown County State Park',
                    'Ohio River with hills'
                ]
            },
            'OH': {
                'landmarks': ['Rock and Roll Hall of Fame', 'Cedar Point', 'Hocking Hills', 'Lake Erie'],
                'backgrounds': [
                    'Rock and Roll Hall of Fame',
                    'Cedar Point amusement park',
                    'Hocking Hills with waterfalls',
                    'Lake Erie with islands'
                ]
            },
            'MI': {
                'landmarks': ['Mackinac Island', 'Sleeping Bear Dunes', 'Detroit Renaissance Center', 'Lake Michigan'],
                'backgrounds': [
                    'Mackinac Island with Grand Hotel',
                    'Sleeping Bear Dunes',
                    'Detroit skyline with Renaissance Center',
                    'Lake Michigan with lighthouses'
                ]
            },
            'WI': {
                'landmarks': ['Door County', 'Wisconsin Dells', 'Milwaukee Art Museum', 'Lake Superior'],
                'backgrounds': [
                    'Door County with cherry orchards',
                    'Wisconsin Dells water parks',
                    'Milwaukee Art Museum wings',
                    'Lake Superior with Apostle Islands'
                ]
            },
            'PA': {
                'landmarks': ['Independence Hall', 'Gettysburg', 'Pocono Mountains', 'Philadelphia Museum'],
                'backgrounds': [
                    'Independence Hall with Liberty Bell',
                    'Gettysburg battlefield',
                    'Pocono Mountains with lakes',
                    'Philadelphia Museum of Art'
                ]
            },
            'NJ': {
                'landmarks': ['Atlantic City Boardwalk', 'Liberty State Park', 'Delaware Water Gap', 'Jersey Shore'],
                'backgrounds': [
                    'Atlantic City Boardwalk',
                    'Liberty State Park with Statue of Liberty',
                    'Delaware Water Gap',
                    'Jersey Shore beaches'
                ]
            },
            'DE': {
                'landmarks': ['Rehoboth Beach', 'Brandywine Valley', 'Delaware Bay', 'Dover Air Force Base'],
                'backgrounds': [
                    'Rehoboth Beach boardwalk',
                    'Brandywine Valley with mansions',
                    'Delaware Bay with marshes',
                    'Dover Air Force Base'
                ]
            },
            'MD': {
                'landmarks': ['Inner Harbor', 'Assateague Island', 'Antietam Battlefield', 'Chesapeake Bay'],
                'backgrounds': [
                    'Baltimore Inner Harbor',
                    'Assateague Island with wild horses',
                    'Antietam National Battlefield',
                    'Chesapeake Bay with sailboats'
                ]
            },
            'VA': {
                'landmarks': ['Colonial Williamsburg', 'Shenandoah National Park', 'Virginia Beach', 'Blue Ridge Mountains'],
                'backgrounds': [
                    'Colonial Williamsburg',
                    'Shenandoah National Park',
                    'Virginia Beach boardwalk',
                    'Blue Ridge Parkway'
                ]
            },
            'WV': {
                'landmarks': ['New River Gorge', 'Blackwater Falls', 'Harpers Ferry', 'Monongahela National Forest'],
                'backgrounds': [
                    'New River Gorge Bridge',
                    'Blackwater Falls State Park',
                    'Harpers Ferry historic town',
                    'Monongahela National Forest'
                ]
            },
            'KY': {
                'landmarks': ['Mammoth Cave', 'Bourbon Trail', 'Red River Gorge', 'Churchill Downs'],
                'backgrounds': [
                    'Mammoth Cave National Park',
                    'Kentucky Bourbon Trail',
                    'Red River Gorge with arches',
                    'Churchill Downs with Twin Spires'
                ]
            }
        }
    
    def get_location_from_zip(self, zip_code: str) -> Tuple[str, str]:
        """
        Get city and state from zip code using a free API.
        Returns (city, state) tuple.
        """
        try:
            url = f"https://api.zippopotam.us/us/{zip_code}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                city = data['places'][0]['place name']
                state = data['places'][0]['state abbreviation']
                return city, state
            else:
                return "Unknown", "Unknown"
        except Exception:
            return "Unknown", "Unknown"
    
    def generate_location_background(self, zip_code: str) -> Dict[str, str]:
        """
        Generate location-specific background description for personalized images.
        
        Args:
            zip_code: 5-digit zip code string
            
        Returns:
            Dictionary with background description and location info
        """
        city, state = self.get_location_from_zip(zip_code)
        
        # Check if it's a major city first
        if city in self.major_cities:
            city_data = self.major_cities[city]
            import random
            background = random.choice(city_data['backgrounds'])
            return {
                'background_description': background,
                'city': city,
                'state': state,
                'location_type': 'major_city',
                'landmarks': city_data['landmarks']
            }
        
        # If not a major city, use state landmarks
        elif state in self.state_landmarks:
            state_data = self.state_landmarks[state]
            import random
            background = random.choice(state_data['backgrounds'])
            return {
                'background_description': background,
                'city': city,
                'state': state,
                'location_type': 'state',
                'landmarks': state_data['landmarks']
            }
        
        # Fallback for unknown locations
        else:
            return {
                'background_description': 'a beautiful outdoor setting with natural scenery',
                'city': city,
                'state': state,
                'location_type': 'unknown',
                'landmarks': []
            }
    
    def get_location_context(self, zip_code: str) -> str:
        """
        Get location context for narrative generation.
        
        Args:
            zip_code: 5-digit zip code string
            
        Returns:
            Location context string for narrative generation
        """
        location_data = self.generate_location_background(zip_code)
        
        if location_data['location_type'] == 'major_city':
            return f"Customer is from {location_data['city']}, {location_data['state']}. Consider incorporating {location_data['city']} landmarks and culture subtly in the background."
        elif location_data['location_type'] == 'state':
            return f"Customer is from {location_data['city']}, {location_data['state']}. Consider incorporating {location_data['state']} state landmarks and natural features subtly in the background."
        else:
            return f"Customer is from {location_data['city']}, {location_data['state']}. Use general regional aesthetics."
    
    def get_background_prompt(self, zip_code: str) -> str:
        """
        Get background prompt for image generation.
        
        Args:
            zip_code: 5-digit zip code string
            
        Returns:
            Background prompt string for image generation
        """
        location_data = self.generate_location_background(zip_code)
        return location_data['background_description'] 