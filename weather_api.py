import os
import math
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv


# .env 파일 불러오기
load_dotenv()


# 기상청 API 인증키
SERVICE_KEY = os.getenv("KMA_SERVICE_KEY")


# 기상청 초단기실황 API 주소
URL = (
    "https://apis.data.go.kr/1360000/"
    "VilageFcstInfoService_2.0/"
    "getUltraSrtNcst"
)


def convert_to_grid(lat, lon):
    """
    위도(latitude), 경도(longitude)를
    기상청 격자 좌표 nx, ny로 변환합니다.
    """

    RE = 6371.00877
    GRID = 5.0

    SLAT1 = 30.0
    SLAT2 = 60.0

    OLON = 126.0
    OLAT = 38.0

    XO = 43
    YO = 136

    DEGRAD = math.pi / 180.0

    re = RE / GRID

    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD

    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD

    sn = (
        math.tan(
            math.pi * 0.25
            + slat2 * 0.5
        )
        /
        math.tan(
            math.pi * 0.25
            + slat1 * 0.5
        )
    )

    sn = (
        math.log(
            math.cos(slat1)
            / math.cos(slat2)
        )
        /
        math.log(sn)
    )

    sf = math.tan(
        math.pi * 0.25
        + slat1 * 0.5
    )

    sf = (
        math.pow(sf, sn)
        * math.cos(slat1)
        / sn
    )

    ro = math.tan(
        math.pi * 0.25
        + olat * 0.5
    )

    ro = (
        re
        * sf
        / math.pow(ro, sn)
    )

    ra = math.tan(
        math.pi * 0.25
        + lat * DEGRAD * 0.5
    )

    ra = (
        re
        * sf
        / math.pow(ra, sn)
    )

    theta = (
        lon * DEGRAD
        - olon
    )

    if theta > math.pi:
        theta -= 2.0 * math.pi

    if theta < -math.pi:
        theta += 2.0 * math.pi

    theta *= sn

    nx = int(
        math.floor(
            ra * math.sin(theta)
            + XO
            + 0.5
        )
    )

    ny = int(
        math.floor(
            ro
            - ra * math.cos(theta)
            + YO
            + 0.5
        )
    )

    return nx, ny


def get_weather(lat, lon):
    """
    위도와 경도를 받아
    해당 위치의 현재 날씨 정보를 반환합니다.
    """

    # API 키가 설정되어 있는지 확인
    if not SERVICE_KEY:
        raise RuntimeError(
            "KMA_SERVICE_KEY가 설정되어 있지 않습니다."
        )

    # 위도 / 경도 → 기상청 격자 좌표
    nx, ny = convert_to_grid(
        lat,
        lon
    )

    # 현재 한국 시간
    now = datetime.now(
        ZoneInfo("Asia/Seoul")
    )

    # 기상청 데이터 제공 지연을 고려하여
    # 1시간 전 자료 사용
    target_time = (
        now
        - timedelta(hours=1)
    )

    base_date = target_time.strftime(
        "%Y%m%d"
    )

    base_time = target_time.strftime(
        "%H00"
    )

    # API 요청 파라미터
    params = {

        "serviceKey": SERVICE_KEY,

        "pageNo": 1,

        "numOfRows": 100,

        "dataType": "JSON",

        "base_date": base_date,

        "base_time": base_time,

        "nx": nx,

        "ny": ny
    }

    try:

        response = requests.get(
            URL,
            params=params,
            timeout=10
        )

        # HTTP 오류 확인
        response.raise_for_status()

    except requests.exceptions.Timeout:

        raise RuntimeError(
            "기상청 API 요청 시간이 초과되었습니다."
        )

    except requests.exceptions.ConnectionError:

        raise RuntimeError(
            "기상청 API 서버에 연결할 수 없습니다."
        )

    except requests.exceptions.RequestException as error:

        raise RuntimeError(
            f"기상청 API 요청 오류: {error}"
        )

    try:

        data = response.json()

    except ValueError:

        raise RuntimeError(
            "기상청 API 응답을 JSON으로 변환하지 못했습니다."
        )

    # 기상청 API 내부 응답 확인
    try:

        header = (
            data["response"]
            ["header"]
        )

    except KeyError:

        raise RuntimeError(
            "기상청 API 응답 형식이 올바르지 않습니다."
        )

    result_code = header.get(
        "resultCode"
    )

    result_message = header.get(
        "resultMsg"
    )

    if result_code != "00":

        raise RuntimeError(
            f"기상청 API 오류: "
            f"{result_message}"
        )

    # 날씨 데이터 가져오기
    try:

        items = (
            data["response"]
            ["body"]
            ["items"]
            ["item"]
        )

    except (
        KeyError,
        TypeError
    ):

        raise RuntimeError(
            "기상청 날씨 데이터가 없습니다."
        )

    weather = {}

    # 필요한 데이터 추출
    for item in items:

        category = item.get(
            "category"
        )

        value = item.get(
            "obsrValue"
        )

        # 기온
        if category == "T1H":

            weather["temperature"] = value

        # 습도
        elif category == "REH":

            weather["humidity"] = value

        # 풍속
        elif category == "WSD":

            weather["windSpeed"] = value

        # 1시간 강수량
        elif category == "RN1":

            weather["rainfall"] = value

        # 강수 형태
        elif category == "PTY":

            weather[
                "precipitationType"
            ] = value

    # 반드시 필요한 값 확인
    if "temperature" not in weather:

        raise RuntimeError(
            "기온 데이터를 찾을 수 없습니다."
        )

    if "humidity" not in weather:

        raise RuntimeError(
            "습도 데이터를 찾을 수 없습니다."
        )

    if "windSpeed" not in weather:

        raise RuntimeError(
            "풍속 데이터를 찾을 수 없습니다."
        )

    # 요청에 사용한 정보도 함께 저장
    weather["nx"] = nx
    weather["ny"] = ny

    weather["baseDate"] = (
        base_date
    )

    weather["baseTime"] = (
        base_time
    )

    return weather
