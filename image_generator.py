from openai import OpenAI
client = OpenAI()
class ImageGenerator:
    def __init__(self, api_key):
        self.api_key = api_key
        # openai.api_key = api_key
    def generate_image(self, text):
        response = client.images.generate(
            model="dall-e-3",
            prompt=text,
            n=1,
            quality="hd",
            user="chatdev-viewer-app",
            size="1792x1024",
            style="vivid"
        )
        image = response.data[0].url
        return image