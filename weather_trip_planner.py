import requests
from bs4 import BeautifulSoup
import datetime
import re
import sys
import json
import webbrowser
from urllib.parse import quote, quote_plus

def search_location(city_name):
    """Search for a location on timeanddate.com and return its ID."""
    # Parse city and state from input
    city_state_pattern = r'([\w\s\-]+),\s*(\w+)'
    match = re.search(city_state_pattern, city_name)
    
    if match:
        city = match.group(1).strip()
        state = match.group(2).strip()
        print(f"Searching for city: {city}, state: {state}")
    else:
        city = city_name
        state = None
        print(f"Searching for: {city}")
    
    search_url = f"https://www.timeanddate.com/weather/?query={quote(city_name)}+usa"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all search result rows
        location_rows = soup.select('table tr')
        
        if not location_rows or len(location_rows) <= 1:  # Account for header row
            print(f"No matching locations found for '{city_name}'")
            return None
        
        usa_locations = []
        
        # Define state abbreviations dictionary
        state_abbr_to_name = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
            'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
            'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
            'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
            'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
            'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
            'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
            'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
            'DC': 'District of Columbia'
        }
        
        # Get state full name if abbreviation was provided
        state_full = state_abbr_to_name.get(state.upper(), state) if state else None
        
        # Skip the header row
        for row in location_rows[1:]:
            location_link = row.select_one('a')
            if not location_link:
                continue
                
            href = location_link.get('href', '')
            location_id_match = re.search(r'@(\d+)', href)
            
            if location_id_match:
                location_id = location_id_match.group(1)
                location_name = location_link.text.strip()
                location_text = row.text.strip()
                
                # Only consider USA locations
                if 'USA' not in location_text:
                    continue
                
                # Calculate a match score
                score = 0
                
                # Check for exact city name match
                if city.lower() == location_name.lower():
                    score += 100
                # Check for city name contained in location name
                elif city.lower() in location_name.lower():
                    score += 50
                else:
                    continue  # Skip if city name not found at all
                
                # If state is provided, check for state match
                if state:
                    # Try to match state abbreviation or full name
                    if state.upper() in location_text or (state_full and state_full in location_text):
                        score += 50
                    else:
                        score -= 20  # Penalize if state doesn't match
                
                # Additional bonus for location that is exactly the city (not a district/area)
                if location_name.lower() == city.lower():
                    score += 30
                
                # Penalty for locations with "historical", "district", etc.
                lower_text = location_text.lower()
                if any(term in lower_text for term in ['historical', 'district', 'north', 'south', 'east', 'west']):
                    score -= 10
                
                usa_locations.append({
                    'id': location_id,
                    'name': location_name,
                    'full_text': location_text,
                    'score': score
                })
        
        if not usa_locations:
            print(f"No matching locations found in USA for '{city_name}'")
            return None
        
        # Sort locations by score and get the highest
        usa_locations.sort(key=lambda x: x['score'], reverse=True)
        
        # Print top matches for debugging
        print("\nTop location matches:")
        for i, loc in enumerate(usa_locations[:3]):
            print(f"{i+1}. {loc['full_text']} (Score: {loc['score']})")
        
        # Return the highest scored result's ID
        location_id = usa_locations[0]['id']
        location_name = usa_locations[0]['name']
        print(f"\nSelected location: {location_name} (ID: {location_id})")
        return location_id, location_name, location_text
        
    except Exception as e:
        print(f"Error searching for location: {e}")
        return None

