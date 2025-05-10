# Weekend Beach Trip Searcher

## Purpose
Plan your next beach trip with confidence! This tool analyzes weather forecasts for multiple beach destinations over the next 2 weeks, finding periods with optimal weather that are weekend-adjacent. 

It automatically generates hotel search links within your all-in budget, saving you hours of manual searching and helping you avoid weather disappointments.

## How It Works

The tool scrapes 14-day weather forecasts from timeanddate.com, analyzes each location for rain-free periods near weekends, and generates Expedia hotel search URLs within your specified price range.

## Installation & Usage

```bash
# Clone the repository
git clone https://github.com/yourusername/weekend-beach-trip-searcher.git
cd weekend-beach-trip-searcher

# Note: If you're viewing this on GitHub, you can also download the code directly 
# using the green "Code" button above

# Install dependencies
pip install -r requirements.txt

# Basic usage
python weather_trip_planner.py <trip_length_in_nights> <max_price_in_usd> "<city1>, <state1> & <city2>, <state2> & ..."

# Example: 2-night trip for max $300/night at multiple beach destinations
python weather_trip_planner.py 2 300 "Ocean City, MD & Virginia Beach, VA & Dewey Beach, DE & Rehoboth Beach, DE"
```

### Parameters:
- `trip_length_in_nights`: Duration of your stay in nights
- `max_price`: Maximum nightly rate for hotels
- `cities`: One or more destinations separated by `&`

## Example Results

```
==================================================
SUMMARY OF ALL RESULTS
==================================================
1. Ocean City, MD: Sat, May 10 to Mon, May 12 (2 nights)
   Temperatures: 70°F/52°F, 73°F/57°F, 68°F/57°F
2. Dewey Beach, DE: Sat, May 10 to Mon, May 12 (2 nights)
   Temperatures: 70°F/52°F, 73°F/57°F, 68°F/57°F
3. Rehoboth Beach, DE: Sat, May 10 to Mon, May 12 (2 nights)
   Temperatures: 70°F/52°F, 73°F/57°F, 68°F/57°F
Do you want to open any of the hotel search URLs? (Enter numbers separated by comma, or 'all')
Selection: 
```

After selecting options (e.g. type in `1,2,3` and hit Enter), the script opens Expedia hotel search pages directly in your browser, with your dates, location and price filters already applied.

## Notes

As someone who works with a weather data company I have to give the standard disclaimer that 14 day forecasts are not the most accurate and are very prone to changing. This tool searches Expedia for only **fully refundable** hotels for that reason.

## Future Enhancements

- [ ] Support for international destinations - Hardcoded to USA right now due to issues in timeanddate search ordering
- [ ] Explore integration with flight bookings
- [ ] Mobile app version with notifications for ideal weather windows
- [ ] More config options for searches
- [ ] Automated pulling of search results and ranking based on your criteria (e.g. average rating, sentiment, etc.)

## Contributing

Contributions are welcome! Feel free to submit a pull request or open an issue to discuss new features or improvements.

## License

MIT 