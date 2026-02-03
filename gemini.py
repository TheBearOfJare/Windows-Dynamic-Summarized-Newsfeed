from google import genai
from google.genai import types
import os
import json

# Read the config json
with open("config.json", "r") as f:
    user_config = json.load(f)

# support using the environment variable gemini_key
try:
    client = genai.Client(api_key=user_config["gemini_key"])
except Exception:
    print(
        "No key in config, trying environment variable. If this fails the program will exit rather ungracefully."
    )
    client = genai.Client(api_key=os.environ["gemini_key"])

grounding_tool = types.Tool(google_search=types.GoogleSearch())

config = types.GenerateContentConfig(
    tools=[grounding_tool], maxOutputTokens=user_config["response_length"]
)


def updateFeed(base_path="."):
    try:
        interests_path = os.path.join(base_path, "interests.txt")
        if os.path.exists(interests_path):
            with open(interests_path, "r") as f:
                interests = [line.strip() for line in f.readlines() if line.strip()]
        else:
            interests = ["World Events"]

        prompt = "Find and summarize the latest news in the following categories: " + ", ".join(interests) + " Try to find seperate sources for each topic. This is a markdown document, so use markdown formatting for clarity and organization. Give each topic a heading above its summary. Start your response with a short 2-3 sentence summary of the most important news across all catagories."

        response = client.models.generate_content(
            model=user_config["model"],
            contents=prompt,
            config=config,
        )
        return add_citations(response)
    except Exception as e:
        # Re-raise so main.pyw can handle it or log it
        raise e


def add_citations(response):
    text = response.text
    supports = response.candidates[0].grounding_metadata.grounding_supports
    chunks = response.candidates[0].grounding_metadata.grounding_chunks

    # Sort supports by end_index in descending order to avoid shifting issues when inserting.
    sorted_supports = sorted(supports, key=lambda s: s.segment.end_index, reverse=True)

    for support in sorted_supports:
        end_index = support.segment.end_index
        if support.grounding_chunk_indices:
            # Create citation string like [1](link1)[2](link2)
            citation_links = []
            for i in support.grounding_chunk_indices:
                if i < len(chunks):
                    uri = chunks[i].web.uri
                    citation_links.append(f"<a href='{uri}'>{i + 1}</a>")

            citation_string = "<sub>" + ", ".join(citation_links) + "</sub>"
            text = text[:end_index] + citation_string + text[end_index:]

    return text
