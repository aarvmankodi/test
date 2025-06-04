
# 🚀 The AI Developer Challenge

### Make Something Insanely Great
Welcome. This isn’t just a coding task. This is a mission. A calling for the bold and curious—those who dare to think
differently. If you're ready to build something magical, something powerful, something *insanely great*—read on.

---

## 🌟 The Vision

Imagine this:  
A user types a simple idea —
> “Make me a glowing dragon standing on a cliff at sunset.”

And your app...

- Understands the request using a local LLM.
- Generates stunning visuals from text.
- Transforms that image into an interactive 3D model.
- Remembers it. Forever.

You're not building an app. You're building **a creative partner**.

---

## 🛠️ Key Technologies Used

-   **Python**: The core language for the application.
-   **Openfabric SDK**: For interacting with Openfabric apps.
-   **Hugging Face `transformers` & `torch`**: Used for local LLM-based prompt expansion. The current model is `TinyLlama/TinyLlama-1.1B-Chat-v1.0`.
-   **SQLite3**: For long-term memory storage of generation metadata.
-   **Flask & Connexion**: Underlying framework for the web API (provided by the boilerplate).
-   **Marshmallow**: For data serialization and validation (used in ontology).

---

## ⚙️ Configuration

Openfabric application IDs (which should be the resolvable hostnames of the apps) are configured in `app/config/properties.json` for the `super-user`. Ensure these are correctly set up before running the application. For example:
```json
{
  "super-user": {
    "app_ids": [
      "text-to-image-app-hostname.openfabric.network",
      "image-to-3d-app-hostname.openfabric.network"
    ]
  }
}
```
*Replace `"text-to-image-app-hostname.openfabric.network"` and `"image-to-3d-app-hostname.openfabric.network"` with the actual hostnames for the Text-to-Image (App ID: `f0997a01-d6d3-a5fe-53d8-561300318557`) and Image-to-3D (App ID: `69543f29-4d41-4afc-7f29-3d51591f11eb`) apps respectively.*

---

## 🎯 The Mission

Create an intelligent, end-to-end pipeline powered by Openfabric and a locally hosted LLM:

### Step 1: Understand the User

Uses a local LLM (**TinyLlama/TinyLlama-1.1B-Chat-v1.0** via the `transformers` library) to:

- Interpret prompts
- Expand them creatively
- Drive meaningful, artistic input into the generation process

### Step 2: Bring Ideas to Life

Chain two Openfabric apps together:

