#!/usr/bin/env python3

# 添加所需的导入
import logging
import os
import sys
import base64
import io
import signal
import asyncio
import numpy as np
import matplotlib.pyplot as plt
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("geometry-service")

logger.info(f"Python版本: {sys.version}")
logger.info(f"当前工作目录: {os.getcwd()}")
logger.info(f"脚本路径: {__file__}")

app = Server("geometry-service")

def save_figure_to_base64():
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return img_base64

def generate_circle_js(center_x, center_y, radius):
    """生成绘制圆形的JavaScript代码"""
    js_code = f"""
<div id="canvas-container">
<canvas id="geometryCanvas" width="400" height="400" style="border:1px solid #000;"></canvas>
<script>
const canvas = document.getElementById('geometryCanvas');
const ctx = canvas.getContext('2d');

// 设置画布样式
ctx.strokeStyle = '#000';
ctx.lineWidth = 2;

// 绘制圆
ctx.beginPath();
ctx.arc({center_x}, {center_y}, {radius}, 0, 2 * Math.PI);
ctx.stroke();

// 绘制坐标轴
ctx.strokeStyle = '#999';
ctx.lineWidth = 1;
ctx.beginPath();
ctx.moveTo(0, 200);
ctx.lineTo(400, 200);
ctx.moveTo(200, 0);
ctx.lineTo(200, 400);
ctx.stroke();

// 绘制刻度
ctx.fillStyle = '#999';
ctx.font = '12px Arial';
for(let i = 0; i <= 400; i += 50) {{
    ctx.fillText(i-200, i, 215);
    ctx.fillText(200-i, 215, i);
}}
</script>
</div>
"""
    return js_code

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    logger.info(f"调用工具: {name}, 参数: {arguments}")

    try:
        if name == "draw_circle":
            # 验证参数
            if not all(key in arguments for key in ["center_x", "center_y", "radius"]):
                return [TextContent(type="text", text="缺少必要参数")]
            
            # 生成图片并获取base64编码
            img_data = draw_circle(
                arguments["center_x"],
                arguments["center_y"],
                arguments["radius"]
            )
            
            # 返回markdown格式的图片
            return [TextContent(
                type="text",
                text=f"![circle](data:image/png;base64,{img_data})"
            )]
        elif name == "draw_line":
            img = draw_line(arguments.get("x1"), arguments.get("y1"), arguments.get("x2"), arguments.get("y2"))
            return [TextContent(type="text", text=f"data:image/png;base64,{img}")]
        elif name == "draw_triangle":
            img = draw_triangle(arguments.get("points"))
            return [TextContent(type="text", text=f"data:image/png;base64,{img}")]
        elif name == "draw_rectangle":
            img = draw_rectangle(arguments.get("x"), arguments.get("y"), arguments.get("width"), arguments.get("height"))
            return [TextContent(type="text", text=f"data:image/png;base64,{img}")]
        elif name == "draw_polygon":
            img = draw_polygon(arguments.get("points"))
            return [TextContent(type="text", text=f"data:image/png;base64,{img}")]
        elif name == "draw_trapezoid":
            img = draw_trapezoid(arguments.get("points"))
            return [TextContent(type="text", text=f"data:image/png;base64,{img}")]
        elif name == "draw_ellipse":
            img = draw_ellipse(arguments.get("center_x"), arguments.get("center_y"), arguments.get("width"), arguments.get("height"))
            return [TextContent(type="text", text=f"data:image/png;base64,{img}")]
        elif name == "draw_sin_curve":
            img = draw_sin_curve(arguments.get("start_x", 0), arguments.get("end_x", 2*np.pi))
            return [TextContent(type="text", text=f"data:image/png;base64,{img}")]
        elif name == "draw_cos_curve":
            img = draw_cos_curve(arguments.get("start_x", 0), arguments.get("end_x", 2*np.pi))
            return [TextContent(type="text", text=f"data:image/png;base64,{img}")]
        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]
    except Exception as e:
        logger.error(f"绘图出错: {str(e)}", exc_info=True)
        return [TextContent(type="text", text=f"绘图出错: {str(e)}")]

