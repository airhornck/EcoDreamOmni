"""Account health scoring engine."""



def calculate_health_score(
    posts_today: int,
    posts_week: int,
    engagement_rate: float,
    violation_count: int,
    last_login_days: int,
) -> float:
    """Calculate account health score (0-100).

    Factors:
    - Posting frequency (too low = dormant, too high = spam risk)
    - Engagement rate
    - Violation history
    - Login recency
    """
    score = 100.0

    # Posting frequency penalty
    if posts_today > 5:
        score -= (posts_today - 5) * 5  # -5 per post over 5/day
    if posts_week > 30:
        score -= (posts_week - 30) * 1  # -1 per post over 30/week
    if posts_week < 3:
        score -= 10  # dormant penalty

    # Engagement bonus/penalty
    if engagement_rate < 0.01:
        score -= 15
    elif engagement_rate < 0.03:
        score -= 5
    elif engagement_rate > 0.08:
        score += 5

    # Violation penalty (heavy)
    score -= violation_count * 20

    # Login recency
    if last_login_days > 7:
        score -= 10
    if last_login_days > 30:
        score -= 20

    # Clamp to 0-100
    return max(0.0, min(100.0, score))
