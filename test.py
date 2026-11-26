import requests

# Set the endpoint URL and payload
url = "http://127.0.0.1:6277/recommend_food_place"
data = {
    "query": "Find pizza places in New York"
}

# Send a POST request
response = requests.post(url, json=data)

# Print the server response
print(response.text)