@app.list_tools()
async def list_tools() -> list[Tool]:
    logger.info("列出工具...")
    return [
        Tool(
            name="draw_line",
            description="绘制线段",
            inputSchema={
                "type": "object",
                "properties": {
                    "x1": {"type": "number", "description": "起点x"},
                    "y1": {"type": "number", "description": "起点y"},
                    "x2": {"type": "number", "description": "终点x"},
                    "y2": {"type": "number", "description": "终点y"}
                },
                "required": ["x1", "y1", "x2", "y2"]
            }
        ),
        Tool(
            name="draw_triangle",
            description="绘制三角形",
            inputSchema={
                "type": "object",
                "properties": {
                    "points": {
                        "type": "array",
                        "description": "三角形三个顶点坐标，如[[x1,y1],[x2,y2],[x3,y3]]",
                        "items": {"type": "array", "items": {"type": "number"}}
                    }
                },
                "required": ["points"]
            }
        ),
        Tool(
            name="draw_rectangle",
            description="绘制矩形",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "左上角x"},
                    "y": {"type": "number", "description": "左上角y"},
                    "width": {"type": "number", "description": "宽度"},
                    "height": {"type": "number", "description": "高度"}
                },
                "required": ["x", "y", "width", "height"]
            }
        ),
        Tool(
            name="draw_polygon",
            description="绘制多边形（如平行四边形）",
            inputSchema={
                "type": "object",
                "properties": {
                    "points": {
                        "type": "array",
                        "description": "多边形顶点坐标，如[[x1,y1],[x2,y2],...]",
                        "items": {"type": "array", "items": {"type": "number"}}
                    }
                },
                "required": ["points"]
            }
        ),
        Tool(
            name="draw_trapezoid",
            description="绘制梯形",
            inputSchema={
                "type": "object",
                "properties": {
                    "points": {
                        "type": "array",
                        "description": "梯形四个顶点坐标，如[[x1,y1],[x2,y2],[x3,y3],[x4,y4]]",
                        "items": {"type": "array", "items": {"type": "number"}}
                    }
                },
                "required": ["points"]
            }
        ),
        Tool(
            name="draw_circle",
            description="绘制圆",
            inputSchema={
                "type": "object",
                "properties": {
                    "center_x": {"type": "number", "description": "圆心x"},
                    "center_y": {"type": "number", "description": "圆心y"},
                    "radius": {"type": "number", "description": "半径"}
                },
                "required": ["center_x", "center_y", "radius"]
            }
        ),
        Tool(
            name="draw_ellipse",
            description="绘制椭圆",
            inputSchema={
                "type": "object",
                "properties": {
                    "center_x": {"type": "number", "description": "中心x"},
                    "center_y": {"type": "number", "description": "中心y"},
                    "width": {"type": "number", "description": "宽轴"},
                    "height": {"type": "number", "description": "高轴"}
                },
                "required": ["center_x", "center_y", "width", "height"]
            }
        ),
        Tool(
            name="draw_sin_curve",
            description="绘制正弦曲线",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_x": {"type": "number", "description": "起始x", "default": 0},
                    "end_x": {"type": "number", "description": "终止x", "default": 6.28}
                }
            }
        ),
        Tool(
            name="draw_cos_curve",
            description="绘制余弦曲线",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_x": {"type": "number", "description": "起始x", "default": 0},
                    "end_x": {"type": "number", "description": "终止x", "default": 6.28}
                }
            }
        ),
    ]

@app.list_resources()
async def list_resources() -> list[Resource]:
    logger.info("列出资源...")
    return [
        Resource(
            uri="geometry://shapes",
            name="几何图形绘制",
            mimeType="image/png",
            description="支持线段、三角形、矩形、多边形、梯形、圆、椭圆、正弦曲线、余弦曲线等"
        )
    ]

def draw_line(x1, y1, x2, y2):
    plt.figure()
    plt.plot([x1, x2], [y1, y2], marker='o')
    plt.title("Line")
    plt.axis('equal')
    return save_figure_to_base64()

def draw_triangle(points):
    pts = np.array(points + [points[0]])
    plt.figure()
    plt.plot(pts[:,0], pts[:,1], marker='o')
    plt.title("Triangle")
    plt.axis('equal')
    return save_figure_to_base64()

def draw_rectangle(x, y, width, height):
    rect = np.array([
        [x, y],
        [x+width, y],
        [x+width, y+height],
        [x, y+height],
        [x, y]
    ])
    plt.figure()
    plt.plot(rect[:,0], rect[:,1], marker='o')
    plt.title("Rectangle")
    plt.axis('equal')
    return save_figure_to_base64()

def draw_polygon(points):
    pts = np.array(points + [points[0]])
    plt.figure()
    plt.plot(pts[:,0], pts[:,1], marker='o')
    plt.title("Polygon")
    plt.axis('equal')
    return save_figure_to_base64()

def draw_trapezoid(points):
    pts = np.array(points + [points[0]])
    plt.figure()
    plt.plot(pts[:,0], pts[:,1], marker='o')
    plt.title("Trapezoid")
    plt.axis('equal')
    return save_figure_to_base64()

def draw_circle(center_x, center_y, radius):
    """绘制圆形并返回base64编码的PNG图片"""
    plt.figure(figsize=(8, 8))
    plt.clf()
    
    # 设置坐标轴范围
    margin = radius * 0.2
    plt.xlim(center_x - radius - margin, center_x + radius + margin)
    plt.ylim(center_y - radius - margin, center_y + radius + margin)
    
    # 绘制坐标轴
    plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    plt.axvline(x=0, color='gray', linestyle='-', alpha=0.3)
    plt.grid(True, alpha=0.3)
    
    # 生成圆的点
    theta = np.linspace(0, 2*np.pi, 100)
    x = center_x + radius * np.cos(theta)
    y = center_y + radius * np.sin(theta)
    
    # 绘制圆
    plt.plot(x, y, 'b-', linewidth=2)
    plt.title(f"Circle (center: {center_x}, {center_y}, radius: {radius})")
    plt.axis('equal')
    
    # 转换为base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', transparent=True)
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def draw_ellipse(center_x, center_y, width, height):
    theta = np.linspace(0, 2*np.pi, 100)
    x = center_x + width/2 * np.cos(theta)
    y = center_y + height/2 * np.sin(theta)
    plt.figure()
    plt.plot(x, y)
    plt.title("Ellipse")
    plt.axis('equal')
    return save_figure_to_base64()

def draw_sin_curve(start_x, end_x):
    x = np.linspace(start_x, end_x, 500)
    y = np.sin(x)
    plt.figure()
    plt.plot(x, y)
    plt.title("Sine Curve")
    plt.axis('equal')
    return save_figure_to_base64()

def draw_cos_curve(start_x, end_x):
    x = np.linspace(start_x, end_x, 500)
    y = np.cos(x)
    plt.figure()
    plt.plot(x, y)
    plt.title("Cosine Curve")
    plt.axis('equal')
    return save_figure_to_base64()

async def main():
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