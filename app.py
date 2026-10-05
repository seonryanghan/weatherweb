from flask import Flask, render_template, request, jsonify

from weather_api import get_weather

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/weather", methods=["POST"])
def weather():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "요청 데이터가 없습니다."
        }), 400

    lat = data.get("lat")
    lon = data.get("lon")

    if lat is None or lon is None:

        return jsonify({
            "error": "위도 또는 경도 값이 없습니다."
        }), 400

    try:

        lat = float(lat)
        lon = float(lon)

    except ValueError:

        return jsonify({
            "error": "위도 또는 경도 값이 올바르지 않습니다."
        }), 400

    try:

        weather_data = get_weather(
            lat,
            lon
        )

        return jsonify(weather_data)

    except Exception as error:

        print(
            "날씨 API 오류:",
            error
        )

        return jsonify({
            "error":
                "기상청 날씨 정보를 가져오지 못했습니다."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
