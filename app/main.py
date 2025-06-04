import logging
from typing import Dict
import os
from datetime import datetime
import base64
import sqlite3

from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

from ontology_dc8f06af066e4a7880a5938933236037.config import ConfigClass
from ontology_dc8f06af066e4a7880a5938933236037.input import InputClass
from ontology_dc8f06af066e4a7880a5938933236037.output import OutputClass
from openfabric_pysdk.context import AppModel, State
from core.stub import Stub

# Configurations for the app
configurations: Dict[str, ConfigClass] = dict()

# Initialize LLM pipeline
# Using a smaller model for easier setup. Replace with DeepSeek or Llama if resources allow.
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    # Check if CUDA is available and use it, otherwise use CPU
    device = 0 if torch.cuda.is_available() else -1
    llm_pipeline = pipeline(
        "text-generation",
        model=MODEL_NAME,
        tokenizer=tokenizer,
        torch_dtype=torch.bfloat16, # Use bfloat16 for better performance if available
        device=device, # device_map="auto" can also be used for multi-GPU
    )
    logging.info(f"LLM pipeline initialized with model: {MODEL_NAME} on device: {'cuda' if device == 0 else 'cpu'}")
except Exception as e:
    logging.error(f"Failed to load LLM model: {e}")
    llm_pipeline = None

TEXT_TO_IMAGE_APP_ID = "f0997a01-d6d3-a5fe-53d8-561300318557"
IMAGE_TO_3D_APP_ID = "69543f29-4d41-4afc-7f29-3d51591f11eb"
OUTPUT_DIR = "generated_outputs"

DATABASE_FILE = os.path.join(OUTPUT_DIR, "generation_memory.db")

