"""
LangChain-based structured flight query parser.
Deterministic, JSON-only output.
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.settings import settings


class FlightQuery(BaseModel):
    """Schema for flight query parameters."""
    origin: str = Field(description="IATA origin airport code (e.g. SFO)")
    destination: str = Field(
        description="IATA destination airport code (e.g. CDG)")
    date: str = Field(description="Departure date YYYY-MM-DD")


parser = JsonOutputParser(pydantic_object=FlightQuery)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Extract structured flight search parameters.\n{format_instructions}"
        ),
        ("user", "{query}")
    ]
)

""" LLM parser """
llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
    api_key=settings.OPENAI_API_KEY,
)

chain = prompt | llm | parser

""" public API function to parse flight query """


async def parse_flight_query(query: str) -> dict:
    """
    Guaranteed structured output.
    """
    return await chain.ainvoke(
        {
            "query": query,
            "format_instructions": parser.get_format_instructions(),
        }
    )
