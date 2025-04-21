import nltk
import torch
import ollama
from pprint import pprint
from transformers import AutoTokenizer, AutoModelForSequenceClassification


nltk.download('punkt')


EMOTION_MODEL_NAME = "searle-j/kote_for_easygoing_people"
tokenizer = AutoTokenizer.from_pretrained(EMOTION_MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(EMOTION_MODEL_NAME)
model.eval()
model.to("cpu")  # GPU 사용 가능하면 "cuda"로 변경 가능

# 모델의 label 순서는 config.id2label을 참조. 여기서는 예시로 리스트만 정의:
LABELS = [
    '불평/불만','환영/호의','감동/감탄','지긋지긋','고마움','슬픔','화남/분노','존경',
    '기대감','우쭐댐/무시함','안타까움/실망','비장함','의심/불신','뿌듯함','편안/쾌적',
    '신기함/관심','아껴주는','부끄러움','공포/무서움','절망','한심함','역겨움/징그러움',
    '짜증','어이없음','없음','패배/자기혐오','귀찮음','힘듦/지침','즐거움/신남','깨달음',
    '죄책감','증오/혐오','흐뭇함(귀여움/예쁨)','당황/난처','경악','부담/안_내킴',
    '서러움','재미없음','불쌍함/연민','놀람','행복','불안/걱정','기쁨','안심/신뢰'
]


def get_emotion_vector(text: str) -> torch.Tensor:
    """
    주어진 문장(text)에 대해, searle-j/kote_for_easygoing_people 모델을 사용해
    각 감정 라벨별 점수를 시그모이드(sigmoid)로 변환하여 얻은 벡터를 반환.
    NOTE: 이 모델은 multi-label 구조이므로 softmax가 아닌 sigmoid가 적합합니다.
    (각 감정별 확률이 독립적으로 계산되며, 합이 1을 초과할 수 있음)
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)            # outputs.logits : shape (batch_size, num_labels)
    
    # 다중 라벨 예측인 경우, 시그모이드(sigmoid)를 적용하여 각 감정 라벨의 확률(0~1)을 구함
    probs = torch.sigmoid(outputs.logits)[0] # shape: (num_labels,)
    
    # CPU 텐서로 변환 후 반환
    return probs.cpu()

def cosine_similarity(vec1: torch.Tensor, vec2: torch.Tensor) -> float:
    """
    두 1D 텐서(vec1, vec2)의 코사인 유사도를 계산하여 0.0 ~ 1.0 사이의 값을 반환.
    vec1, vec2는 동일 차원이어야 하며, 모두 양수(감정 확률)여도 -1~+1이 아니라 0~1 범위 내에서 유사도가 계산됨.
    """
    dot = torch.dot(vec1, vec2).item()
    norm1 = torch.norm(vec1).item()
    norm2 = torch.norm(vec2).item()
    
    # 두 벡터 중 하나라도 0벡터(길이=0)이면 유사도 0으로 처리
    if norm1 * norm2 == 0:
        return 0.0
    
    return dot / (norm1 * norm2)


def hybrid_chunk_text_by_emotion_fulltext(
    text : str,
    similarity_threshold=0.3
):
    # min_words, max_words 파라미터가 필요 없다면 빼도 됨
    # 일단 여기서는 예시로 min_words, max_words를 None으로 두거나, 
    # 감정 기반으로만 분할하게 할 수도 있습니다.

    # with open(file_path, "r", encoding="utf-8") as f:
    #     full_text = f.read()
    
    sentences = nltk.sent_tokenize(text)
    sentence_info_list = []
    for s in sentences:
        s_stripped = s.strip()
        if not s_stripped:
            continue
        # 원한다면 토큰 수 계산, 감정 분석
        e_vec = get_emotion_vector(s_stripped)
        sentence_info_list.append((s_stripped, e_vec))

    final_chunks = []
    current_chunk = []
    prev_vec = None

    for (sent_text, e_vec) in sentence_info_list:
        if not current_chunk:
            current_chunk = [(sent_text, e_vec)]
            prev_vec = e_vec
            continue

        sim = cosine_similarity(prev_vec, e_vec)
        if sim < similarity_threshold:
            # 감정 차이가 크면 -> 새 청크
            chunk_text = " ".join(x[0] for x in current_chunk)
            final_chunks.append(chunk_text)
            current_chunk = [(sent_text, e_vec)]
        else:
            # 비슷하면 계속 합침
            current_chunk.append((sent_text, e_vec))

        prev_vec = e_vec

    # 마지막 청크
    if current_chunk:
        chunk_text = " ".join(x[0] for x in current_chunk)
        final_chunks.append(chunk_text)

    # List형태 청크 반환환
    return final_chunks