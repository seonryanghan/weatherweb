let button;
let statusText;


document.addEventListener(
    "DOMContentLoaded",
    function () {

        button =
            document.getElementById(
                "weatherButton"
            );

        statusText =
            document.getElementById(
                "status"
            );


        console.log(
            "button:",
            button
        );

        console.log(
            "statusText:",
            statusText
        );


        button.addEventListener(
            "click",
            getLocation
        );
    }
);
function getPrecipitationText(type) {

    const precipitationTypes = {
        "0": "없음",
        "1": "비",
        "2": "비/눈",
        "3": "눈",
        "5": "빗방울",
        "6": "빗방울/눈날림",
        "7": "눈날림"
    };

    return precipitationTypes[type] || "알 수 없음";
}

function setLoading(isLoading) {

    if (isLoading) {

        button.disabled = true;
        button.textContent = "조회 중...";

        statusText.textContent =
            "현재 위치와 날씨 정보를 불러오는 중입니다.";

    } else {

        button.disabled = false;
        button.textContent = "현재 위치 날씨 조회";
    }
}

function formatWeatherTime(
    baseDate,
    baseTime
) {

    const year =
        baseDate.substring(0, 4);

    const month =
        baseDate.substring(4, 6);

    const day =
        baseDate.substring(6, 8);

    const hour =
        baseTime.substring(0, 2);

    const minute =
        baseTime.substring(2, 4);

    return (
        `${year}-${month}-${day} ` +
        `${hour}:${minute}`
    );
}

function getLocation() {

    if (!navigator.geolocation) {

        statusText.textContent =
            "이 브라우저에서는 위치 정보를 지원하지 않습니다.";

        return;
    }


    setLoading(true);


    navigator.geolocation.getCurrentPosition(
        getWeather,
        locationError,
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 60000
        }
    );
}


async function getWeather(position) {

    const latitude =
        position.coords.latitude;

    const longitude =
        position.coords.longitude;


    console.log("위도:", latitude);
    console.log("경도:", longitude);


    try {

        statusText.textContent =
            "기상청에서 날씨 정보를 가져오는 중입니다.";


        const response = await fetch(
            "/api/weather",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    lat: latitude,
                    lon: longitude
                })
            }
        );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "날씨 정보를 가져오지 못했습니다."
            );
        }


        document.getElementById(
            "temperature"
        ).textContent =
            data.temperature;


        document.getElementById(
            "humidity"
        ).textContent =
            data.humidity;


        document.getElementById(
            "windSpeed"
        ).textContent =
            data.windSpeed;

        document.getElementById(
            "rainfall"
        ).textContent =
            data.rainfall ?? "-";

        document.getElementById(
            "precipitationType"
        ).textContent =
            getPrecipitationText(
                data.precipitationType
            );

        document.getElementById(
            "baseTime"
        ).textContent =
            formatWeatherTime(
                data.baseDate,
                data.baseTime
            );

        statusText.textContent =
            "날씨 정보를 불러왔습니다.";

    }

    catch (error) {

        console.error(error);

        statusText.textContent =
            error.message;

    }

    finally {

        setLoading(false);
    }
}


function locationError(error) {

    console.error(error);


    switch (error.code) {

        case error.PERMISSION_DENIED:

            statusText.textContent =
                "위치 정보 사용 권한이 거부되었습니다.";

            break;


        case error.POSITION_UNAVAILABLE:

            statusText.textContent =
                "현재 위치 정보를 확인할 수 없습니다.";

            break;


        case error.TIMEOUT:

            statusText.textContent =
                "위치 정보를 가져오는 시간이 초과되었습니다.";

            break;


        default:

            statusText.textContent =
                "현재 위치를 가져오는 중 오류가 발생했습니다.";
    }


    setLoading(false);
}