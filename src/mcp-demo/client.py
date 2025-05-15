# mcp_client_demo.py
import asyncio
from typing import Optional
from contextlib import AsyncExitStack
from dotenv import load_dotenv
from ollama import AsyncClient
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
import os

# 加载环境变量
load_dotenv()


class MCPClientDemo:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.llm_client = AsyncClient()

    async def connect_server(self, server_script: str):
        """连接MCP服务器[1,6](@ref)"""
        server_params = StdioServerParameters(command="uv", args=["run", server_script])

        # 建立stdio通信通道
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.reader, self.writer = stdio_transport

        # 初始化会话
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.reader, self.writer)
        )
        await self.session.initialize()

        # 获取工具列表
        tools = await self.session.list_tools()
        print(f"🔧 可用工具: {[t.name for t in tools.tools]}")

    async def process_query(self, query: str):
        """处理用户查询[5,8](@ref)"""
        # 构造LLM请求参数
        messages = [{"role": "user", "content": query}]
        tools = await self._prepare_tools()

        # 调用LLM生成响应
        response = await self.llm_client.chat(
            model="qwen3:14b",
            messages=messages,
            tools=tools,
        )

        # 处理工具调用
        tool_calls = response.message.tool_calls
        if tool_calls:
            print("🛠️ 检测到工具调用请求:")
            for call in tool_calls:
                tool_name = call.function.name
                args = call.function.arguments
                print(f"调用工具: {tool_name} 参数: {args}")

                # 执行工具调用
                result = await self.session.call_tool(tool_name, args)
                print(f"🔧 工具执行结果: {result}")

                # 将结果反馈给LLM
                messages.append(
                    {
                        "role": "tool",
                        "content": str(result),
                        "tool_call_id": call.get("id"),
                    }
                )

                # 获取最终响应
                final_response = await self.llm_client.chat(
                    model="qwen3:14b", messages=messages, stream=True
                )
                async for chunk in final_response:
                    print(chunk.message.content, flush=True, end="")
        else:
            print("📝 直接响应:", response.message.content)

    async def _prepare_tools(self):
        """转换工具格式[2,6](@ref)"""
        tools_response = await self.session.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in tools_response.tools
        ]

    async def close(self):
        """关闭连接"""
        await self.exit_stack.aclose()


async def main():
    client = MCPClientDemo()
    try:
        # 连接本地MCP服务器（需提前运行）
        await client.connect_server("{cwd}/src/mcp-demo/server.py".format(cwd=os.getcwd()))

        # 示例查询
        while True:
            query = input("\n❓ 输入查询（输入q退出）: ")
            if query.lower() == "q":
                break
            await client.process_query(query)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
