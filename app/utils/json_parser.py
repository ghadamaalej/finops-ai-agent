import json
import re


def parse_json_array(text: str):

    if not text:
        raise ValueError("LLM returned an empty response")

    text = text.strip()

    # --------------------------------------------------
    # Remove markdown code fences
    # --------------------------------------------------

    if text.startswith("```"):
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"\s*```$",
            "",
            text
        )

        text = text.strip()

    # --------------------------------------------------
    # Find the JSON array
    # --------------------------------------------------

    start = text.find("[")

    if start == -1:
        raise ValueError(
            "LLM response does not contain a JSON array"
        )

    # Find matching closing bracket
    depth = 0
    in_string = False
    escape = False

    end = None

    for i in range(start, len(text)):

        char = text[i]

        if escape:
            escape = False
            continue

        if char == "\\":
            escape = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "[":
            depth += 1

        elif char == "]":
            depth -= 1

            if depth == 0:
                end = i
                break

    if end is None:

        raise ValueError(
            "LLM response contains an incomplete JSON array"
        )

    json_text = text[start:end + 1]

    # --------------------------------------------------
    # Parse JSON
    # --------------------------------------------------

    try:

        data = json.loads(
            json_text
        )

    except json.JSONDecodeError as exc:

        print(
            "\n===== INVALID JSON FROM LLM ====="
        )

        print(
            json_text
        )

        print(
            "===== JSON ERROR ====="
        )

        print(
            f"Line: {exc.lineno}"
        )

        print(
            f"Column: {exc.colno}"
        )

        print(
            f"Message: {exc.msg}"
        )

        print(
            "==============================\n"
        )

        raise

    if not isinstance(data, list):

        raise ValueError(
            "LLM response must be a JSON array"
        )

    return data