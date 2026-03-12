import os
import requests
import re
from typing import List, Dict
from langchain_core.tools import tool

from dotenv import load_dotenv
from utils.place_info_search import GeoapifyPlaceSearchTool

class PlaceSearchWithImagesTool:
    """Combine Geoapify Place search + Unsplash images"""
    def __init__(self):
        load_dotenv()
        self.geoapify_key = os.environ.get("GPLACES_API_KEY")
        self.unsplash_key = os.environ.get("UNSPLASH_API_KEY")
        self.geoapify_tool = GeoapifyPlaceSearchTool(self.geoapify_key)
        self.tools_list = self._setup_tools()

    def _setup_tools(self) -> List:
        @tool
        def search_top_places_with_images(place: str) -> List[Dict]:
            """Return top attractions with actual image URLs"""
            results = []
            
            # Get places from Geoapify
            top_places = self.geoapify_tool.search_attractions(place)[:5]
            
            for item in top_places:
                # Extract clean place name
                if " - " in item:
                    place_name = item.split(" - ")[0].strip()
                    full_description = item
                else:
                    place_name = item
                    full_description = item
                
                # Clean the place name for image search
                clean_name = re.sub(r'[,-].*$', '', place_name).strip()
                
                # Get images from Unsplash
                image_urls = []
                
                # Try different search queries for better results
                search_queries = [
                    clean_name,
                    f"{clean_name} landmark",
                    f"{clean_name} tourist attraction",
                    clean_name.split()[0] if len(clean_name.split()) > 1 else clean_name
                ]
                
                # Remove duplicates
                seen = set()
                unique_queries = []
                for q in search_queries:
                    if q not in seen and q:
                        seen.add(q)
                        unique_queries.append(q)
                
                # Search Unsplash with different queries
                for query in unique_queries[:2]:  # Try first 2 unique queries
                    if len(image_urls) >= 3:
                        break
                        
                    unsplash_url = "https://api.unsplash.com/search/photos"
                    params = {
                        "query": query,
                        "per_page": 5,
                        "client_id": self.unsplash_key
                    }
                    
                    try:
                        response = requests.get(unsplash_url, params=params)
                        if response.status_code == 200:
                            data = response.json()
                            for photo in data.get("results", []):
                                if len(image_urls) >= 3:
                                    break
                                # Get regular sized image
                                if "urls" in photo and "regular" in photo["urls"]:
                                    img_url = photo["urls"]["regular"]
                                    if img_url not in image_urls:
                                        image_urls.append(img_url)
                    except:
                        continue
                
                # If no images found, try a more generic search with just the first word
                if not image_urls and len(clean_name.split()) > 1:
                    simple_query = clean_name.split()[0]
                    try:
                        params = {
                            "query": simple_query,
                            "per_page": 3,
                            "client_id": self.unsplash_key
                        }
                        response = requests.get(unsplash_url, params=params)
                        if response.status_code == 200:
                            data = response.json()
                            for photo in data.get("results", []):
                                if len(image_urls) >= 3:
                                    break
                                if "urls" in photo and "regular" in photo["urls"]:
                                    img_url = photo["urls"]["regular"]
                                    if img_url not in image_urls:
                                        image_urls.append(img_url)
                    except:
                        pass
                
                # Add to results
                results.append({
                    "title": place_name,
                    "description": full_description,
                    "images": image_urls  # This will be a list of actual image URLs
                })
            
            return results
        
        return [search_top_places_with_images]