def init_db():
    # Ensure the OUTPUT_DIR exists for the DB file
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logging.info(f"Created output directory for DB: {OUTPUT_DIR}")
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            original_prompt TEXT,
            expanded_prompt TEXT,
            image_path TEXT,
            model_3d_path TEXT
        )
    ''')
    conn.commit()
    conn.close()
    logging.info(f"Database initialized/checked at {DATABASE_FILE}")

############################################################
# Config callback function
############################################################
def config(configuration: Dict[str, ConfigClass], state: State) -> None:
    """
    Stores user-specific configuration data.

    Args:
        configuration (Dict[str, ConfigClass]): A mapping of user IDs to configuration objects.
        state (State): The current state of the application (not used in this implementation).
    """
    for uid, conf in configuration.items():
        logging.info(f"Saving new config for user with id:'{uid}'")
        configurations[uid] = conf


############################################################
# Execution callback function
############################################################
def execute(model: AppModel) -> None:
    """
    Main execution entry point for handling a model pass.

    Args:
        model (AppModel): The model object containing request and response structures.
    """
    init_db() # Initialize database

    # Retrieve input
    request: InputClass = model.request

    # Retrieve user config
    user_config: ConfigClass = configurations.get('super-user', None)
    logging.info(f"{configurations}")

    # Initialize the Stub with app IDs
    app_ids = user_config.app_ids if user_config else []
    stub = Stub(app_ids)
    logging.info(f"Stub initialized. Available connections: {list(stub._connections.keys())}")
    logging.info(f"User config app_ids: {user_config.app_ids if user_config else 'No user_config'}")

    # ------------------------------
    # TODO : add your magic here
    # ------------------------------

    expanded_prompt = ""
    if llm_pipeline is not None and request.prompt:
        # Create a more descriptive prompt for the LLM
        messages = [
            {
                "role": "system",
                "content": "You are an expert creative assistant. Expand the following user idea into a vivid and detailed description suitable for an image generation model. Focus on visual details, artistic style, and composition. Make it about 2-3 sentences long.",
            },
            {"role": "user", "content": request.prompt},
        ]
        prompt_for_llm = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        try:
            logging.info(f"Original prompt: {request.prompt}")
            # Adjust max_length and other parameters as needed
            # The max_length should be sufficient for the prompt + expansion
            outputs = llm_pipeline(
                prompt_for_llm,
                max_new_tokens=150, # Max tokens to generate for the expansion
                num_return_sequences=1,
                eos_token_id=tokenizer.eos_token_id,
                do_sample=True,
                temperature=0.7,
                top_k=50,
                top_p=0.95
            )
            generated_text = outputs[0]['generated_text']

            # Extract only the assistant's response
            # The generated_text will contain the input prompt as well.
            # We need to find where the assistant's response starts.
            assistant_response_start = generated_text.find(tokenizer.apply_chat_template([{"role": "assistant", "content": ""}], tokenize=False, add_generation_prompt=False))
            if assistant_response_start != -1:
                expanded_prompt = generated_text[assistant_response_start:].replace(tokenizer.apply_chat_template([{"role": "assistant", "content": ""}], tokenize=False, add_generation_prompt=False), "").strip()
            else:
                # Fallback if the exact template match isn't found (should be rare for chat models)
                # This tries to remove the input prompt part.
                input_part = prompt_for_llm.replace(tokenizer.bos_token, "").replace(tokenizer.eos_token, "")
                expanded_prompt = generated_text.replace(input_part, "").strip()

            logging.info(f"Expanded prompt: {expanded_prompt}")
        except Exception as e:
            logging.error(f"Error during LLM prompt expansion: {e}")
            expanded_prompt = f"Error expanding prompt: {request.prompt}" # Fallback
    elif not request.prompt:
        expanded_prompt = "No prompt provided."
        logging.warning("No prompt provided by the user.")
    else:
        expanded_prompt = f"LLM not available. Using original prompt: {request.prompt}"
        logging.warning("LLM pipeline not available. Using original prompt.")

    image_path = None
    image_filename = "generated_image.png" # Default filename

    if TEXT_TO_IMAGE_APP_ID in stub._connections: # Check if connection to app was successful
        logging.info(f"Calling Text-to-Image app ({TEXT_TO_IMAGE_APP_ID}) with prompt: {expanded_prompt}")
        try:
            # Ensure output directory exists
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)
                logging.info(f"Created output directory: {OUTPUT_DIR}")

            text_to_image_payload = {'prompt': expanded_prompt}

            image_output_object = stub.call(TEXT_TO_IMAGE_APP_ID, text_to_image_payload, 'super-user')

            if image_output_object:
                image_data = image_output_object.get('result')
                if image_data:
                    image_filename = f"generated_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    image_path = os.path.join(OUTPUT_DIR, image_filename)

                    with open(image_path, 'wb') as f:
                        f.write(image_data)
                    logging.info(f"Text-to-Image generation successful. Image saved to: {image_path}")
                else:
                    logging.error("Text-to-Image app returned no 'result' field or empty data.")
                    image_path = "Error: Text-to-Image app returned no image data."
            else:
                logging.error("Text-to-Image app returned no output.")
                image_path = "Error: Text-to-Image app returned no output."
        except Exception as e:
            logging.error(f"Error during Text-to-Image generation: {e}")
            image_path = f"Error during Text-to-Image: {str(e)}"
    else:
        logging.warning(f"Text-to-Image app ({TEXT_TO_IMAGE_APP_ID}) not configured or connection failed. Skipping image generation.")
        logging.warning(f"Available connections for stub: {list(stub._connections.keys())}")
        image_path = "Skipped: Text-to-Image app not available."

    model_3d_path = None
    model_3d_filename = "generated_model.obj" # Default, actual format might vary

    if image_path and os.path.exists(image_path) and not image_path.startswith("Error") and not image_path.startswith("Skipped"):
        if IMAGE_TO_3D_APP_ID in stub._connections: # Check if connection to app was successful
            logging.info(f"Calling Image-to-3D app ({IMAGE_TO_3D_APP_ID}) with image: {image_path}")
            try:
                # Read the generated image and encode it as base64
                with open(image_path, "rb") as image_file:
                    image_data_bytes = image_file.read()
                    base64_encoded_image = base64.b64encode(image_data_bytes).decode('utf-8')

                image_to_3d_payload = {'image': base64_encoded_image, 'filename': os.path.basename(image_path)}

                model_3d_output_object = stub.call(IMAGE_TO_3D_APP_ID, image_to_3d_payload, 'super-user')

                if model_3d_output_object:
                    model_data = model_3d_output_object.get('result')
                    output_filename_suggestion = model_3d_output_object.get('filename', model_3d_filename)

                    if model_data:
                        model_3d_filename = f"generated_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{output_filename_suggestion}"
                        model_3d_path = os.path.join(OUTPUT_DIR, model_3d_filename)

                        with open(model_3d_path, 'wb') as f:
                            f.write(model_data)
                        logging.info(f"Image-to-3D generation successful. Model saved to: {model_3d_path}")
                    else:
                        logging.error("Image-to-3D app returned no 'result' field or empty data.")
                        model_3d_path = "Error: Image-to-3D app returned no model data."
                else:
                    logging.error("Image-to-3D app returned no output.")
                    model_3d_path = "Error: Image-to-3D app returned no output."
            except Exception as e:
                logging.error(f"Error during Image-to-3D generation: {e}")
                model_3d_path = f"Error during Image-to-3D: {str(e)}"
        else:
            logging.warning(f"Image-to-3D app ({IMAGE_TO_3D_APP_ID}) not configured or connection failed. Skipping 3D model generation.")
            model_3d_path = "Skipped: Image-to-3D app not available."
    elif image_path and (image_path.startswith("Error") or image_path.startswith("Skipped")):
        logging.warning(f"Skipping Image-to-3D generation because image generation failed or was skipped: {image_path}")
        model_3d_path = "Skipped: Image generation failed or was skipped."
    else:
        logging.warning("Skipping Image-to-3D generation because no valid image path was provided.")
        model_3d_path = "Skipped: No image generated."

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO generations (original_prompt, expanded_prompt, image_path, model_3d_path)
            VALUES (?, ?, ?, ?)
        ''', (request.prompt, expanded_prompt, image_path, model_3d_path))
        conn.commit()
        conn.close()
        logging.info(f"Generation data saved to database for prompt: {request.prompt}")
    except Exception as e:
        logging.error(f"Error saving generation data to database: {e}")

    # Prepare structured response
    response_object: OutputClass = model.response

    response_object.original_prompt = request.prompt
    response_object.expanded_prompt = expanded_prompt
    response_object.image_path = image_path
    response_object.model_3d_path = model_3d_path

    # Construct a status message
    status = "Pipeline execution completed."
    if image_path and (image_path.startswith("Error") or image_path.startswith("Skipped")):
        status += f" Image generation issue: {image_path.split(':', 1)[-1].strip()}."
    if model_3d_path and (model_3d_path.startswith("Error") or model_3d_path.startswith("Skipped")):
        status += f" 3D model generation issue: {model_3d_path.split(':', 1)[-1].strip()}."

    response_object.status_message = status

    logging.info(f"Execution finished. Response: original_prompt='{response_object.original_prompt}', "
                 f"expanded_prompt='{response_object.expanded_prompt}', image_path='{response_object.image_path}', "
                 f"model_3d_path='{response_object.model_3d_path}', status_message='{response_object.status_message}'")