from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer, util
import fitz  # PyMuPDF
import textstat

app = FastAPI()

# ✅ CORS (VERY IMPORTANT for frontend connection)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- MODELS ----------------
model_name = "google/flan-t5-base"
translation_model_name = "facebook/nllb-200-distilled-600M"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

trans_tokenizer = AutoTokenizer.from_pretrained(translation_model_name)
trans_model = AutoModelForSeq2SeqLM.from_pretrained(translation_model_name)

similarity_model = SentenceTransformer('all-MiniLM-L6-v2')

# ---------------- REQUEST MODEL ----------------
class TextRequest(BaseModel):
    text: str
    target_lang: str = "hindi"

# ---------------- LANGUAGE MAP ----------------
LANGUAGES = {
    "hindi": "hin_Deva",
    "telugu": "tel_Telu",
    "tamil": "tam_Taml",
    "malayalam": "mal_Mlym",
    "kannada": "kan_Knda",
    "marathi": "mar_Deva",
    "bengali": "ben_Beng",
    "gujarati": "guj_Gujr",
    "punjabi": "pan_Guru",
    "odia": "ory_Orya",
    "urdu": "urd_Arab"
}

# ---------------- CHUNK FUNCTION ----------------
def split_text(text, max_words=80):
    words = text.split()
    return [" ".join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

# ---------------- PDF TEXT EXTRACTION ----------------
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# ---------------- HOME ----------------
@app.get("/")
def home():
    return {"message": "Legal Document AI Backend Running Successfully 🚀"}

# ---------------- SIMPLIFY ----------------
@app.post("/simplify")
def simplify_text(request: TextRequest):
    chunks = split_text(request.text)
    result = []

    for chunk in chunks:
        inputs = tokenizer(
            "Simplify this legal text in simple English: " + chunk,
            return_tensors="pt",
            truncation=True
        )
        outputs = model.generate(**inputs, max_length=150)
        result.append(tokenizer.decode(outputs[0], skip_special_tokens=True))

    return {"simplified": " ".join(result)}

# ---------------- SUMMARIZE ----------------
@app.post("/summarize")
def summarize_text(request: TextRequest):
    chunks = split_text(request.text)
    result = []

    for chunk in chunks:
        inputs = tokenizer(
            "Summarize this legal text clearly: " + chunk,
            return_tensors="pt",
            truncation=True
        )
        outputs = model.generate(**inputs, max_length=150)
        result.append(tokenizer.decode(outputs[0], skip_special_tokens=True))

    return {"summary": " ".join(result)}

# ---------------- SIMILARITY ----------------
@app.post("/similarity")
def check_similarity(request: TextRequest):
    inputs = tokenizer(
        "Simplify this legal text: " + request.text,
        return_tensors="pt",
        truncation=True
    )
    outputs = model.generate(**inputs, max_length=150)

    simplified = tokenizer.decode(outputs[0], skip_special_tokens=True)

    embeddings = similarity_model.encode([request.text, simplified])
    score = util.cos_sim(embeddings[0], embeddings[1]).item()

    return {
        "simplified": simplified,
        "similarity_score": round(score, 3)
    }

# ---------------- TRANSLATE ----------------
@app.post("/translate")
def translate_text(request: TextRequest):

    # Step 1: Simplify
    chunks = split_text(request.text)
    simplified_chunks = []

    for chunk in chunks:
        inputs = tokenizer(
            "Explain this legal text in simple English: " + chunk,
            return_tensors="pt",
            truncation=True
        )
        outputs = model.generate(**inputs, max_length=150)
        simplified_chunks.append(tokenizer.decode(outputs[0], skip_special_tokens=True))

    simplified_text = " ".join(simplified_chunks)

    # Step 2: Language selection
    target_lang = LANGUAGES.get(request.target_lang.lower(), "hin_Deva")

    # Step 3: Set source language
    trans_tokenizer.src_lang = "eng_Latn"

    translated_chunks = []

    for chunk in split_text(simplified_text):
        trans_inputs = trans_tokenizer(chunk, return_tensors="pt", truncation=True)

        trans_outputs = trans_model.generate(
            **trans_inputs,
            forced_bos_token_id=trans_tokenizer.convert_tokens_to_ids(target_lang),
            max_length=200,
            repetition_penalty=2.0,
            no_repeat_ngram_size=3
        )

        translated_chunks.append(
            trans_tokenizer.decode(trans_outputs[0], skip_special_tokens=True)
        )

    return {
        "simplified": simplified_text,
        "translated_text": " ".join(translated_chunks),
        "language": request.target_lang
    }

# ================= PDF APIs =================

@app.post("/pdf/simplify")
async def simplify_pdf(file: UploadFile = File(...)):
    content = await file.read()
    text = extract_text_from_pdf(content)
    return simplify_text(TextRequest(text=text))

@app.post("/pdf/summarize")
async def summarize_pdf(file: UploadFile = File(...)):
    content = await file.read()
    text = extract_text_from_pdf(content)
    return summarize_text(TextRequest(text=text))

@app.post("/pdf/translate")
async def translate_pdf(file: UploadFile = File(...), target_lang: str = "hindi"):
    content = await file.read()
    text = extract_text_from_pdf(content)
    return translate_text(TextRequest(text=text, target_lang=target_lang))

# -------- KEYWORDS --------
@app.post("/keywords")
def extract_keywords(request: TextRequest):
    words = list(set(request.text.split()))
    return {"keywords": words[:10]}

# -------- READABILITY --------
@app.post("/readability")
def readability_score(request: TextRequest):
    score = textstat.flesch_reading_ease(request.text)
    return {"readability_score": score}

# -------- LANGUAGES --------
@app.get("/languages")
def get_languages():
    return LANGUAGES