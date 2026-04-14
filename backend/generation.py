import os
import json
import asyncio
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
openai_key = os.environ.get("OPENAI_API_KEY")
llm_provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()

anthropic_client = AsyncAnthropic(api_key=anthropic_key) if anthropic_key else None
openai_client = AsyncOpenAI(api_key=openai_key) if openai_key else None

def format_context(chunks: list) -> str:
    ctx_parts = []
    for i, c in enumerate(chunks):
        ctx_parts.append(f"--- Document chunk {i+1} ---\nFilename: {c['filename']}\nPage: {c['page']}\nText: {c['text']}")
    return "\n\n".join(ctx_parts)

def build_citations(chunks: list) -> str:
    citations = []
    for c in chunks:
        citations.append(f"[Doc: {c['filename']}, Page: {c['page']}, Chunk: {c['chunk_index']}]")
    return " | ".join(citations)

async def generate_response_sse(query: str, chunks: list):
    context = format_context(chunks)
    citations_str = build_citations(chunks)
    
    system_prompt = "You are DocuMind, an AI assistant who answers questions strictly based on the provided document excerpts. If the answer is not in the excerpts, say so."
    user_prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer concisely and format your final result well. Always rely on the context provided."
    
    yield f"data: {json.dumps({'citations': citations_str})}\n\n"
    
    if llm_provider == "anthropic" and anthropic_client:
        async with anthropic_client.messages.stream(
            max_tokens=1024,
            model="claude-3-5-haiku-20241022",
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        ) as stream:
            async for text in stream.text_stream:
                if text:
                    yield f"data: {json.dumps({'content': text})}\n\n"
    elif openai_client:
        stream = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=True
        )
        async for chunk in stream:
            text = chunk.choices[0].delta.content
            if text:
                yield f"data: {json.dumps({'content': text})}\n\n"
    else:
        yield f"data: {json.dumps({'content': 'No valid LLM provider or API key found.'})}\n\n"
        
    yield f"data: {json.dumps({'done': True})}\n\n"
