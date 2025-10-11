from services.model_manager import ollama_manager

def generate_global(text_chunk):
    prompt = f"""
You are creating a cinematic background music prompt for an AI music generator.
Step 1: Write a **one-line summary** of the emotional tone and setting of the full text. Focus on the mood, relationships, or themes — not plot details.
Step 2: Write **one sentence** describing ideal background music that matches this story. Use emotional and musical terms, not composer names or musical eras.
Do NOT summarize the story. Do NOT mention any composers. Only describe the feeling and sound of the music.

Format:
Scene Summary: [One emotional or atmospheric sentence]
Global Music Theme: [One sentence describing the ideal music: mood, genre, instruments, tempo, and evolution]

Example:
Scene Summary: A tender and quiet reflection on lost love and the warmth of shared memories.  
Global Music Theme: A slow, emotional piano-driven score with soft ambient textures and subtle string swells that evolve gently over time.

Text:
{text_chunk}

Now write only the two lines: scene summary and global music theme.
"""
    response = ollama_manager.chat([{"role": "user", "content": prompt}])
    return response["message"]["content"]

def generate_regional(text_chunk):
    prompt = f"""
You are generating a **compact music prompt** for a text-to-music AI based on the scene below.

Your goal: extract only key musical elements — keep it concise, direct, and focused on the sound.

Respond using this minimal format:
Scene: [5–10 words]
Emotions: [1–3 keywords]
Mood & Style: [short musical genre + vibe]
Instruments: [2–4 key instruments/sounds]
Tempo: [BPM or brief description]
Progression: [how it evolves, in <10 words]

Example:
Scene: Detective walks through abandoned asylum  
Emotions: Eerie, tense  
Mood & Style: Dark ambient  
Instruments: Low drones, eerie violin, reverb piano  
Tempo: 50–60 BPM, slow  
Progression: Builds tension, ends in sharp swell

Text:
{text_chunk}

Only return the prompt in the compact format shown above. Avoid full sentences or extra text.
"""
    response = ollama_manager.chat([{"role": "user", "content": prompt}])
    return response["message"]["content"]

def compose_musicgen_prompt(global_theme_output: str, regional_prompt_output: str) -> str:
    final_prompt = f"""{global_theme_output}

Maintain the overall mood, style, and instrumentation described above while adapting to the local scene below.

{regional_prompt_output}

Generate music that reflects the scene and emotions, while remaining stylistically consistent with the global theme.
"""
    return final_prompt

