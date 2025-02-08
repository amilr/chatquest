import os
import requests
from io import BytesIO

def log_prompt(prompt: str):
    label = "= imaging prompt "
    print(label + ("=" * (50 - len(label))))
    print(prompt.strip())
    print("=" * 50)

def clean_prompt(prompt: str) -> str:
    # Check and clean up the prompt if needed
    lines = prompt.split('\n')

    if len(lines) == 1:
        return prompt

    if 'prompt' in lines[0].lower():
        prompt = '\n'.join(lines[1:]).strip()
    
    # Remove wrapping double quotes if present
    if prompt.startswith('"') and prompt.endswith('"'):
        prompt = prompt[1:-1]

    return prompt

def generate_image(prompt: str, width: int, height: int) -> bytes:
    TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
    
    prompt = clean_prompt(prompt)
    log_prompt(prompt)
    
    try:
        url = "https://api.together.xyz/v1/images/generations"

        payload = {
            "model": "black-forest-labs/FLUX.1-schnell",
            "steps": 10,
            "n": 1,
            "height": height,
            "width": width,
            "guidance": 3.5,
            "prompt": prompt
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer {}".format(TOGETHER_API_KEY)
        }

        response = requests.post(url, json=payload, headers=headers)
        json_response = response.json()
        image_url = json_response['data'][0]['url']
        
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            io = BytesIO(image_response.content)
            return io.getvalue()
            
        return None
        
    except Exception as e:
        print(f"Image generation failed: {str(e)}")
        return None
    
def generate_image_large(prompt: str) -> bytes:
    return generate_image(prompt, 512, 512)

def generate_image_dynamic(prompt: str, cells: int) -> bytes:
    if cells == 1:
        width = 512
    else:
        width = cells * 256
    return generate_image(prompt, width, 256)