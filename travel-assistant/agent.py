import os
import sys
import asyncio
import importlib
# from dotenv import load_dotenv
from typing import Dict, Any, List
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client
# from langchain_openai import ChatOpenAI

# load_dotenv()

rag_engine = importlib.import_module("rag-engine")
KnowledgeBaseRetriever = rag_engine.KnowledgeBaseRetriever
SYSTEM_TRAVEL_PROMPT = """You are an expert, context-aware AI Travel Assistant specializing in Singapore. 
Your job is to generate accurate, weather-aware, and budget-aware travel itineraries and recommendations.
Generate clear travel itineraries along with transportation details.
Include budget estimates when user asks for cost information or has a budget in mind.
Consider user preferences, like family friendly trip, from chat history when providing recommendations.

### CRITICAL RULES & CITATION INSTRUCTIONS:
1. **Knowledge Base Usage (RAG)**: Use ONLY the provided retrieved Knowledge Base context for destination facts (attractions, culture, districts, transport). Cite source files clearly.
2. **MCP Tool Responses**: Use weather forecasts and currency calculations strictly from the connected MCP tool execution results. Mark them explicitly with "[Source: MCP Weather Tool]" or "[Source: MCP Currency Tool]".
3. **Missing Facts & Tool Errors**: If the knowledge base does NOT contain required info, explicitly state: "Information not available in knowledge base." Do NOT invent or hallucinate facts.
4. **Distinction**: Clearly differentiate between:
   - 📌 **Destination Facts** (from RAG)
   - ⚡ **Real-time Context** (from MCP tools)
   - 💡 **AI Recommendations & Adjustments** (LLM synthesis)
5. **Weather Adaptation**: Whenever rain or thunderstorms are forecasted in MCP weather outputs, swap outdoor activities for nearby indoor alternatives found in the knowledge base (e.g., Cloud Forest, ArtScience Museum).
6. **Budget Awareness**: Use MCP currency conversion outputs to provide cost estimates in SGD and USD. If the user asks for budget-friendly options, prioritize free or low-cost attractions.
7. Call MCP tools only when necessary. If the user query does not require weather or currency info, do not invoke MCP tools.
8. If user asks only for current information like weather or exchange rates, provide the MCP tool output directly without additional synthesis.
"""

class TravelAssistantAgent:
    def __init__(self):
        # Initialize Local Ollama LLM (Requires 'ollama run llama3.1' or running service)
        self.llm = ChatOllama(
            model="llama3.1",
            temperature=0.2
        )
        # self.llm = ChatOpenAI(
        #     model="gpt-4o",
        #     temperature=0.2
        # )
        self.rag = KnowledgeBaseRetriever()

    async def run_query(self, user_query: str, chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Processes query using Chroma RAG, OpenAI, and MCP tool execution."""
        
        # 1. Retrieve ChromaDB context
        retrieved_rag_context = self.rag.retrieve_context(user_query)

        # Setup paths for Python executable & MCP servers
        python_executable = sys.executable
        base_dir = os.path.dirname(os.path.abspath(__file__))
        weather_script = os.path.join(base_dir, "weather-mcp-server.py")
        currency_script = os.path.join(base_dir, "currency-mcp-server.py")

        weather_params = StdioServerParameters(command=python_executable, args=[weather_script])
        currency_params = StdioServerParameters(command=python_executable, args=[currency_script])

        mcp_tools = []
        
        try:
            
            # Connect to MCP Servers over stdio
            async with stdio_client(weather_params) as (r1, w1), ClientSession(r1, w1) as s1:
                await s1.initialize()
                tools_weather = await load_mcp_tools(s1)
                
                async with stdio_client(currency_params) as (r2, w2), ClientSession(r2, w2) as s2:
                    await s2.initialize()
                    tools_currency = await load_mcp_tools(s2)
                    
                    mcp_tools = tools_weather + tools_currency
                    
                    # Bind local MCP tools directly to Ollama Chat Model
                    llm_with_tools = self.llm.bind_tools(mcp_tools)

                    # Format System & Conversational Messages
                    messages = [SystemMessage(content=SYSTEM_TRAVEL_PROMPT)]
                    
                    if chat_history:
                        for msg in chat_history:
                            if msg["role"] == "user":
                                messages.append(HumanMessage(content=msg["content"]))
                            elif msg["role"] == "assistant":
                                messages.append(AIMessage(content=msg["content"]))

                    augmented_prompt = f"User Request: {user_query}\n\n{retrieved_rag_context}"
                    messages.append(HumanMessage(content=augmented_prompt))

                    # Step 1: Tool Selection Decision
                    ai_response = await llm_with_tools.ainvoke(messages)
                    tool_results_str = ""
                    tool_outputs = []

                    # Step 2: Execute selected MCP tools if triggered
                    if hasattr(ai_response, "tool_calls") and ai_response.tool_calls:
                        messages.append(ai_response)
                        for tool_call in ai_response.tool_calls:
                            selected_tool = next((t for t in mcp_tools if t.name == tool_call["name"]), None)
                            if selected_tool:
                                tool_out = await selected_tool.ainvoke(tool_call["args"])
                                tool_results_str += f"\n[MCP Tool Executed: {tool_call['name']}]\nOutput: {tool_out}\n"
                                messages.append(HumanMessage(content=f"MCP Tool Response ({tool_call['name']}): {tool_out}"))

                        # Step 3: Synthesize final output with context & tool outputs
                        final_res = await self.llm.ainvoke(messages)
                        response_text = final_res.content
                    else:
                        response_text = ai_response.content

                    return {
                        "answer": response_text,
                        "rag_context": retrieved_rag_context,
                        "mcp_output": tool_results_str if tool_results_str else "No MCP tools required for this query."
                    }

        except Exception as mcp_conn_err:
            # Fallback if MCP server process failed to connect or crashed on stdio startup
            fallback_msg = (
                f"Note: MCP real-time tools were unavailable ({str(mcp_conn_err)}). "
                "Answering strictly using stored Knowledge Base facts."
            )
                    
            # Invoke LLM without tool-binding as a fallback strategy
            fallback_res = await self.llm.ainvoke([
                SystemMessage(content=SYSTEM_TRAVEL_PROMPT),
                HumanMessage(content=f"User Request: {user_query}\n\n{retrieved_rag_context}\n\n{fallback_msg}")
            ])

            return {
                "answer": fallback_res.content,
                "rag_context": retrieved_rag_context,
                "mcp_output": f"MCP Connection Error: {str(mcp_conn_err)}"
            }