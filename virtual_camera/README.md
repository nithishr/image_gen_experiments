# Virtual Camera

This project is focused on image generation using a virtual camera based on a location picked by the user from the Map. The images are generated using [FLUX.1-schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell) model hosted on [Together.ai](https://www.together.ai/) based on the surroundings, weather and the location. It is inspired by [Paragraphica](https://bjoernkarmann.dk/project/paragraphica).

The app also has a tab to generate images based on custom prompt.

![img](app.png)

For the weather, [weatherAPI](https://www.weatherapi.com/) is used. For the information about the surroundings, [OpenSteetMap](https://www.openstreetmap.org/) is used.

You will need an API key for both weather api & together.ai to run the demo. Together.ai has free access to FLUX.1-schnell :)

## Installation

To get started with the project, clone the repository and install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

The API keys are read from the Streamlit secrets stored in the `.streamlit/secrets.toml` file.

It can be created from the `secrets.example.toml` file provided.

```
WEATHER_API_KEY = ""
TOGETHER_API_KEY = ""
```

## Usage

To run the virtual camera experiments, use the following command:

```bash
streamlit run virtual_camera.py
```

## License

This project is licensed under the MIT License.
