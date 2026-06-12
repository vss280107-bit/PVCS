# lightweight nlp model
"""
ML Engine — Pure-Python NLP.
Provides quality scoring, TF-IDF similarity, and rule-based AI suggestions.
"""
import re, math, random
from typing import List, Dict, Tuple, Optional
from collections import Counter

# Tokenizer
def tokenize(text: str) -> List[str]:
    return re.findall(r"\b\w+\b", text.lower())

def sentence_split(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]

# Lexicons
VAGUE = {"thing","stuff","something","somehow","whatever","maybe","perhaps",
         "kind of","sort of","basically","generally","often","usually",
         "sometimes","a lot","very","really","quite","rather"}

INSTRUCTION = {"explain","describe","list","provide","generate","create","write",
               "analyze","summarize","compare","evaluate","suggest","recommend",
               "identify","outline","define","calculate","translate","convert",
               "review","assess","classify","extract","format","rewrite","improve"}

STRUCTURE = {"step","first","second","third","finally","then","next",
             "additionally","furthermore","however","therefore","because",
             "example","note","important","constraint","requirement"}

POSITIVE = {"please","great","good","excellent","helpful","clear","accurate",
            "detailed","comprehensive","thorough","precise","concise"}

NEGATIVE = {"bad","wrong","incorrect","avoid","do not","never","cannot",
            "impossible","failure","error","unclear","vague","confusing"}

# Scoring
def compute_clarity_score(text: str) -> float:
    tokens = tokenize(text)
    if not tokens: return 0.0
    sentences = sentence_split(text)
    vague_penalty = min(sum(1 for t in tokens if t in VAGUE) / max(len(tokens),1) * 3, 0.5)
    avg_len = len(tokens) / max(len(sentences), 1)
    length_score = 1.0 - abs(avg_len - 17) / 30
    instr_bonus = min(sum(1 for t in tokens if t in INSTRUCTION) * 0.1, 0.3)
    return round(max(0.0, min(1.0, length_score - vague_penalty + instr_bonus)), 3)

def compute_specificity_score(text: str) -> float:
    tokens = tokenize(text)
    if not tokens: return 0.0
    score = 0.3
    if re.search(r"\d+", text): score += 0.2
    if re.search(r"\b[A-Z][a-z]+\b", text): score += 0.15
    if re.search(r"`[^`]+`|\"[^\"]+\"", text): score += 0.2
    score += min(sum(1 for t in tokens if t in STRUCTURE) * 0.05, 0.15)
    score += min(len(tokens) / 200, 0.15)
    return round(min(score, 1.0), 3)

def compute_sentiment(text: str) -> str:
    t = set(tokenize(text))
    pos = len(t & POSITIVE); neg = len(t & NEGATIVE)
    return "positive" if pos > neg else "cautionary" if neg > pos else "neutral"

def compute_quality_score(text: str) -> Tuple[float, float, float]:
    clarity = compute_clarity_score(text)
    spec    = compute_specificity_score(text)
    n       = len(tokenize(text))
    length_bonus = 0.1 if 30 <= n <= 300 else (-0.2 if n < 10 else 0.0)
    overall = round(min(1.0, max(0.0, clarity * 0.4 + spec * 0.4 + 0.2 + length_bonus)), 3)
    return overall, clarity, spec

# TF-IDF Similarity 
def tfidf_similarity(a: str, b: str) -> float:
    def tfidf(tokens, corpus):
        tf = Counter(tokens); n = len(corpus)
        return {w: (c/len(tokens)) * (math.log((n+1)/(sum(1 for d in corpus if w in d)+1))+1)
                for w, c in tf.items()}
    at = tokenize(a); bt = tokenize(b)
    va = tfidf(at, [set(at), set(bt)]); vb = tfidf(bt, [set(at), set(bt)])
    words = set(va)|set(vb)
    dot = sum(va.get(w,0)*vb.get(w,0) for w in words)
    ma = math.sqrt(sum(v**2 for v in va.values()))
    mb = math.sqrt(sum(v**2 for v in vb.values()))
    return round(dot/(ma*mb), 4) if ma and mb else 0.0

