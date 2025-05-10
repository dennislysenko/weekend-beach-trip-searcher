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
        return location_id, location_name, usa_locations[0]['full_text']
        
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
    
    print(f"Finding {trip_length}-night periods with good weather that are weekend-adjacent...")
    suitable_periods = find_suitable_periods(forecast_data, trip_length)
    
    if not suitable_periods:
        print(f"No suitable periods found in the 14-day forecast for {city_name}")
        return []
    
    # Prepare results for this city
    city_results = []
    
    print(f"\nSuitable periods for {city_name}:")
    for i, period in enumerate(suitable_periods, 1):
        start_date = period['start_date']
        end_date = period['end_date']
        
        start_date_str = start_date.strftime("%a, %b %d")
        end_date_str = end_date.strftime("%a, %b %d")
        
        # Calculate the number of days in the range
        days_in_range = (end_date - start_date).days + 1
        
        # Calculate nights from days
        nights = days_in_range - 1
        
        # Count rainy days
        rainy_days = sum(1 for day in period['days'] if day['has_rain'])
        total_days = len(period['days'])
        rain_percentage = (rainy_days / total_days) * 100
        
        print(f"{i}. {start_date_str} to {end_date_str} ({nights} nights / {days_in_range} days)")
        print(f"   Rain: {rainy_days}/{total_days} days ({rain_percentage:.1f}%)")
        
        # Collect forecast details
        forecast_details = []
        for day in period['days']:
            date_str = day['date'].strftime("%a, %b %d")
            temp_str = ""
            if day['temp_high'] and day['temp_low']:
                temp_str = f" [{day['temp_high']}°F / {day['temp_low']}°F]"
            
            # Add rain probability if available
            rain_prob_str = ""
            if day['rain_probability'] is not None:
                rain_prob_str = f" (Rain: {day['rain_probability']}%)"
                
            forecast_details.append(f"   - {date_str}{temp_str}: {day['description']}{rain_prob_str}")
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
            'expedia_url': expedia_url,
            'rain_percentage': rain_percentage,
            'days_data': period['days']  # Include full days data for summary
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
            rain_probability = None
            
            if weather_desc:
                # Check weather description for rain-related terms
                has_rain = any(term in weather_desc.lower() for term in 
                              ['rain', 'shower', 'drizzle', 'thunderstorm', 
                               'precipitation', 'sprinkle', 'tstorm'])
            
            # If no weather description found, check for precipitation chance
            if len(precip_cells) >= 8:  # The chance column is usually 8th td
                chance_cell = precip_cells[7]  # 0-indexed, so 8th cell is index 7
                chance_text = chance_cell.text.strip()
                if chance_text and chance_text != '0%':
                    try:
                        chance = int(chance_text.replace('%', ''))
                        rain_probability = chance
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
                'rain_probability': rain_probability,
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

def find_suitable_periods(forecast_data, trip_length):
    """Find date ranges of specified length that meet weather criteria and are weekend-adjacent.
    
    Args:
        forecast_data: List of daily forecast dictionaries
        trip_length: Number of NIGHTS to stay (n nights = n+1 days)
    
    Returns:
        List of suitable periods that are weekend-adjacent
    """
    suitable_periods = []
    
    # Convert trip_length to integer
    trip_length = int(trip_length)
    
    # For n nights, we need n+1 days
    days_needed = trip_length + 1
    
    # Check each possible start date
    for i in range(len(forecast_data) - days_needed + 1):
        start_date = forecast_data[i]['date']
        end_date = forecast_data[i + days_needed - 1]['date']
        days_range = [forecast_data[i + j] for j in range(days_needed)]
        
        # Count rainy days in this period
        rainy_days = sum(1 for day in days_range if day['has_rain'])
        
        # Check if rain on first or last day is ≤ 30%
        start_day_rain_prob = days_range[0]['rain_probability'] or 0
        end_day_rain_prob = days_range[-1]['rain_probability'] or 0
        
        # Debug output for each potential period
        # print(f"\nEvaluating period: {start_date.strftime('%a, %b %d')} to {end_date.strftime('%a, %b %d')}")
        # print(f"Rainy days: {rainy_days}/{days_needed} (needs < {days_needed / 2})")
        # print(f"Start day rain: {start_day_rain_prob}% (needs ≤ 30%)")
        # print(f"End day rain: {end_day_rain_prob}% (needs ≤ 30%)")
        # print(f"Weekend adjacent: {is_weekend_adjacent(start_date, end_date)}")
        
        # # Print details for each day
        # for j, day in enumerate(days_range):
        #     print(f"  Day {j+1} ({day['date'].strftime('%a, %b %d')}): " +
        #           f"Rain prob: {day['rain_probability'] or 0}%, " +
        #           f"has_rain: {day['has_rain']}")
        
        # Check criteria:
        # 1. Less than half the days have rain
        # 2. Both departure and arrival have ≤ 30% rain probability
        # 3. Is weekend-adjacent
        if (rainy_days < days_needed / 2 and  # Less than half the days have rain
            start_day_rain_prob <= 30 and     # ≤ 30% chance on departure
            end_day_rain_prob <= 30 and       # ≤ 30% chance on arrival
            is_weekend_adjacent(start_date, end_date)):  # Weekend-adjacent
            
            # print(f"✓ Period PASSES all criteria")
            suitable_periods.append({
                'start_date': start_date,
                'end_date': end_date,
                'days': days_range
            })
        # else:
            # print(f"✗ Period FAILS criteria")
    
    return suitable_periods

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
        # Extract temperature and rain probability information
        temp_rain_info = []
        for day in result['days_data']:
            high = day['temp_high'] or "N/A"
            low = day['temp_low'] or "N/A"
            rain_prob = day['rain_probability'] or 0
            temp_rain_info.append(f"{high}°F/{low}°F (Rain: {rain_prob}%)")
        
        temp_rain_summary = ", ".join(temp_rain_info)
        print(f"{i}. {result['city']}: {result['start_date_str']} to {result['end_date_str']} ({result['nights']} nights)")
        print(f"   Weather: {temp_rain_summary}")
        print(f"   Rain percentage: {result['rain_percentage']:.1f}%")
    
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