from pathlib import Path
from typing import Sequence, List
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableSerializable
from langgraph.constants import START, END
from langgraph.graph import MessageGraph
from tools.configuration import GoogleConfiguration as Configuration

GENERATE = "GENERATE"
CRITICIZE = "CRITICIZE"
NO_OF_ITRs = 6
configuration = Configuration()
llm = configuration.get_llm(temperature=0.7)

def generation_node(state: Sequence[BaseMessage]):
    """Generates Tweets with a lot of effort."""
    prompt = ChatPromptTemplate.from_messages([
        ('system', 'You are a helpful assistant who is an expert expanding on an idea or correcting the contents based on suggestions.'),
        (MessagesPlaceholder(variable_name="messages"))
    ])
    chain: RunnableSerializable = prompt | llm
    result = [chain.invoke({"messages": state})]
    return result

def criticize_node(state: Sequence[BaseMessage]) -> List[BaseMessage]:
    """This guy is the wise learnt rubber duck filled."""
    prompt = ChatPromptTemplate.from_messages([
        ('system','You are a helpful assistant who is an expert at reviewing and suggesting corrections.'),
        (MessagesPlaceholder(variable_name="messages"))
    ])
    chain: RunnableSerializable = prompt | llm
    result = chain.invoke({"messages": [HumanMessage(state[-1].content)]})
    return [HumanMessage(content=result.content)]

def route_based_on_enough_criticizm(state: Sequence[BaseMessage]) -> str:
    """"""
    if len(state) < NO_OF_ITRs:
        return GENERATE
    else:
        return END


def process(content: str):
    builder = MessageGraph()
    builder.add_node(GENERATE, generation_node)
    builder.add_node(CRITICIZE, criticize_node)
    builder.add_edge(START, GENERATE)
    builder.add_edge(GENERATE, CRITICIZE)
    builder.add_conditional_edges(CRITICIZE, route_based_on_enough_criticizm)

    graph = builder.compile()
    graph.get_graph().draw_png(f"misc/{Path(__file__).stem}.png")

    for c in graph.stream(HumanMessage(content=content)):
        print(c, "\n", "-"*20)

if __name__=="__main__":
    process("In a black hole there is in goldilocks zone.")