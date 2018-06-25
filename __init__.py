from flask import Flask, jsonify, request
import building_automation

app = Flask(__name__)

test_building = [
	{'address': '207 Park Avenue, Raleigh', 'sqFootage': 2500 }
]

@app.route("/test_building")
def get_test():
	return jsonify(test_building)

@app.route("/buildings/<string:addr>")
def get_square_footage(addr):
	squareFootage = building_automation.squareFootage(addr)
	return jsonify({'address': addr, 'sqFootage': squareFootage})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)