# Suggestion Templates 
TEMPLATES = {
    "clarity": [
        ("Specify the exact output format",
         lambda t: t + "\n\nOutput format: Provide a structured response with clear sections and bullet points.",
         "Specifying output format reduces ambiguity and dramatically improves response consistency."),
        ("Remove vague hedging language",
         lambda t: re.sub(r"\b(very|really|quite|rather|basically|somehow|kind of|sort of)\b\s*", "", t, flags=re.I).strip(),
         "Hedging words weaken prompts. Direct language produces more precise AI responses."),
        ("Add explicit action verb",
         lambda t: ("Please " + t[0].lower() + t[1:]) if not t.lower().startswith(("please","you","i","analyze","write","create","generate","list","explain")) else t,
         "Action verbs at the start activate task-focused processing in language models."),
    ],
    "specificity": [
        ("Define the target audience explicitly",
         lambda t: t + "\n\nTarget audience: [Specify: developer / student / business professional / general public]",
         "Audience context enables the model to calibrate vocabulary, depth, and tone appropriately."),
        ("Add concrete constraints and limits",
         lambda t: t + "\n\nConstraints:\n- Response length: 200-400 words\n- Format: Use bullet points for lists\n- Tone: Professional and concise",
         "Hard constraints prevent over-verbose responses and keep output within expected parameters."),
        ("Include a worked example",
         lambda t: t + "\n\nExample of expected output:\n[Provide a short example here to anchor the response]",
         "Few-shot examples are the single most effective technique for improving output quality."),
    ],
    "structure": [
        ("Add role-priming context",
         lambda t: "You are an expert AI assistant with deep knowledge in this domain.\n\n" + t,
         "Role priming activates domain-specific knowledge patterns and improves answer depth."),
        ("Break into step-by-step instructions",
         lambda t: "Please complete the following task step by step:\n\n" + t + "\n\nThink through each step carefully before responding.",
         "Chain-of-thought framing reduces errors and improves reasoning for complex tasks."),
        ("Add output quality checklist",
         lambda t: t + "\n\nBefore finalizing your response, verify:\n- Accuracy: Are all facts correct?\n- Completeness: Have all parts been addressed?\n- Clarity: Is the response easy to understand?",
         "Self-verification prompts reduce hallucination and improve factual accuracy."),
    ],
    "tone": [
        ("Establish professional register",
         lambda t: re.sub(r"\b(hey|hi there|yo|gonna|wanna|kinda|dunno)\b", "", t, flags=re.I).strip(),
         "Professional language signals the expected register and elevates response quality."),
        ("Add context framing",
         lambda t: "Context: I need your expert assistance with the following task.\n\n" + t,
         "Context framing helps the model understand the gravity and purpose of the request."),
        ("Include response quality directive",
         lambda t: t + "\n\nPlease ensure your response is:\n- Factually accurate\n- Well-organized\n- Free from assumptions or speculation",
         "Quality directives reduce hallucination and set clear expectations for the response."),
    ],
}

REASONING = {
    "clarity": ["Clear prompts yield clear responses — specificity is the #1 predictor of output quality.",
                "Removing ambiguity from prompts reduces token waste and improves response precision by up to 40%."],
    "specificity": ["Concrete details give the model fewer variables to guess, producing more reliable outputs.",
                    "Specificity metrics show that detailed prompts generate responses with 35% higher accuracy scores."],
    "structure": ["Well-structured prompts improve chain-of-thought reasoning in language models.",
                  "Role-primed and structured prompts reduce hallucination rates by approximately 25%."],
    "tone": ["Tone alignment ensures the model calibrates its response register to match your use case.",
             "Professional framing reduces casual errors and improves citation quality in responses."],
}

def generate_suggestions(text: str, types: Optional[List[str]] = None) -> List[Dict]:
    if types is None: types = list(TEMPLATES.keys())
    overall, clarity, spec = compute_quality_score(text)
    results = []
    for stype in types:
        tmpl = TEMPLATES.get(stype, [])
        if not tmpl: continue
        label, transform, reasoning = random.choice(tmpl)
        try: suggested = transform(text)
        except: suggested = text
        gap = {"clarity": 1-clarity, "specificity": 1-spec}.get(stype, 1-overall)
        conf = round(max(0.45, min(0.97, 0.5 + gap*0.4 + random.uniform(-0.04, 0.04))), 3)
        results.append({
            "suggestion_type": stype,
            "original_text": text,
            "suggested_text": suggested,
            "reasoning": f"**{label}**: {random.choice(REASONING.get(stype, [reasoning]))}",
            "confidence_score": conf,
        })
    return results

def diff_summary(old: str, new: str) -> Dict:
    sim = tfidf_similarity(old, new)
    chg = round((1 - sim) * 100, 1)
    delta = len(tokenize(new)) - len(tokenize(old))
    label = "Minor edit" if chg < 10 else "Moderate revision" if chg < 40 else "Major rewrite"
    return {"similarity": sim, "change_percentage": chg, "change_label": label, "token_delta": delta}
