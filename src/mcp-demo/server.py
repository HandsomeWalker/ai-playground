# server.py
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

# 创建 MCP 实例
mcp = FastMCP("本地计算服务")


# 定义工具类（支持数据模型验证）
class ConversionRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str


@mcp.tool()
def currency_converter(request: ConversionRequest) -> dict:
    """货币转换工具，使用当日最新汇率"""
    exchange_rates = {"USD_CNY": 7.23, "CNY_USD": 0.14}
    key = f"{request.from_currency}_{request.to_currency}"
    rate = exchange_rates.get(key, 1.0)
    converted = request.amount * rate
    return {
        "amount": request.amount,
        "converted": round(converted, 2),
        "rate": rate,
        "timestamp": "2025-05-13",
    }


@mcp.tool()
def get_weather(city: str) -> dict:
    """今日天气查询工具"""
    weather_data = {
        "北京": {"temperature": 25, "condition": "晴"},
        "上海": {"temperature": 28, "condition": "多云"},
        "广州": {"temperature": 23, "condition": "阴"},
        "深圳": {"temperature": 26, "condition": "小雨"},
        "杭州": {"temperature": 24, "condition": "雷阵雨"},
        "成都": {"temperature": 21, "condition": "小雨转阴"},
    }
    return weather_data.get(city, {"temperature": 0, "condition": "未知"})


if __name__ == "__main__":
    mcp.run(transport="stdio")  # 本地调试模式
