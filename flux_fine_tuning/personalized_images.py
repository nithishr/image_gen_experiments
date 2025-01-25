import replicate
import streamlit as st
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.chat_models import ChatOllama

MODEL_NAME = st.secrets["MODEL_NAME"]


def generate_prompt_for_photo(seed_prompt: str) -> str:
    """Generate the prompt for the photo generation model using LLM."""
    llm = ChatOllama(
        model="llama3.1",
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Write a prompt for an image generation model. The prompts should describe a person named NITHISH in various scenarios. Make sure to use the word NITHISH in all caps in every prompt. Make the prompts highly detailed and interesting, and make them varied in subject matter. Make sure the prompts will generate images that include unobscured facial details. NITHISH is an adult male in 30s from India. Include some reference to this in prompt to avoid misrepresenting NITHISH's age or gender. Always ask for high quality images. Return only the new prompt and nothing else.",
            ),
            ("human", "{input}"),
        ]
    )

    # Generate the prompt using LLM
    chain = prompt | llm

    response = chain.invoke(input=seed_prompt)
    return response


def generate_photo(prompt, model, steps=10, num_outputs=1):
    """Generate the photo using the model."""
    output = replicate.run(
        MODEL_NAME,
        input={
            "model": model,
            "prompt": prompt,
            "go_fast": False,
            "lora_scale": 1,
            "megapixels": "1",
            "num_outputs": num_outputs,
            "aspect_ratio": "1:1",
            "output_format": "webp",
            "guidance_scale": 3,
            "output_quality": 80,
            "prompt_strength": 0.8,
            "extra_lora_scale": 1,
            "num_inference_steps": steps,
        },
    )
    return output


if __name__ == "__main__":
    # Set the page configuration for Streamlit app
    st.set_page_config(
        page_title="Personalized Photo Generator",
        layout="wide",
        initial_sidebar_state="expanded",
        page_icon="📸",
    )

    if "generated" not in st.session_state:
        st.session_state.generated = False

    with st.sidebar:
        st.title("Personalized Photo Generator")
        with st.form(key="generate_photo"):
            prompt = st.text_area(
                "Prompt",
                "A low-light, medium shot photograph of NITHISH standing in an urban setting. There are skyscrapers in the background. 8k highest resolution with sharp intricate details. Hyperrealistic, detailed, and vivid.",
            )

            model = st.selectbox("Model", ["dev", "schnell"], index=0)
            steps = st.slider("Steps", min_value=1, max_value=50, value=10)
            no_of_outputs = st.slider(
                "Number of Images", min_value=1, max_value=10, value=1
            )
            rewrite_prompt = st.checkbox(
                "Refine prompt using LLM", key="rewrite_prompt"
            )

            # Generate the refined prompt using LLM
            if rewrite_prompt:
                refined_prompt = generate_prompt_for_photo(prompt)
                st.text_area("Refined Prompt", refined_prompt.content)

            # Generate the photo using the model
            if st.form_submit_button("Generate", icon="📸"):
                st.session_state.generated = True
                if rewrite_prompt:
                    photo_output = generate_photo(
                        refined_prompt.content,
                        model,
                        steps=steps,
                        num_outputs=no_of_outputs,
                    )
                else:
                    photo_output = generate_photo(
                        prompt, model, steps=steps, num_outputs=no_of_outputs
                    )

    if st.session_state["generated"]:
        for idx, file_output in enumerate(photo_output):
            st.image(file_output.read())
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            # Save the output image
            with open(f"outputs/output_{idx}_{timestamp}.png", "wb") as f:
                f.write(file_output.read())
