"""
Математическая модель классификации сложности задач
==================================================

Формула определяет классификацию задач по сложности с учётом:
1. Семантики задачи (через Transformer-эмбеддинги)
2. Метаданных и истории
3. Минимизации ошибки классификации
4. Возможности принятия решений с uncertainty estimation
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import IntEnum


class ComplexityLevel(IntEnum):
    """Уровни сложности задач (K=5)"""
    TRIVIAL = 1  # Тривиальная
    EASY = 2     # Простая
    MEDIUM = 3   # Средняя
    HARD = 4     # Сложная
    COMPLEX = 5 # Комплексная


@dataclass
class TaskFeatures:
    """Входные данные задачи"""
    title: str
    description: str
    comments: List[str]
    labels: List[str]
    created_at_timestamp: float
    repo_stars: int
    repo_language: str
    similar_issues_avg_difficulty: Optional[float] = None
    author_past_performance: Optional[float] = None


# =============================================================================
# ЧАСТЬ 1: СЕМАНТИЧЕСКОЕ КОДИРОВАНИЕ
# =============================================================================

def encode_text(title: str, description: str, comments: List[str], 
                encoder_model) -> np.ndarray:
    """
    Семантическое кодирование текста задачи
    
    e_text = α · BERT(title) + (1-α) · AttentionPool(BERT(description + comments))
    
    Args:
        title: Заголовок задачи
        description: Описание задачи
        comments: Список комментариев
        encoder_model: Предобученная BERT-модель
    
    Returns:
        e_text: Семантический эмбеддинг размерности d_text
    """
    # Получаем эмбеддинги через Transformer
    e_title = encoder_model.encode(title)  # shape: (d_model,)
    full_text = description + " ".join(comments)
    e_desc = encoder_model.encode(full_text)  # shape: (d_model,)
    
    # Attention-weighted pooling для комментариев (упрощённо)
    alpha = 0.4  # Обучаемый параметр α ∈ [0, 1]
    
    e_text = alpha * e_title + (1 - alpha) * e_desc
    return e_text


def encode_metadata(labels: List[str], timestamp: float, 
                   encoder) -> np.ndarray:
    """
    Кодирование метаданных задачи
    
    e_meta = MLP_meta([labels_onehot; timestamp_norm])
    
    Args:
        labels: Список меток задачи
        timestamp: Временная метка создания
        encoder: Label encoder для меток
    
    Returns:
        e_meta: Вектор метаданных размерности d_meta
    """
    # One-hot encoding меток + нормализованный timestamp
    labels_encoded = encoder.labels_to_onehot(labels)
    timestamp_norm = (timestamp - T_MIN) / (T_MAX - T_MIN)  # Нормализация
    
    x_meta = np.concatenate([labels_encoded, [timestamp_norm]])
    
    # MLP проекция (однослойная для простоты)
    e_meta = np.tanh(W_meta @ x_meta + b_meta)
    return e_meta


def encode_repo_features(stars: int, language: str, 
                         lang_encoder) -> np.ndarray:
    """
    Кодирование признаков репозитория
    
    e_repo = MLP_repo([log(stars+1); lang_onehot])
    """
    stars_log = np.log(stars + 1) / np.log(1e6)  # Логарифмическая нормализация
    lang_encoded = lang_encoder.onehot(language)
    
    x_repo = np.concatenate([[stars_log], lang_encoded])
    e_repo = np.tanh(W_repo @ x_repo + b_repo)
    return e_repo


def compute_historical_features(similar_avg: Optional[float] = None,
                                author_perf: Optional[float] = None) -> np.ndarray:
    """
    Исторические признаки
    
    e_hist = [σ(similar_avg); σ(author_performance)]
    
    где σ - сигмоидальное преобразование для стабильности
    """
    similar_norm = 1 / (1 + np.exp(-similar_avg)) if similar_avg else 0.5
    author_norm = 1 / (1 + np.exp(-author_perf)) if author_perf else 0.5
    
    return np.array([similar_norm, author_norm])


# =============================================================================
# ЧАСТЬ 2: FUSION LAYER (Объединение признаков)
# =============================================================================

def fusion_gate(e_text: np.ndarray, e_meta: np.ndarray, 
                e_repo: np.ndarray, e_hist: np.ndarray) -> np.ndarray:
    """
    Gated Fusion Layer - адаптивное объединение признаков
    
    e_fused = Gate · e_text + (1 - Gate) · e_context
    
    где:
        Gate = σ(W_gate · [e_text; e_context])
        e_context = [e_meta; e_repo; e_hist]
    
    Args:
        e_text: Семантические признаки (d_text,)
        e_meta: Метаданные (d_meta,)
        e_repo: Признаки репозитория (d_repo,)
        e_hist: Исторические признаки (d_hist,)
    
    Returns:
        e_fused: Объединённый вектор признаков
    """
    e_context = np.concatenate([e_meta, e_repo, e_hist])
    
    # Gating mechanism
    gate_input = np.concatenate([e_text, e_context])
    gate = 1 / (1 + np.exp(W_gate @ gate_input + b_gate))  # Сигмоида
    
    e_fused = gate * e_text + (1 - gate) * e_context
    return e_fused


# =============================================================================
# ЧАСТЬ 3: ORDINAL CLASSIFICATION (Классификация с учётом порядка)
# =============================================================================

def compute_thresholds(e_fused: np.ndarray) -> np.ndarray:
    """
    Вычисление пороговых значений для ordinal classification
    
    φ_k = w_k^T · e_fused + b_k,   k = 1, ..., K-1
    
    где K = 5 уровней сложности
    
    Args:
        e_fused: Объединённый вектор признаков
    
    Returns:
        thresholds: Массив порогов φ_1, φ_2, φ_3, φ_4
    """
    thresholds = np.array([
        W_thresh[k] @ e_fused + b_thresh[k] 
        for k in range(N_CLASSES - 1)
    ])
    return thresholds


def ordinal_to_class(thresholds: np.ndarray) -> int:
    """
    Преобразование порогов в класс сложности
    
    ĉ = 1 + Σ_{k=1}^{K-1} I(φ_k > 0)
    
    где I - индикаторная функция
    
    Args:
        thresholds: Вычисленные пороги φ_1, ..., φ_{K-1}
    
    Returns:
        predicted_class: Класс сложности 1..K
    """
    predicted_class = 1
    for k, phi in enumerate(thresholds):
        if phi > 0:
            predicted_class = k + 2
    return min(predicted_class, N_CLASSES)


def class_to_probabilities(thresholds: np.ndarray) -> np.ndarray:
    """
    Вероятности классов через сигмоиду разностей порогов
    
    P(c=j | e) = σ(φ_j - φ_{j-1})
    
    Args:
        thresholds: Пороги φ_1, ..., φ_{K-1}
    
    Returns:
        probs: Распределение вероятностей [P(1), P(2), ..., P(K)]
    """
    # Добавляем фиктивные пороги на концах
    extended = np.concatenate([[-np.inf], thresholds, [+np.inf]])
    
    probs = []
    for j in range(N_CLASSES):
        # P(c=j) = σ(φ_j - φ_{j-1})
        diff = extended[j+1] - extended[j]
        probs.append(1 / (1 + np.exp(-diff)))
    
    # Нормализация
    probs = np.array(probs)
    probs = probs / probs.sum()
    return probs


# =============================================================================
# ЧАСТЬ 4: ПОЛНАЯ ФОРМУЛА КЛАССИФИКАЦИИ
# =============================================================================

def predict_complexity(task: TaskFeatures, encoder_model, 
                       label_encoder, lang_encoder) -> Tuple[int, np.ndarray, float]:
    """
    Полная формула классификации сложности задачи
    
    ĉ = argmax_j P(c=j | x)
    
    где:
        x = [e_text; e_meta; e_repo; e_hist]
        P(c=j | x) = softmax(W_out · e_fused + b_out)_j
    
    Args:
        task: Признаки задачи
        encoder_model: BERT/Transformer encoder
        label_encoder: Encoder для меток
        lang_encoder: Encoder для языков
    
    Returns:
        predicted_class: Предсказанный класс (1-5)
        probabilities: Распределение вероятностей
        entropy: Энтропия (неопределённость)
    """
    # Шаг 1: Кодирование признаков
    e_text = encode_text(task.title, task.description, task.comments, encoder_model)
    e_meta = encode_metadata(task.labels, task.created_at_timestamp, label_encoder)
    e_repo = encode_repo_features(task.repo_stars, task.repo_language, lang_encoder)
    e_hist = compute_historical_features(
        task.similar_issues_avg_difficulty,
        task.author_past_performance
    )
    
    # Шаг 2: Fusion
    e_fused = fusion_gate(e_text, e_meta, e_repo, e_hist)
    
    # Шаг 3: Вычисление порогов
    thresholds = compute_thresholds(e_fused)
    
    # Шаг 4: Вероятности и предсказание
    probabilities = class_to_probabilities(thresholds)
    predicted_class = ordinal_to_class(thresholds)
    
    # Шаг 5: Вычисление энтропии (неопределённость)
    entropy = -np.sum(probabilities * np.log(probabilities + 1e-10))
    
    return predicted_class, probabilities, entropy


# =============================================================================
# ЧАСТЬ 5: ФУНКЦИЯ ПОТЕРЬ
# =============================================================================

def ordinal_cross_entropy_loss(probabilities: np.ndarray, 
                               true_class: int) -> float:
    """
    Ordinal Cross-Entropy Loss
    
    L_ordinal = -Σ_j y_j · log(P(c=j))
    
    Args:
        probabilities: Предсказанные вероятности
        true_class: Истинный класс (1-indexed)
    
    Returns:
        loss: Значение функции потерь
    """
    true_class_idx = true_class - 1  # Convert to 0-indexed
    loss = -np.log(probabilities[true_class_idx] + 1e-10)
    return loss


def consistency_loss(e_texts: np.ndarray, classes: np.ndarray, 
                     margin: float = 0.1) -> float:
    """
    Consistency Loss - штраф за нарушение семантической согласованности
    
    L_consistency = max(0, c_j - c_i - ε · ||e_i - e_j||)
    
    Если семантически похожие задачи имеют разную сложность - штраф!
    
    Args:
        e_texts: Матрица текстовых эмбеддингов (n_samples, d)
        classes: Массив истинных классов
        margin: Минимальный зазор
    
    Returns:
        loss: Значение регуляризатора
    """
    n = len(classes)
    loss = 0.0
    count = 0
    
    for i in range(n):
        for j in range(i+1, n):
            # Если задача j сложнее задачи i
            if classes[j] > classes[i]:
                semantic_dist = np.linalg.norm(e_texts[i] - e_texts[j])
                # Штраф, если расстояние меньше разницы в классах
                violation = classes[j] - classes[i] - margin * semantic_dist
                if violation > 0:
                    loss += violation
                    count += 1
    
    return loss / max(count, 1)


def ordinality_loss(thresholds: np.ndarray, margin: float = 0.5) -> float:
    """
    Ordinality Loss - штраф за нарушение порядка порогов
    
    L_ordinality = Σ_k max(0, φ_k - φ_{k+1} + δ)
    
    Обеспечивает φ_1 < φ_2 < ... < φ_{K-1}
    
    Args:
        thresholds: Значения порогов
        margin: Требуемый зазор между порогами
    
    Returns:
        loss: Значение регуляризатора
    """
    loss = 0.0
    for k in range(len(thresholds) - 1):
        violation = thresholds[k] - thresholds[k+1] + margin
        if violation > 0:
            loss += violation
    return loss


def total_loss(probabilities: np.ndarray, true_class: int,
               e_texts: np.ndarray, classes: np.ndarray,
               thresholds: np.ndarray,
               beta: float = 0.1) -> float:
    """
    Полная функция потерь
    
    L_total = L_ordinal + β · (L_consistency + L_ordinality)
    
    Args:
        probabilities: Предсказанные вероятности
        true_class: Истинный класс
        e_texts: Текстовые эмбеддинги батча
        classes: Истинные классы батча
        thresholds: Пороги для ordinality loss
        beta: Коэффициент регуляризации
    
    Returns:
        loss: Полное значение функции потерь
    """
    L_ordinal = ordinal_cross_entropy_loss(probabilities, true_class)
    L_consistency = consistency_loss(e_texts, classes)
    L_ordinality = ordinality_loss(thresholds)
    
    return L_ordinal + beta * (L_consistency + L_ordinality)


# =============================================================================
# ЧАСТЬ 6: ФУНКЦИЯ ПРИНЯТИЯ РЕШЕНИЙ
# =============================================================================

def make_decision(predicted_class: int, probabilities: np.ndarray, 
                  entropy: float) -> dict:
    """
    Функция принятия решений на основе неопределённости
    
    Decision(e) = 
        Auto-Assign(ĉ)           если H < τ_auto
        Human-Review(ĉ, conf)    если τ_auto ≤ H < τ_review
        Escalate(ĉ)               если H ≥ τ_review
    
    Args:
        predicted_class: Предсказанный класс
        probabilities: Распределение вероятностей  
        entropy: Энтропия (мера неопределённости)
    
    Returns:
        decision: Словарь с решением и рекомендациями
    """
    # Пороги для принятия решений (настраиваемые)
    TAU_AUTO = 0.5    # Автоматическое назначение
    TAU_REVIEW = 1.0  # Требуется проверка
    
    max_prob = np.max(probabilities)
    
    if entropy < TAU_AUTO:
        return {
            "action": "AUTO_ASSIGN",
            "class": predicted_class,
            "confidence": max_prob,
            "entropy": entropy,
            "message": f"Высокая уверенность ({max_prob:.1%}). Автоматическое назначение."
        }
    elif entropy < TAU_REVIEW:
        return {
            "action": "HUMAN_REVIEW",
            "class": predicted_class,
            "confidence": max_prob,
            "entropy": entropy,
            "alternatives": get_top_alternatives(probabilities, top_k=2),
            "message": f"Средняя уверенность ({max_prob:.1%}). Рекомендуется проверка."
        }
    else:
        return {
            "action": "ESCALATE",
            "class": predicted_class,
            "confidence": max_prob,
            "entropy": entropy,
            "message": "Низкая уверенность. Требуется эскалация к эксперту."
        }


def get_top_alternatives(probabilities: np.ndarray, 
                         top_k: int = 2) -> List[Tuple[int, float]]:
    """Получить альтернативные классы с их вероятностями"""
    indices = np.argsort(probabilities)[::-1][:top_k]
    return [(int(idx + 1), float(prob)) for idx, prob in zip(indices, probabilities[indices])]


# =============================================================================
# ИТОГОВАЯ ФОРМУЛА
# =============================================================================

"""
================================================================================
                    ИТОГОВАЯ МАТЕМАТИЧЕСКАЯ ФОРМУЛА
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   PREDICTION FORMULA:                                                        │
│   ───────────────────                                                        │
│                                                                             │
│                           ┌─────────────────────────────────────┐            │
│                           │  e_text = α·E(title) + (1-α)·E(desc)│            │
│                           └─────────────────────────────────────┘            │
│                                        │                                      │
│                                        ▼                                      │
│                           ┌─────────────────────────────────────┐            │
│                           │  e_meta = MLP(labels, timestamp)   │            │
│                           │  e_repo = MLP(stars, language)      │            │
│                           │  e_hist = [σ(similar), σ(perf)]     │            │
│                           └─────────────────────────────────────┘            │
│                                        │                                      │
│                                        ▼                                      │
│                           ┌─────────────────────────────────────┐            │
│                           │  gate = σ(W·[e_text; e_context])   │            │
│                           │  e_fused = gate·e_text +            │            │
│                           │           (1-gate)·e_context        │            │
│                           └─────────────────────────────────────┘            │
│                                        │                                      │
│                                        ▼                                      │
│                           ┌─────────────────────────────────────┐            │
│                           │  φ_k = w_k · e_fused + b_k          │            │
│                           │  (для k = 1, 2, 3, 4)               │            │
│                           └─────────────────────────────────────┘            │
│                                        │                                      │
│                                        ▼                                      │
│                           ┌─────────────────────────────────────┐            │
│                           │  P(c=j) = σ(φ_j - φ_{j-1})         │            │
│                           │  ĉ = argmax_j P(c=j)                │            │
│                           └─────────────────────────────────────┘            │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   LOSS FUNCTION:                                                            │
│   ──────────────                                                             │
│                                                                             │
│   L(θ) = -Σ_j y_j · log(P_θ(c=j|x))                                         │
│          + β · [ max(0, c_j - c_i - ε·||e_i-e_j||)                          │
│                   + Σ_k max(0, φ_k - φ_{k+1} + δ) ]                         │
│                                                                             │
│   где:                                                                       │
│     - θ = {W_*, b_*, α, ε, δ} — все обучаемые параметры                      │
│     - y_j — one-hot кодирование истинного класса                              │
│     - β — коэффициент семантической регуляризации                             │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   DECISION FUNCTION:                                                         │
│   ──────────────────                                                         │
│                                                                             │
│   H = -Σ_j P(c=j) · log(P(c=j))  [Entropy]                                  │
│                                                                             │
│        ┌  AUTO_ASSIGN(ĉ)         если H < 0.5                               │
│   D =  │  HUMAN_REVIEW(ĉ, alt)    если 0.5 ≤ H < 1.0                        │
│        └  ESCALATE(ĉ)             если H ≥ 1.0                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
"""

# =============================================================================
# ПРИМЕР ИСПОЛЬЗОВАНИЯ
# =============================================================================

if __name__ == "__main__":
    """
    Пример использования модели для классификации задачи
    
    Задача: "Fix memory leak in data processing pipeline"
    Labels: [bug, performance]
    Stars: 5000
    Language: Python
    """
    
    print("=" * 70)
    print("Классификация сложности задачи")
    print("=" * 70)
    
    # Пример задачи
    task = TaskFeatures(
        title="Fix memory leak in data processing pipeline",
        description="The application experiences gradual memory increase...",
        comments=["I can reproduce this on v2.1", "Check PR #123"],
        labels=["bug", "performance", "high-priority"],
        created_at_timestamp=1700000000.0,
        repo_stars=5000,
        repo_language="Python",
        similar_issues_avg_difficulty=3.5,
        author_past_performance=0.7
    )
    
    print(f"\n📋 Задача: {task.title}")
    print(f"   Метки: {task.labels}")
    print(f"   Репозиторий: {task.repo_language}, ⭐ {task.repo_stars}")
    
    # Примечание: В реальном использовании здесь была бы инициализация
    # настоящих моделей (BERT, энкодеры меток и т.д.)
    
    print("\n⚠️  Примечание: Для работы требуется инициализация моделей:")
    print("   - Transformer encoder (BERT/RoBERTa)")
    print("   - Label encoder")
    print("   - Language encoder")
    print("   - Обучение модели на размеченных данных")
    
    print("\n" + "=" * 70)
    print("МАТЕМАТИЧЕСКАЯ ФОРМУЛА (компактная запись)")
    print("=" * 70)
    
    formula = """
    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                 │
    │   ĉ(x) = argmax_{j∈{1..5}}  σ(φ_j - φ_{j-1})                   │
    │                                                                 │
    │   где:                                                         │
    │     φ_k = w_k^T · (gate ⊙ e_text + (1-gate) ⊙ e_context) + b_k │
    │     gate = σ(W_gate^T · [e_text; e_context])                  │
    │     e_text = α·BERT(title) + (1-α)·BERT(description)          │
    │     e_context = [MLP(labels); MLP(repo); historical]           │
    │                                                                 │
    │   Решение:                                                     │
    │     H < 0.5  → AUTO_ASSIGN(ĉ)                                 │
    │     H < 1.0  → HUMAN_REVIEW(ĉ)                                │
    │     H ≥ 1.0  → ESCALATE(ĉ)                                    │
    │                                                                 │
    │   Loss:                                                        │
    │     L = -log P(c=c*|x) + β·[consistency + ordinality]         │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
    """
    print(formula)
