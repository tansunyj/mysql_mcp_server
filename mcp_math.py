#!/usr/bin/env python3

import asyncio
import logging
import os
import sys
import math
import signal  # 添加这行导入
from typing import Dict, Any
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("math-service")

logger.info(f"Python版本: {sys.version}")
logger.info(f"当前工作目录: {os.getcwd()}")
logger.info(f"脚本路径: {__file__}")

# 初始化MCP服务器
app = Server("math-service")

def calculate_triangle(base: float, height: float, a: float = None, b: float = None, c: float = None) -> Dict[str, float]:
    """计算三角形的面积和周长"""
    area = 0.5 * base * height
    
    # 如果提供了三边长，计算周长
    if all(x is not None for x in [a, b, c]):
        perimeter = a + b + c
    else:
        perimeter = None
        
    return {
        "area": area,
        "perimeter": perimeter if perimeter else "需要提供三边长才能计算周长"
    }

def calculate_circle(radius: float) -> Dict[str, float]:
    """计算圆的面积和周长"""
    area = math.pi * radius * radius
    perimeter = 2 * math.pi * radius
    return {
        "area": area,
        "perimeter": perimeter
    }

def calculate_ellipse(a: float, b: float) -> Dict[str, float]:
    """计算椭圆的面积和周长（周长使用Ramanujan近似公式）"""
    area = math.pi * a * b
    # Ramanujan近似公式
    h = ((a - b) / (a + b)) ** 2
    perimeter = math.pi * (a + b) * (1 + (3 * h / (10 + math.sqrt(4 - 3 * h))))
    return {
        "area": area,
        "perimeter": perimeter
    }

def calculate_trapezoid(a: float, b: float, h: float, c: float = None, d: float = None) -> Dict[str, float]:
    """计算梯形的面积和周长"""
    area = (a + b) * h / 2
    perimeter = a + b + (c + d if c and d else 2 * math.sqrt(h**2 + ((b-a)/2)**2))
    return {
        "area": area,
        "perimeter": perimeter
    }

def calculate_trig_functions(angle_degrees: float) -> Dict[str, float]:
    """计算三角函数值"""
    angle_rad = math.radians(angle_degrees)
    return {
        "sin": math.sin(angle_rad),
        "cos": math.cos(angle_rad),
        "tan": math.tan(angle_rad),
        "cot": 1 / math.tan(angle_rad) if math.tan(angle_rad) != 0 else float('inf')
    }

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""
    logger.info(f"调用工具: {name}, 参数: {arguments}")
    
    try:
        result = None
        if name == "triangle_calc":
            result = calculate_triangle(
                float(arguments["base"]),
                float(arguments["height"]),
                float(arguments.get("a", None)),
                float(arguments.get("b", None)),
                float(arguments.get("c", None))
            )
        elif name == "circle_calc":
            result = calculate_circle(float(arguments["radius"]))
        elif name == "ellipse_calc":
            result = calculate_ellipse(
                float(arguments["a"]),
                float(arguments["b"])
            )
        elif name == "trapezoid_calc":
            result = calculate_trapezoid(
                float(arguments["a"]),
                float(arguments["b"]),
                float(arguments["height"]),
                float(arguments.get("c", None)),
                float(arguments.get("d", None))
            )
        elif name == "trig_functions":
            result = calculate_trig_functions(float(arguments["angle"]))
        
        if result:
            return [TextContent(type="text", text=str(result))]
        else:
            return [TextContent(type="text", text="未知的计算类型")]
            
    except Exception as e:
        logger.error(f"计算出错: {str(e)}", exc_info=True)
        return [TextContent(type="text", text=f"计算出错: {str(e)}")]

@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用的数学计算工具"""
    logger.info("列出工具...")
    return [
        Tool(
            name="triangle_calc",
            description="计算三角形的面积和周长",
            inputSchema={
                "type": "object",
                "properties": {
                    "base": {"type": "number", "description": "底边长"},
                    "height": {"type": "number", "description": "高"},
                    "a": {"type": "number", "description": "边长a（可选）"},
                    "b": {"type": "number", "description": "边长b（可选）"},
                    "c": {"type": "number", "description": "边长c（可选）"}
                },
                "required": ["base", "height"]
            }
        ),
        Tool(
            name="circle_calc",
            description="计算圆的面积和周长",
            inputSchema={
                "type": "object",
                "properties": {
                    "radius": {"type": "number", "description": "半径"}
                },
                "required": ["radius"]
            }
        ),
        Tool(
            name="ellipse_calc",
            description="计算椭圆的面积和周长",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "长半轴"},
                    "b": {"type": "number", "description": "短半轴"}
                },
                "required": ["a", "b"]
            }
        ),
        Tool(
            name="trapezoid_calc",
            description="计算梯形的面积和周长",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "上底"},
                    "b": {"type": "number", "description": "下底"},
                    "height": {"type": "number", "description": "高"},
                    "c": {"type": "number", "description": "左边长（可选）"},
                    "d": {"type": "number", "description": "右边长（可选）"}
                },
                "required": ["a", "b", "height"]
            }
        ),
        Tool(
            name="trig_functions",
            description="计算三角函数值（正弦、余弦、正切、余切）",
            inputSchema={
                "type": "object",
                "properties": {
                    "angle": {"type": "number", "description": "角度值（度）"}
                },
                "required": ["angle"]
            }
        )
    ]

@app.list_resources()
async def list_resources() -> list[Resource]:
    """列出可用的数学计算资源"""
    logger.info("列出资源...")
    return [
        Resource(
            uri="math://formulas",
            name="数学公式计算服务",
            mimeType="application/json",
            description="提供各种几何图形的面积周长计算和三角函数计算"
        )
    ]

async def main():
    """主入口点"""
    from mcp.server.stdio import stdio_server

    def signal_handler(sig, frame):
        logger.info(f"收到信号 {sig}，准备退出...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    logger.info("注册信号处理器，按Ctrl+C可正常退出")

    sys.stdout.flush()
    sys.stderr.flush()

    logger.info("MCP服务即将启动并进入监听状态...")

    async with stdio_server() as (read_stream, write_stream):
        try:
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
        except Exception as e:
            logger.error(f"服务器错误: {str(e)}", exc_info=True)
            raise

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("收到键盘中断，程序退出")
    except Exception as e:
        logger.critical(f"MCP服务启动失败: {str(e)}", exc_info=True)
        sys.exit(1)