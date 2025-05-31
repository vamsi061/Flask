import requests
import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://api.a4f.co/v1/chat/completions"
MODEL = "provider-4/gpt-4.1"

template = (
    "You are tasked with extracting specific information from the following text content:\n\n"
    "{dom_content}\n\n"
    "Please follow these instructions carefully:\n"
    "1. Extract only the information that directly matches this description: {parse_description}\n"
    "2. Do not include any extra text, comments, or explanations.\n"
    "3. Return an empty string ('') if no relevant information is found.\n"
    "4. Only output the requested data—no greetings or context."
)

def parse_with_ollama(dom_chunks, parse_description, max_chunks=5):
    """Parses a list of DOM content chunks using the OpenRouter LLM API in batches."""
    if not dom_chunks or not isinstance(dom_chunks, list):
        print("⚠️ Warning: dom_chunks is empty or not a list.")
        return ""

    # Limit the total number of chunks to process
    dom_chunks = dom_chunks[:10]  # Process at most 10 chunks
    
    parsed_results = []
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    total_batches = (len(dom_chunks) + max_chunks - 1) // max_chunks

    for i in range(0, len(dom_chunks), max_chunks):
        batch_index = i // max_chunks + 1
        batch_chunks = dom_chunks[i:i + max_chunks]

        # Defensive check: ensure batch_chunks are strings and not empty
        batch_chunks = [chunk for chunk in batch_chunks if isinstance(chunk, str) and chunk.strip()]
        if not batch_chunks:
            print(f"⚠️ Batch {batch_index} has no valid chunks, skipping.")
            continue

        # Combine chunks but limit the total size
        combined_chunk = "\n\n".join(batch_chunks)
        # Limit to ~10,000 characters to avoid excessive token usage
        if len(combined_chunk) > 10000:
            combined_chunk = combined_chunk[:10000]
            
        prompt_text = template.format(dom_content=combined_chunk, parse_description=parse_description)

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are an expert information extractor."},
                {"role": "user", "content": prompt_text}
            ],
            "temperature": 0.2,
        }

        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                result = response.json()
                # Defensive parsing of JSON structure
                message = ""
                try:
                    message = result["choices"][0]["message"]["content"].strip()
                except (KeyError, IndexError, AttributeError):
                    print(f"⚠️ Unexpected response format in batch {batch_index}: {result}")
                    message = ""
                parsed_results.append(message)
                print(f"✅ Parsed batch {batch_index} of {total_batches}")
            else:
                print(f"❌ Error on batch {batch_index}: {response.status_code} - {response.text}")
                parsed_results.append("")

        except requests.exceptions.RequestException as e:
            print(f"🚨 Request exception in batch {batch_index}: {e}")
            parsed_results.append("")

    # Join all batch results and ensure a string output
    combined_result = "\n".join(parsed_results)
    return combined_result if isinstance(combined_result, str) else ""