- **Text to Image**  
  App ID: `f0997a01-d6d3-a5fe-53d8-561300318557`  
  [View on Openfabric](https://openfabric.network/app/view/f0997a01-d6d3-a5fe-53d8-561300318557)

- **Image to 3D**  
  App ID: `69543f29-4d41-4afc-7f29-3d51591f11eb`  
  [View on Openfabric](https://openfabric.network/app/view/69543f29-4d41-4afc-7f29-3d51591f11eb)

Use their **manifest** and **schema** dynamically to structure requests.
Generated images and 3D models are saved in the `generated_outputs` directory within the application workspace.

### Step 3: Remember Everything

The application implements long-term memory by storing metadata about each generation:
- 🧠 **Short-Term**: Session context is handled by passing data through the pipeline steps during a single interaction.
- 💾 **Long-Term**: Details of each generation (original prompt, LLM-expanded prompt, paths to the generated image and 3D model, and a timestamp) are persisted across sessions in a SQLite database located at `generated_outputs/generation_memory.db`.

This database allows for recalling past creations. While advanced natural language recall (e.g., "regenerate the robot from last Thursday") is not yet implemented, the foundational data storage is in place for future enhancements. Users can inspect the database to see their generation history.

---

## 🛠 The Pipeline

User Prompt
↓
Local LLM (TinyLlama-1.1B-Chat-v1.0 via `transformers`) for prompt expansion
↓
Text-to-Image App (Openfabric, App ID: f0997a01-d6d3-a5fe-53d8-561300318557)
↓
Image Output (saved in `generated_outputs/`)
↓
Image-to-3D App (Openfabric, App ID: 69543f29-4d41-4afc-7f29-3d51591f11eb)
↓
3D Model Output (saved in `generated_outputs/`)
↓
Metadata and paths stored in SQLite DB (`generated_outputs/generation_memory.db`)

Simple. Elegant. Powerful.

---

## 📦 Deliverables

What we expect:

- ✅ Fully working Python project
- ✅ `README.md` with clear instructions
- ✅ Prompt → Image → 3D working example
- ✅ Logs or screenshots
- ✅ Memory functionality (clearly explained)

---

## 🧠 What We’re Really Testing

- Your grasp of the **Openfabric SDK** (`Stub`, `Remote`, `schema`, `manifest`)
- Your **creativity** in prompt-to-image generation
- Your **engineering intuition** with LLMs
- Your ability to manage **context and memory**
- Your **attention to quality** — code, comments, and clarity

---

## 🚀 Bonus Points

- 🎨 Visual GUI with Streamlit or Gradio
- 🔍 FAISS/ChromaDB for memory similarity
- 🗂 Local browser to explore generated 3D assets
- 🎤 Voice-to-text interaction

---

## ✨ Example Experience

Prompt:
> “Design a cyberpunk city skyline at night.”

→ LLM expands into vivid, textured visual descriptions  
→ Text-to-Image App renders a cityscape  
→ Image-to-3D app converts it into depth-aware 3D  
→ The system remembers the request for remixing later

That’s not automation. That’s imagination at scale.

---

### API Output Structure
The application returns a JSON object with the following structure:
```json
{
  "original_prompt": "User's initial prompt",
  "expanded_prompt": "Prompt as expanded by the local LLM",
  "image_path": "Path to the generated image (e.g., generated_outputs/image.png) or error/skipped message",
  "model_3d_path": "Path to the generated 3D model (e.g., generated_outputs/model.obj) or error/skipped message",
  "status_message": "A summary of the execution status"
}
```

---

## 💡 Where to start
The main application logic is orchestrated within the `execute` function in the `app/main.py` file. This function handles:
- Initialization of services (like the database).
- Processing of the input prompt.
- Orchestration of the generation pipeline (LLM expansion, Text-to-Image, Image-to-3D).
- Storing results for long-term memory.
- Preparing the structured output response.

Refer to `app/main.py` for the detailed implementation.

The Openfabric SDK's `Stub` class (see `app/core/stub.py`) is used to interact with configured Openfabric applications. An example of how an Openfabric app is called using the stub:
(The following is a conceptual example, the actual implementation details are in `app/main.py`)
```python
    # Conceptual example of calling an Openfabric app
    # Ensure 'stub' is initialized and the 'app_id_or_hostname' is correctly configured.
    # payload = {'prompt': 'Your data for the app'}
    # user_id = 'super-user'
    # output_object = stub.call(app_id_or_hostname, payload, user_id)
    # result = output_object.get('result')
    # # Process the result...
```

A more specific example from the original boilerplate showing how to call an app and save image output:
(Note: actual app hostnames/IDs and payload structure will vary based on the specific Openfabric app)
```python
    # Call the Text to Image app
    object = stub.call('c25dcd829d134ea98f5ae4dd311d13bc.node3.openfabric.network', {'prompt': 'Hello World!'}, 'super-user')
    image = object.get('result')
    # save to file
    with open('output.png', 'wb') as f:
        f.write(image)
```

## How to start
The application can be executed in two different ways:
* locally by running the `start.sh` 
* on in a docker container using `Dockerfile`

If all is fine you should be able to access the application on `http://localhost:8888/swagger-ui/#/App/post_execution` and see the following screen:

![Swagger UI](./swagger-ui.png)

## Ground Rules
Step up with any arsenal (read: libraries or packages) you believe in, but remember:
* 👎 External services like chatGPT are off-limits. Stand on your own.
* 👎 Plagiarism is for the weak. Forge your own path.
* 👎 A broken app equals failure. Non-negotiable.

## This Is It
We're not just evaluating a project; we're judging your potential to revolutionize our 
landscape. A half-baked app won’t cut it.

We're zeroing in on:
* 👍 Exceptional documentation.
* 👍 Code that speaks volumes.
* 👍 Inventiveness that dazzles.
* 👍 A problem-solving beast.
* 👍 Unwavering adherence to the brief