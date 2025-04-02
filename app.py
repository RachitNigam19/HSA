from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import logging  

# Setup logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Configure Gemini AI API
client = genai.Client(api_key="AIzaSyBtla9N2ZYwBXyb3O-aZ_OmrToybdFXvXU")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        if 'topic' not in request.form or 'ratio' not in request.form or 'prompt' not in request.form:
            return jsonify({'error': 'Missing prompt, topic, or ratio'}), 400

        prompt = request.form['prompt']
        topic = request.form['topic']
        ratio = request.form['ratio']
        logging.info(f"Received prompt: {prompt}, topic: {topic}, ratio: {ratio}")

        # Determine image size based on ratio
        size_map = {'1:1': (1080, 1080), '16:9': (1920, 1080), '4:3': (1200, 900)}
        width, height = size_map.get(ratio, (1080, 1080))

        # Generate image using Gemini AI
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['Text', 'Image']
            )
        )

        for part in response.candidates[0].content.parts:
            if part.text:
                logging.info(f"Generated text: {part.text}")
            elif part.inline_data:
                image_data = part.inline_data.data
                image = Image.open(BytesIO(image_data))
                image = image.resize((width, height))
                
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                filename = f"{topic.replace(' ', '_')}.png"
                return jsonify({'image': img_str, 'filename': filename})

        return jsonify({'error': 'No image generated'}), 400
    except Exception as e:
        logging.exception("Error generating image")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="127.0.0.1", port=8080)