def process_city(city_name, trip_length, max_price):
    """Process a single city to find suitable travel periods."""
    print(f"\n{'='*50}")
    print(f"ANALYZING: {city_name}")
    print(f"{'='*50}")
    
    location_result = search_location(city_name)
    
    if not location_result:
        print(f"Could not find location for {city_name}")
        return []
        
    location_id, city, full_location = location_result
    
    # Extract state from full location text (format is typically "USA, State, City")
    state_match = re.search(r'USA,\s*([\w\s\-]+),', full_location)
    state = state_match.group(1).strip() if state_match else None
    
    # Get state abbreviation if we have a state
    state_abbr = None
    if state:
        state_name_to_abbr = {v: k for k, v in {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
            'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
            'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
            'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
            'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
            'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
            'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
            'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
            'DC': 'District of Columbia'
        }.items()}
        
        # Find closest matching state
        for state_name in state_name_to_abbr:
            if state_name.lower() in state.lower() or state.lower() in state_name.lower():
                state_abbr = state_name_to_abbr[state_name]
                break
    
    print(f"Fetching 14-day forecast for location ID {location_id}...")
    html_content = get_weather_forecast(location_id)
    
    if not html_content:
        print(f"Could not fetch forecast for {city_name}")
        return []
    
    print("Parsing forecast data...")
    forecast_data = parse_forecast(html_content)
    
    if not forecast_data:
        print(f"No forecast data found for {city_name}")
        return []
    
    print(f"Found forecast data for {len(forecast_data)} days")
    
    print(f"Finding {trip_length}-night periods without rain that are weekend-adjacent...")
    rain_free_periods = find_rain_free_periods(forecast_data, trip_length)
    
    if not rain_free_periods:
        print(f"No suitable periods found in the 14-day forecast for {city_name}")
        return []
    
    # Prepare results for this city
    city_results = []
    
    print(f"\nSuitable periods for {city_name}:")
    for i, period in enumerate(rain_free_periods, 1):
        start_date = period['start_date']
        end_date = period['end_date']
        
        start_date_str = start_date.strftime("%a, %b %d")
        end_date_str = end_date.strftime("%a, %b %d")
        
        # Calculate the number of days in the range
        days_in_range = (end_date - start_date).days + 1
        
        # Calculate nights from days
        nights = days_in_range - 1
        
        print(f"{i}. {start_date_str} to {end_date_str} ({nights} nights / {days_in_range} days)")
        
        # Collect forecast details
        forecast_details = []
        for day in period['days']:
            date_str = day['date'].strftime("%a, %b %d")
            temp_str = ""
            if day['temp_high'] and day['temp_low']:
                temp_str = f" [{day['temp_high']}°F / {day['temp_low']}°F]"
            forecast_details.append(f"   - {date_str}{temp_str}: {day['description']}")
            print(forecast_details[-1])
        
        # Generate Expedia URL for this period
        expedia_url = generate_expedia_url(city, state_abbr, start_date, end_date, max_price)
        print(f"   Hotel search: {expedia_url}")
        
        # Add this period to the city's results
        city_results.append({
            'city': city_name,
            'period_num': i,
            'start_date': start_date,
            'end_date': end_date,
            'start_date_str': start_date_str,
            'end_date_str': end_date_str,
            'nights': nights,
            'days': days_in_range,
            'forecast': forecast_details,
            'expedia_url': expedia_url
        })
        
    return city_results

