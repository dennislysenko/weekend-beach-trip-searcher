#!/bin/bash

echo "Enter destination city and state (e.g., Ocean City, Maryland):"
read city

echo "Enter start date (YYYY-MM-DD):"
read start_date

echo "Enter end date (YYYY-MM-DD):"
read end_date

echo "Enter maximum total price (e.g., 400):"
read max_price

# URL encode city
city_encoded=$(echo "$city" | sed 's/ /%20/g' | sed 's/,/%2C/g')

# Construct URL
base_url="https://www.expedia.com/Hotel-Search?"
params="adults=2&children=&destination=$city_encoded&startDate=$start_date&endDate=$end_date&price=0&price=$max_price&sort=RECOMMENDED"

final_url="${base_url}${params}"

echo -e "\nOpening in browser..."
open "$final_url"
