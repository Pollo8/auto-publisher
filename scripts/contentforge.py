import datetime as dt, json, os, pathlib, base64, io
from slugify import slugify
from huggingface_hub import InferenceClient
from jinja2 import Template
from PIL import Image

HF_TOKEN = os.getenv('HF_TOKEN') or ''  # локально можно временно оставить пустым
LLM_ID   = "NousResearch/Llama-3-8B-Instruct"
SD_ID    = "stabilityai/stable-diffusion-3.5-medium"

client = InferenceClient(token=HF_TOKEN)
POST_TMPL = Template(pathlib.Path('templates/post.md').read_text('utf-8'))

def llm(prompt):
    return client.text_generation(LLM_ID, prompt, max_new_tokens=700)

def sd(prompt):
    img_b64 = client.text_to_image(SD_ID, prompt, size="1024x1024", format="png")
    return Image.open(io.BytesIO(base64.b64decode(img_b64)))

queue_file = max(pathlib.Path('topics').glob('queue_*.json'))
ideas = json.loads(queue_file.read_text('utf-8'))

for idea in ideas:
    slug = slugify(idea)
    md_path = pathlib.Path(f'website/content/posts/{slug}.md')
    if md_path.exists():
        continue

    print("Writing:", idea)
    article = llm(f"Напиши 700-словную практическую статью на русском языке про {idea}. Тон дружелюбный, без упоминания ИИ.")
    img = sd(f"{idea}, flat illustration, soft colors")
    hero = f'website/content/posts/{slug}.png'
    img.save(hero)

    md = POST_TMPL.render(
        title = idea.capitalize(),
        date  = dt.datetime.utcnow().isoformat(),
        hero  = hero,
        body  = article
    )
    md_path.write_text(md, 'utf-8')