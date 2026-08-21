from typing import (
    Any,
    List,
    Dict,
    Tuple,
    AsyncGenerator,
    Optional
)
import re
import json
import logging

from app.logic.llm_wrapper import async_generate, async_generate_stream
from app.utils.message_cleanup import sanitize_history
from app.schemas.general import Message
from app.core.prompts import TEST_PROMPT, FAQ_RETRIEVER_AGENT, FAQ_SYNTHESIZER_AGENT
from app.logic.faq_store import faq_store, FAQMatch


logger = logging.getLogger(__name__)

__all__ = [
    "pipeline",
    "pipeline_stream"
]

T_History = List[Dict[str, str]]
T_Conv    = List[Dict[str, str]]


def _build_conv(query: str, prompt: str = FAQ_RETRIEVER_AGENT, history: Optional[T_History] = None, ctx: Optional[str] = None)-> T_Conv: ...
def _format_FAQ(matches: List[FAQMatch]) -> Dict[str, str]: ...
def _parse_llm(response: str) -> Tuple[str, str]: ...

async def synthesis_agent(
        cxt:     str,
        query:   str,
        prompt:  Optional[str]       = FAQ_SYNTHESIZER_AGENT,
        history: Optional[T_History] = None
) -> str: ...

async def synthesis_agent_stream(
    ctx:     str, 
    query:   str, 
    history: Optional[T_History] = None, 
    prompt:  Optional[str]       = None
) -> AsyncGenerator[str, None]: ...

async def pipeline_stream(
    query: str,
    history: Optional[List[Message]] = None,
    user_name: Optional[str] = None
) -> AsyncGenerator[str, None]:
    clean_history = sanitize_history(history)
    conversation = _build_conv(
        query=query,
        prompt=FAQ_RETRIEVER_AGENT,
        history=clean_history
    )

    results = await faq_store.search(query)
    conversation.append(_format_FAQ(results))

    logger.warning("[orchestrator] First retrieval yield")
    logger.warning(f"[orchestrator] {conversation[-1]}")

    final_llm_content: str = ""

    for i in range(1, 4):
        try:
            llm = await async_generate(msg=conversation)
        except Exception as e:
            logger.warning("[orchestrator] Things went wrong while retrieving data")
            logger.warning(f"[orchestrator] Err Msg: {str(e)}")
            continue

        action, value = _parse_llm(llm)

        logger.debug(f"[orchestrator] LLM action: {action}")
        logger.debug(f"[orchestrator] LLM content: {value}")

        if action == "SEARCH":
            conversation.append({
                "role": "assistant",
                "content": llm
            })
            results = await faq_store.search(query=value)
            conversation.append(_format_FAQ(results))
        else:
            if value.upper() == "FAIL":
                yield json.dumps({"error": "NO_ANSWER", "message": "Unable to find relevant information"})
                return
            
            final_llm_content = value
            break

    async for chunk in synthesis_agent_stream(
        ctx=final_llm_content,
        query=query,
        history=history,
        prompt=FAQ_SYNTHESIZER_AGENT
    ):
        yield chunk

async def pipeline(
    query:     str,
    history:   Optional[List[Message]] = None,
    user_name: Optional[str]           = None
):
    clean_history = sanitize_history(history)
    conversation  = _build_conv(
        query=query,
        prompt=FAQ_RETRIEVER_AGENT,
        history=clean_history)

    results = await faq_store.search(query)
    conversation.append(_format_FAQ(results))

    logger.warning("[orchestrator] First retrieval yield")
    logger.warning(f"[orchestrator] {conversation[-1]}")

    final_llm_content: str = ""

    for i in range(1, 4):
        # try:
        #     llm = await async_generate(msg=conversation)
        # except Exception as e:
        #     logger.warning("[orchestrator] Things went wrong while retrieving data")
        #     logger.warning(f"[orchestrator] Err Msg: {str(e)}")

        llm = await async_generate(msg=conversation)

        action, value = _parse_llm(llm)

        logger.debug(f"[orchestrator] LLM action: {action}")
        logger.debug(f"[orchestrator] LLM content: {value}")

        if action == "SEARCH":
            conversation.append(
                {
                    "role": "assistant",
                    "content": llm
                }
            )
            results = await faq_store.search(query=value)
            conversation.append(_format_FAQ(results))
        else:
            if value.upper() == "FAIL":
                return 'NO-ANSWER'
            
            final_llm_content = value
            break

    final_synthesis = await synthesis_agent(
        ctx = final_llm_content,
        query = query,
        history = history,
        prompt = FAQ_SYNTHESIZER_AGENT
    )
    return final_synthesis.strip()

async def synthesis_agent_stream(
    ctx: str, 
    query: str, 
    history: Optional[T_History] = None, 
    prompt: Optional[str] = None
) -> AsyncGenerator[str, None]:
    clean_history = sanitize_history(history)
    conversation = _build_conv(
        query=query,
        prompt=prompt,
        history=clean_history,
        ctx=ctx
    )
    
    try:
        async for chunk in async_generate_stream(conversation):
            # Send raw text chunks instead of JSON
            yield chunk
    except Exception as e:
        logger.warning("[orchestrator] Things went wrong while synthesizing an answer")
        logger.warning(f"[orchestrator] Err Msg: {str(e)}")
        yield f"ERROR: {str(e)}"

async def synthesis_agent(ctx: str, query: str, history: Optional[T_History] = None, prompt: Optional[str] = None) -> str:
    clean_history = sanitize_history(history)
    conversation = _build_conv(
        query = query,
        prompt = prompt,
        history = clean_history,
        ctx = ctx
    )
    # try:
    #     synthesis = await async_generate(conversation)
    # except Exception as e:
    #     logger.warning("[orchestrator] Things went wrong while synthesizing an answer")
    #     logger.warning(f"[orchestrator] Err Msg: {str(e)}")

    synthesis = await async_generate(conversation)
    return synthesis.strip()

def _build_conv(
        query:   str, 
        prompt:  str                 = FAQ_RETRIEVER_AGENT,
        history: Optional[T_History] = None,
        ctx:     Optional[str]       = None
) -> T_Conv:
    conversation = [
        {
            "role":    "system",
            "content": prompt
        }
    ]

    if history: conversation = conversation + history

    if not ctx:
        conversation.append(
            {
                "role":    "user",
                "content": query
            }
        )
        return conversation

    full_ctx = f"##user query: {query}\n##found information from vector store: \n{ctx}"

    conversation.append({
        "role": "user",
        "content": full_ctx
    })
    return conversation

def _format_FAQ(matches: List[FAQMatch]) -> Dict[str, str]:
    formatted = "FAQ pairs found:\n"
    for i, m in enumerate(matches):
        formatted += f"Similar FAQ pair #{i}:\nQ: {m.question}\nA: {m.answer}\n\n"

    msg = {
        "role": "user",
        "content": formatted
    }
    return msg

def _parse_llm(response: str) -> Tuple[str, str]:
    response = response.strip()
    m = re.search(r"ACTION:\s*(SEARCH|ANSWER)", response, re.IGNORECASE)
    action = m.group(1).upper() if m else "ANSWER"
    if action == "SEARCH":
        q = re.search(r"QUERY:\s*(.+?)(?:\n|$)", response, re.IGNORECASE | re.DOTALL)
        value = q.group(1).strip() if q else response
    else:
        c = re.search(r"CONTENT:\s*(.+)", response, re.IGNORECASE | re.DOTALL)
        value = c.group(1).strip() if c else response
    return action, value