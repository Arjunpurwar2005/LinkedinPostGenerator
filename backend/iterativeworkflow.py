import os
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from dotenv import load_dotenv

load_dotenv()

# ---------- TOOLS ----------
search_tool = TavilySearch(max_results=3)

# ---------- LLMs ----------
writer_llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.7)
reviewer_llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.2)

# ---------- STATE ----------
class State(TypedDict):
    topic: str
    draft: str
    review_feedback: str
    is_approved: bool
    attempt: int

# ---------- WRITER AGENT (handles its own tool-calling loop) ----------
WRITER_SYSTEM_PROMPT = (
    "You are an expert LinkedIn content writer. Your job is to write "
    "engaging, professional LinkedIn posts about the given topic. "
    "If the topic requires up-to-date information, statistics, or "
    "current trends, use the web search tool to gather fresh context "
    "before writing. If you have already received feedback on a "
    "previous draft, carefully address every point in the new draft. "
    "Rules for good LinkedIn posts: strong hook in the first line, "
    "1 clear takeaway, easy to skim (short paragraphs), around "
    "150–200 words, ends with a question or call-to-action to invite "
    "engagement. Do not use hashtags."
)

writer_agent = create_agent(
    model=writer_llm,
    tools=[search_tool],
    system_prompt=WRITER_SYSTEM_PROMPT,
)

def writer_node(state: State) -> dict:
    """Writes (or rewrites) the LinkedIn post. Agent decides itself if it needs to search."""
    attempt = state.get("attempt", 0) + 1
    topic = state["topic"]
    previous_feedback = state.get("review_feedback", "")

    if attempt == 1:
        user_message = (
            f"Write a LinkedIn post on this topic: {topic}. "
            f"If you need current info, search the web first."
        )
    else:
        user_message = (
            f"Your previous draft on '{topic}' was rejected.\n"
            f"Here is the reviewer's feedback:\n\n{previous_feedback}\n\n"
            f"Write a new, improved draft that fixes every issue mentioned. "
            f"Do not repeat the same mistake."
        )

    result = writer_agent.invoke({"messages": [("human", user_message)]})
    draft = result["messages"][-1].content  # agent ka final text answer

    print(f"\n\ngenerated post\n{draft}\n")

    return {
        "draft": draft,
        "attempt": attempt,
    }

# ---------- REVIEWER ----------
REVIEWER_SYSTEM_PROMPT = (
    "You are a strict LinkedIn content reviewer. You judge whether a "
    "post is publish-ready. Evaluate against these criteria:\n"
    "1. Strong hook in the first line\n"
    "2. One clear, valuable takeaway\n"
    "3. Easy to skim — uses short paragraphs\n"
    "4. Roughly 150-200 words\n"
    "5. Ends with an engaging question or CTA\n"
    "6. Professional but human tone (not corporate-robotic)\n"
    "7. No hashtags\n\n"
    "Respond in exactly this format:\n"
    "VERDICT: APPROVED or REJECTED\n"
    "FEEDBACK: <one short paragraph explaining why>\n\n"
    "Be strict but fair. Approve only if the post genuinely meets all "
    "criteria. Reject if even one criterion is clearly missing."
)

def reviewer_node(state: State) -> dict:
    """Reviews the draft and decides: approve or reject with feedback."""
    draft = state['draft']

    prompt = (
        f"review this LinkedIn post draft : \n"
        f"{draft}\n"
        f"give your reviews"
    )
    response = reviewer_llm.invoke(
        [("system", REVIEWER_SYSTEM_PROMPT), ("human", prompt)]
    )
    review_text = response.content.strip()

    verdict_part, _, feedback_part = review_text.partition("FEEDBACK:")

    if "APPROVED" in verdict_part.upper():
        is_approved = True
    else:
        is_approved = False

    if feedback_part:
        feedback = feedback_part.strip()
    else:
        feedback = review_text

    print(f"[Verdict: {'APPROVED' if is_approved else 'REJECTED'}]")
    print(f"[Feedback: {feedback}]")

    return {
        "review_feedback": feedback,
        "is_approved": is_approved,
    }

# ---------- ROUTER: loop chalu rakhna hai ya rokna hai ----------
def should_stop_looping(state: State):
    if state['is_approved']:
        print("post has been approved \n")
        return END
    if state['attempt'] >= 3:
        print("reached max attempts")
        return END
    return "writer"

# ---------- GRAPH ----------
graph = StateGraph(State)

graph.add_node("writer", writer_node)
graph.add_node("reviewer", reviewer_node)

graph.add_edge(START, "writer")
graph.add_edge("writer", "reviewer")
graph.add_conditional_edges("reviewer", should_stop_looping)

app = graph.compile()

def get_graph():
    return graph.compile()

def run_agent(graph, topic: str):
    initial_state = {
        "topic": topic,
        "draft": "",
        "review_feedback": "",
        "is_approved": False,
        "attempt": 0,
    }
    final_state = graph.invoke(initial_state)
    return final_state["draft"]


# # ---------- RUN ----------
# print("=" * 55)
# print("Welcome to the LinkedIn Post Generator")
# print("=" * 55)
# print("\nThis tool will draft a LinkedIn post for you, review it")
# print("itself, and iterate until it's publish-ready.")
# print("=" * 55)

# topic = input("\nWhat topic do you want a LinkedIn post about?\n> ").strip()

# if not topic:
#     print("\nNo topic given. Exiting.")
# else:
#     print("\nStarting generation...\n")

#     initial_state = {
#         "topic": topic,
#         "draft": "",
#         "review_feedback": "",
#         "is_approved": False,
#         "attempt": 0,
#     }

#     final_state = app.invoke(initial_state)

#     print("\n" + "=" * 55)
#     print("FINAL LINKEDIN POST")
#     print("=" * 55)
#     print(final_state["draft"])
#     print("=" * 55)
#     print(f"Total attempts: {final_state['attempt']}")
#     print(f"Approved: {final_state['is_approved']}")