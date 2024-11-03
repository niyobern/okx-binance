import json

# Read the JSON file
with open('fees_usdt.json', 'r') as file:
    data = json.load(file)

# Get the fees dictionary
fees = data['fees']

# Convert to list of tuples (coin, info) and sort by fee_usdt
sorted_fees = sorted(
    [(coin, info) for coin, info in fees.items()],
    key=lambda x: x[1]['withdrawal_fee_usdt']
)

sorted_fees = sorted_fees[:88]

# Create a new dictionary with sorted items
sorted_dict = {
    "timestamp": data['timestamp'],
    "fees": {coin: info for coin, info in sorted_fees}
}

with open('sorted_fees.json', 'w') as file:
    json.dump(sorted_dict, file, indent=4)
