import base64
import random
import folium
import streamlit as st

from streamlit_folium import st_folium
import httpx
import logging
from together import Together

# PyConWeb location: CIC Berlin
PYCON_LOCATION = [52.4940361, 13.4436947]
# Constants
WEATHER_API_BASE = "https://api.weatherapi.com/v1/current.json"
WEATHER_API_KEY = st.secrets["WEATHER_API_KEY"]
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
IMAGE_HEIGHT = 768
IMAGE_WIDTH = 1024
IMAGE_GENERATION_MODEL = "black-forest-labs/FLUX.1-schnell-Free"
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"


def get_weather_from_gps_coordinates(lat: float, lon: float) -> dict[str:any]:
    "Get the weather & location based on the GPS coordinates"

    weather_url = f"{WEATHER_API_BASE}?key={WEATHER_API_KEY}&q={lat},{lon}&aqi=no"
    response = httpx.get(weather_url)

    output = {}
    if response.status_code == 200:
        data = response.json()
        output["location"] = data["location"]
        output["temperature"] = data["current"]["temp_c"]
        output["condition"] = data["current"]["condition"]["text"]
    else:
        logging.error("Error getting the weather:", response.status_code, response.text)

    return output


def get_surroundings(lat: float, lon: float, radius: int = 100) -> set[str]:
    "Get the surroundings based on the GPS coordinates and the search radius"
    url = OVERPASS_API_URL

    # Overpass query to get the amenities around the GPS coordinates
    query = f"""
    [out:json];
    (
    node["amenity"](around:{radius},{lat},{lon});
    );
    out body;
    """

    tags = set()

    try:
        # Send the request
        response = httpx.get(url, params={"data": query})

        # Check response status
        if response.status_code == 200:
            data = response.json()  # Parse JSON response
            # print(data)  # Print JSON data
            for element in data["elements"]:
                if "tags" in element:
                    tags.add(element["tags"]["amenity"])

        else:
            logging.error(
                "Error calling Open Street Maps API:",
                response.status_code,
                response.text,
            )
    except Exception as e:
        logging.error("Error calling Open Street Maps API:", e)

    return tags


def generate_image_from_prompt(prompt: str) -> bytes:
    "Generate image from the prompt using Together AI"
    try:
        client = Together(api_key=TOGETHER_API_KEY)
        response = client.images.generate(
            prompt=prompt,
            model=IMAGE_GENERATION_MODEL,
            width=IMAGE_WIDTH,
            height=IMAGE_HEIGHT,
            steps=4,
            n=1,
            response_format="b64_json",
        )
        b64_json = response.data[0].b64_json
        img_data = base64.b64decode(b64_json)
        st.session_state.image = img_data
        st.session_state.prompt = prompt
        return img_data
    except Exception as e:
        logging.error("Error generating the image:", e)


def generate_photo(gps_coordinates: list[float], radius: int = 100) -> None:
    "Generate photo from the GPS coordinates"
    if not gps_coordinates:
        logging.warning(
            "Please click on the map to get the GPS coordinates. Using default GPS coordinates."
        )
        gps_coordinates = {"lat": PYCON_LOCATION[0], "lng": PYCON_LOCATION[1]}

    # Get the weather details
    weather = get_weather_from_gps_coordinates(
        gps_coordinates["lat"], gps_coordinates["lng"]
    )
    st.session_state.weather = weather

    # Get the surroundings information
    surrounding_tags = get_surroundings(
        gps_coordinates["lat"], gps_coordinates["lng"], radius=radius
    )
    st.session_state.tags = surrounding_tags

    # Get random 3 tags from the surrounding tags
    if len(surrounding_tags) < 3:
        random_tags = ", ".join(surrounding_tags)
    else:
        random_tags = ", ".join(random.sample(list(surrounding_tags), 3))

    # Generate the image with the prompt based on location and surroundings
    prompt = f"A realistic photo taken at {weather['location']['name']}, {weather['location']['region']}, {weather['location']['country']}. The weather is {weather['condition']} and {weather['temperature']}°C. The time is {weather['location']['localtime']}."

    # If there are amenities nearby, add them to the prompt
    if random_tags:
        prompt += f"Nearby there is {random_tags}."

    st.session_state.prompt = prompt
    image = generate_image_from_prompt(prompt)
    st.session_state.image = image


if __name__ == "__main__":
    # Set the page configuration and initialize the session state variables
    st.set_page_config(
        page_title="Virtual Camera",
        page_icon="📸",
        layout="wide",
        initial_sidebar_state="auto",
        menu_items=None,
    )
    if "weather" not in st.session_state:
        st.session_state.weather = {}

    if "tags" not in st.session_state:
        st.session_state.tags = {}

    if "prompt" not in st.session_state:
        st.session_state.prompt = ""

    if "image" not in st.session_state:
        st.session_state.image = None

    # create tabs in the application
    image_generation, map_photo_generator = st.tabs(["Flux-Schnell", "Virtual 📸"])
    st.write("Generated using Flux Schnell Model via Together AI")

    with image_generation:
        prompt = st.text_area(
            "Enter a prompt for the image generation",
            "photography, orange hue, korean woman model, solid orange backdrop, using a camera setup that mimics a large aperture, f/1. 4 --ar 9:16 --style raw",
        )

        generate = st.button(
            "Generate Image",
            on_click=generate_image_from_prompt,
            kwargs={"prompt": prompt},
            icon="📸",
        )

        if generate:
            st.write(st.session_state.prompt)
            st.image(st.session_state.image, use_container_width=True)

    with map_photo_generator:
        st.title("Virtual 📸")

        # center map on PyConWeb, add marker
        map = folium.Map(location=PYCON_LOCATION, zoom_start=8, height=768, width=1024)
        folium.Marker(PYCON_LOCATION, popup="PyConWeb", tooltip="PyConWeb").add_to(map)

        col1, col2 = st.columns(2, vertical_alignment="center")

        with col1:
            # call to render Folium map in Streamlit
            selected_location = st_folium(
                map, width=1024, height=768, returned_objects=["last_clicked"]
            )

        clicked = st.button(
            "Click",
            on_click=generate_photo,
            kwargs={"gps_coordinates": selected_location["last_clicked"]},
            icon="📸",
        )

        with col2:
            if clicked:
                st.write(st.session_state.prompt)
                st.image(st.session_state.image, use_container_width=True)
                if selected_location["last_clicked"]:
                    st.write(
                        f"[📍](https://www.google.com/maps/search/?api=1&query={selected_location['last_clicked']['lat']},{selected_location['last_clicked']['lng']})"
                    )
