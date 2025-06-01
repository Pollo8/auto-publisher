import datetime as dt
import json
import os
import pathlib
import io

from slugify import slugify
from huggingface_hub import InferenceClient
from jinja2 import Template
from PIL import Image

# ── конфигурация ────────────────────────────────────────────────────────────────
HF_TOKEN = os.getenv("HF_TOKEN") or ""

# Открытая LLM, не-gated
LLM_ID = "HuggingFaceH4/zephyr-7b-beta"
# Популярная SD-модель, доступная через Inference API
IMG_ID = "CompVis/stable-diffusion-v1-4"

client = InferenceClient(token=HF_TOKEN)
POST_TMPL = Template(pathlib.Path("templates/post.md").read_text("utf-8"))

# ── функции генерации ───────────────────────────────────────────────────────────
def llm(prompt: str) -> str:
    """
    Вызывает text_generation и возвращает чистый текст.
    HuggingFaceHub InferenceClient иногда отдаёт словарь или список словарей,
    поэтому мы извлекаем именно строку.
    """
    raw = client.text_generation(
        prompt=prompt,
        model=LLM_ID,
        max_new_tokens=700,
        temperature=0.7,
    )

    # Если вернулся словарь вида {"generated_text": "…"}, то достаём его
    if isinstance(raw, dict):
        return raw.get("generated_text", "").strip()
    # Если вернулся список словарей, берём первый
    if isinstance(raw, list) and len(raw) > 0 and isinstance(raw[0], dict):
        return raw[0].get("generated_text", "").strip()
    # Если всё-таки вернулась строка, просто возвращаем
    if isinstance(raw, str):
        return raw.strip()

    # На крайний случай приводим к строке
    return str(raw).strip()


def sd(prompt: str) -> Image.Image:
    """
    Пытаемся сгенерировать иллюстрацию. Если провайдер не найден или модель недоступна,
    будет выброшено исключение. Обертка вызова ловит его далее в основном цикле.
    """
    png_bytes = client.text_to_image(
        prompt=prompt,
        model=IMG_ID,
        height=768,
        width=768,
    )
    return Image.open(io.BytesIO(png_bytes))


# ── главный цикл ────────────────────────────────────────────────────────────────
queue_file = max(pathlib.Path("topics").glob("queue_*.json"))
ideas = json.loads(queue_file.read_text("utf-8"))

for idea in ideas:
    slug = slugify(idea)
    md_path = pathlib.Path(f"website/content/posts/{slug}.md")
    img_path = f"website/content/posts/{slug}.png"

    # Если файл уже существует, пропускаем
    if md_path.exists():
        continue

    print("Writing:", idea)

    # 1) Генерируем статью
    article_text = llm(
        f"Напиши 700-словную практическую статью на русском языке про «{idea}». "
        "Тон дружелюбный, без упоминания ИИ."
    )

    # 2) Пытаемся сгенерировать иллюстрацию, если не получилось — hero остаётся пустой строкой
    hero = ""
    try:
        img = sd(f"{idea}, flat illustration, soft colours")
        img.save(img_path)
        hero = img_path
    except Exception as e:
        print(f"Image generation failed for '{idea}': {e}")

    # 3) Рендерим Markdown (передаём hero = путь к картинке или пустую строку)
    md = POST_TMPL.render(
        title=idea.capitalize(),
        date=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        hero=hero,
        body=article_text,
    )
    md_path.write_text(md, "utf-8")