def get_weather_forecast(location_id):
    """Get the 14-day weather forecast for a given location ID."""
    forecast_url = f"https://www.timeanddate.com/weather/@{location_id}/ext"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(forecast_url, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching weather forecast: {e}")
        return None

def parse_forecast(html_content):
    """Parse the HTML content to extract weather forecast data."""
    soup = BeautifulSoup(html_content, 'html.parser')
    forecast_data = []
    
    # Find the forecast table - using the id from the sample file
    forecast_table = soup.find('table', id='wt-ext')
    
    if not forecast_table:
        print("Could not find forecast table with id 'wt-ext'")
        # Try alternative selectors
        forecast_table = soup.select_one('table.zebra, table.fw, table.tb-wt')
        if not forecast_table:
            print("Could not find any forecast tables")
            return []
    
    # Find all rows in the tbody section of the table
    tbody = forecast_table.find('tbody')
    if not tbody:
        print("No tbody found in forecast table")
        rows = forecast_table.find_all('tr')
    else:
        rows = tbody.find_all('tr')
    
    if not rows:
        print("No rows found in forecast table")
        return []
    
    print(f"Found {len(rows)} rows in forecast table")
    
    for row in rows:
        try:
            # Skip rows that don't have a th element (header cells with dates)
            th = row.find('th')
            if not th:
                continue
            
            # Extract the day of week and date from the th
            day_span = th.find('span', class_='smaller')
            if not day_span:
                continue
                
            day_of_week = day_span.text.strip()
            
            # The month and day are in the text after the span
            # This captures text like "May 10" that follows the span and br tag
            date_text = th.decode_contents()
            month_day_match = re.search(r'<br/?>([\w]+)\s+(\d{1,2})', date_text)
            
            if not month_day_match:
                print(f"Could not extract month/day from: {date_text}")
                continue
                
            month_abbr = month_day_match.group(1)
            day = int(month_day_match.group(2))
            
            # Find the weather description from img title attribute
            weather_img = row.find('img', class_='mtt')
            weather_desc = ""
            if weather_img and weather_img.has_attr('title'):
                weather_desc = weather_img['title']
            
            # Extract temperature
            temp_cell = None
            for cell in row.find_all('td'):
                if '°F' in cell.text or '°C' in cell.text:
                    temp_cell = cell
                    break
            
            temp_high = None
            temp_low = None
            if temp_cell:
                temp_text = temp_cell.text.strip()
                temp_match = re.search(r'(\d+)\s*/\s*(\d+)', temp_text)
                if temp_match:
                    temp_high = int(temp_match.group(1))
                    temp_low = int(temp_match.group(2))
            
            # Check for precipitation in the row
            precip_cells = row.find_all('td')
            has_rain = False
            
            if weather_desc:
                # Check weather description for rain-related terms
                has_rain = any(term in weather_desc.lower() for term in 
                              ['rain', 'shower', 'drizzle', 'thunderstorm', 
                               'precipitation', 'sprinkle', 'tstorm'])
            
            # If no weather description found, check for precipitation chance
            if not has_rain and len(precip_cells) >= 8:  # The chance column is usually 8th td
                chance_cell = precip_cells[7]  # 0-indexed, so 8th cell is index 7
                chance_text = chance_cell.text.strip()
                if chance_text and chance_text != '0%':
                    try:
                        chance = int(chance_text.replace('%', ''))
                        if chance > 20:  # If more than 20% chance, consider it might rain
                            has_rain = True
                    except ValueError:
                        pass
            
            # Create date object
            year = datetime.datetime.now().year
            # Handle December to January transition
            if month_abbr == 'Jan' and datetime.datetime.now().month == 12:
                year += 1
            
            # Convert month abbreviation to number
            month_mapping = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            month_num = month_mapping.get(month_abbr, None)
            
            if not month_num:
                print(f"Invalid month abbreviation: {month_abbr}")
                continue
            
            date = datetime.date(year, month_num, day)
            
            forecast_data.append({
                'date': date,
                'day_of_week': day_of_week,
                'description': weather_desc,
                'has_rain': has_rain,
                'temp_high': temp_high,
                'temp_low': temp_low
            })
            
        except Exception as e:
            print(f"Error processing row: {e}")
            continue
    
    print(f"Successfully extracted {len(forecast_data)} days of forecast data")
    return forecast_data

def is_weekend_day(date):
    """Check if a date is a weekend day (Saturday or Sunday)."""
    return date.weekday() >= 5  # 5 = Saturday, 6 = Sunday

def is_weekend_adjacent(start_date, end_date):
    """Check if a date range is adjacent to a weekend."""
    # Check if the range includes a weekend
    current_date = start_date
    while current_date <= end_date:
        if is_weekend_day(current_date):
            return True
        current_date += datetime.timedelta(days=1)
    
    # Check if the range is adjacent to a weekend
    before_start = start_date - datetime.timedelta(days=1)
    after_end = end_date + datetime.timedelta(days=1)
    
    return is_weekend_day(before_start) or is_weekend_day(after_end)

def find_rain_free_periods(forecast_data, trip_length):
    """Find date ranges of specified length that have no rain and are weekend-adjacent.
    
    Args:
        forecast_data: List of daily forecast dictionaries
        trip_length: Number of NIGHTS to stay (n nights = n+1 days)
    
    Returns:
        List of rain-free periods that are weekend-adjacent
    """
    rain_free_periods = []
    
    # Convert trip_length to integer
    trip_length = int(trip_length)
    
    # For n nights, we need n+1 days
    days_needed = trip_length + 1
    
    # Check each possible start date
    for i in range(len(forecast_data) - days_needed + 1):
        start_date = forecast_data[i]['date']
        end_date = forecast_data[i + days_needed - 1]['date']
        
        # Check if all days in this period are rain-free
        is_rain_free = True
        for j in range(days_needed):
            if forecast_data[i + j]['has_rain']:
                is_rain_free = False
                break
        
        # If rain-free and weekend-adjacent, add to results
        if is_rain_free and is_weekend_adjacent(start_date, end_date):
            rain_free_periods.append({
                'start_date': start_date,
                'end_date': end_date,
                'days': [forecast_data[i + j] for j in range(days_needed)]
            })
    
    return rain_free_periods

def generate_expedia_url(city_name, state_abbr, start_date, end_date, max_price):
    """Generate an Expedia hotel search URL for the given parameters."""
    # Format dates as YYYY-MM-DD
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    # Create the destination string
    if state_abbr:
        destination = f"{city_name}, {state_abbr}, United States of America"
    else:
        destination = f"{city_name}, United States of America"
    
    # Build the base URL with parameters
    base_url = "https://www.expedia.com/Hotel-Search"
    
    # Format the URL with explicit price range (min=0, max=specified)
    query_parts = [
        f"MDPCID=US.META.HPA.HOTEL-CORESEARCH-desktop.HOTEL",
        f"adults=2",
        f"children=",
        f"destination={quote_plus(destination)}",
        f"endDate={end_date_str}",
        f"startDate={start_date_str}",
        f"sort=REVIEW_RELEVANT",
        f"paymentType=FREE_CANCELLATION",
        f"price=0",  # Min price
        f"price={max_price}",  # Max price
        f"stay_options_group=hotels_option"  # Ensure only hotels (not vacation homes) are shown
    ]
    
    # Join all parts with &
    query_string = "&".join(query_parts)
    
    return f"{base_url}?{query_string}"

def main():
    if len(sys.argv) < 4:
        print("Usage: python weather_trip_planner.py <trip_length_in_nights> <max_price> <city_name1> [& <city_name2> ...]")
        print("Example: python weather_trip_planner.py 2 400 'Ocean City, MD & Virginia Beach, VA'")
        return
    
    try:
        trip_length = int(sys.argv[1])
        if trip_length < 1:
            print("Trip length must be a positive integer")
            return
    except ValueError:
        print("Trip length must be a number")
        return
    
    try:
        max_price = int(sys.argv[2])
        if max_price < 1:
            print("Max price must be a positive integer")
            return
    except ValueError:
        print("Max price must be a number")
        return
    
    # Get the city list - the rest of the arguments may form a single string with '&' separators
    city_input = ' '.join(sys.argv[3:])
    city_names = [city.strip() for city in city_input.split('&')]
    
    if not city_names:
        print("No cities specified")
        return
    
    # Process each city
    all_results = []
    for city_name in city_names:
        if not city_name.strip():
            continue
            
        city_results = process_city(city_name.strip(), trip_length, max_price)
        all_results.extend(city_results)
    
    # Final summary of all results
    if not all_results:
        print("\nNo suitable periods found for any cities.")
        return
    
    print("\n" + "="*50)
    print("SUMMARY OF ALL RESULTS")
    print("="*50)
    
    all_results.sort(key=lambda x: x['start_date'])  # Sort by start date
    
    for i, result in enumerate(all_results, 1):
        # Extract temperature information from forecast days
        temp_info = []
        for day_forecast in result['forecast']:
            # Extract temperature from the forecast string
            temp_match = re.search(r'\[(\d+)°F / (\d+)°F\]', day_forecast)
            if temp_match:
                high, low = temp_match.group(1), temp_match.group(2)
                temp_info.append(f"{high}°F/{low}°F")
        
        temp_summary = ", ".join(temp_info)
        print(f"{i}. {result['city']}: {result['start_date_str']} to {result['end_date_str']} ({result['nights']} nights)")
        print(f"   Temperatures: {temp_summary}")
    
    print("\nDo you want to open any of the hotel search URLs? (Enter numbers separated by comma, or 'all')")
    selection = input("Selection: ")
    
    if selection.lower() == 'all':
        indices = range(1, len(all_results) + 1)
    else:
        try:
            indices = [int(idx.strip()) for idx in selection.split(',') if idx.strip()]
        except ValueError:
            print("Invalid selection. No URLs opened.")
            return
    
    for idx in indices:
        if 1 <= idx <= len(all_results):
            result = all_results[idx - 1]
            print(f"Opening URL for {result['city']}: {result['start_date_str']} to {result['end_date_str']}")
            webbrowser.open(result['expedia_url'])
        else:
            print(f"Invalid index: {idx}")

if __name__ == "__main__":
    main() 