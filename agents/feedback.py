def feedback_section(state, target: str) -> str:
    """
    Reviewer feedback for a revision round, formatted for a prompt.
    Empty on the first attempt.
    """

    if not state.review or state.review.approved:
        return ""

    issues = [
        f"- [{issue.severity}] {issue.description}"
        for issue in state.review.issues
        if issue.target_agent == target
    ]

    lines = [
        "",
        "This is a revision. The reviewer rejected the previous version.",
        f"Reviewer summary: {state.review.feedback}",
    ]

    if issues:
        lines.append("Issues you must fix:")
        lines.extend(issues)

    return "\n".join(lines)
