from pydantic import BaseModel
from typing import Optional

class Location(BaseModel): 
    lat: float 
    lon: float 

class Place(BaseModel): 
    name: str 
    address: str 
    location: Location 
    distance: Optional[float] = None 
    place_id: str 

class NearbyPlacesResponse(BaseModel): 
    places: list[Place]

class GeocodeResult(BaseModel):
    lat: float
    lon: float
    formatted_address: str
    
class GeocodeResponse(BaseModel):
    results: list[GeocodeResult]