#!/usr/bin/env python3

import asyncio
import logging
import os
import sys
from mysql.connector import connect, Error
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import signal
import time

# 配置更详细的日志
logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG级别，显示更多信息
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # 确保日志输出到标准输出
    ]
)
logger = logging.getLogger("mysql-service")

# 启动时记录Python版本和工作目录
logger.info(f"Python版本: {sys.version}")
logger.info(f"当前工作目录: {os.getcwd()}")
logger.info(f"脚本路径: {__file__}")

# Initialize MCP server
logger.info("初始化MCP服务器: mysql-service")
app = Server("mysql-service")


def get_db_config():
    """Get database configuration from environment variables."""
    config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "123456"),
        "database": os.getenv("MYSQL_DATABASE", "ai_content_db"),
        # Add charset and collation to avoid utf8mb4_0900_ai_ci issues with older MySQL versions
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
        "collation": os.getenv("MYSQL_COLLATION", "utf8mb4_unicode_ci"),
        # Disable autocommit for better transaction control
        "autocommit": True,
        # Set SQL mode for better compatibility - can be overridden
        "sql_mode": os.getenv("MYSQL_SQL_MODE", "TRADITIONAL")
    }

    # Remove None values to let MySQL connector use defaults if not specified
    config = {k: v for k, v in config.items() if v is not None}

    # 记录实际使用的配置（密码隐藏）
    safe_config = config.copy()
    if "password" in safe_config:
        safe_config["password"] = "******"  # 隐藏密码
    logger.info(f"MySQL配置: {safe_config}")

    return config


def get_mysql_connection():
    """获取本地MySQL连接"""
    config = get_db_config()
    logger.debug(f"尝试连接MySQL: {config['host']}:{config['port']}")
    try:
        conn = connect(**config)
        logger.debug(f"MySQL连接成功，服务器版本: {conn.get_server_info()}")
        return conn
    except Error as e:
        logger.error(f"MySQL连接失败: {str(e)}")
        logger.error(f"错误代码: {e.errno}, SQL状态: {e.sqlstate}")
        raise


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """执行MySQL工具。"""
    logger.info(f"调用工具: {name}, 参数: {arguments}")

    if name == "query_mysql":
        sql = arguments.get("sql")
        if not sql:
            return [TextContent(type="text", text="SQL查询语句是必需的")]

        result = await query_mysql(sql)
        return [TextContent(type="text", text=str(result))]

    elif name == "list_databases":
        result = await list_databases()
        return [TextContent(type="text", text=str(result))]

    elif name == "list_tables":
        database = arguments.get("database")
        if not database:
            return [TextContent(type="text", text="数据库名是必需的")]

        result = await list_tables(database)
        return [TextContent(type="text", text=str(result))]

    elif name == "describe_table":
        database = arguments.get("database")
        table = arguments.get("table")
        if not database or not table:
            return [TextContent(type="text", text="数据库名和表名都是必需的")]

        result = await describe_table(database, table)
        return [TextContent(type="text", text=str(result))]

    elif name == "search_table":
        database = arguments.get("database")
        table = arguments.get("table")
        column = arguments.get("column")
        keyword = arguments.get("keyword")
        limit = arguments.get("limit", 20)

        if not all([database, table, column, keyword]):
            return [TextContent(type="text", text="数据库名、表名、字段名和关键字都是必需的")]

        result = await search_table(database, table, column, keyword, limit)
        return [TextContent(type="text", text=str(result))]

    else:
        return [TextContent(type="text", text=f"未知工具: {name}")]


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用的MySQL工具。"""
    logger.info("列出工具...")
    return [
        Tool(
            name="query_mysql",
            description="执行SQL查询并返回结果",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "要执行的SQL语句（建议只支持SELECT）"
                    }
                },
                "required": ["sql"]
            }
        ),
        Tool(
            name="list_databases",
            description="查看MySQL服务器上的所有数据库",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_tables",
            description="查看指定数据库的所有表",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "数据库名"
                    }
                },
                "required": ["database"]
            }
        ),
        Tool(
            name="describe_table",
            description="查看指定表的结构",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "数据库名"
                    },
                    "table": {
                        "type": "string",
                        "description": "表名"
                    }
                },
                "required": ["database", "table"]
            }
        ),
        Tool(
            name="search_table",
            description="在指定表的指定字段中搜索包含关键字的数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "数据库名"
                    },
                    "table": {
                        "type": "string",
                        "description": "表名"
                    },
                    "column": {
                        "type": "string",
                        "description": "字段名"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "关键字"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回条数，默认20",
                        "default": 20
                    }
                },
                "required": ["database", "table", "column", "keyword"]
            }
        )
    ]


@app.list_resources()
async def list_resources() -> list[Resource]:
    """列出MySQL表作为资源。"""
    logger.info("列出资源...")
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()

            resources = []
            for db in databases:
                db_name = db[0]
                resources.append(
                    Resource(
                        uri=f"mysql://{db_name}",
                        name=f"数据库: {db_name}",
                        mimeType="text/plain",
                        description=f"数据库: {db_name}"
                    )
                )
            return resources
    except Error as e:
        logger.error(f"列出资源失败: {str(e)}")
        logger.error(f"错误代码: {e.errno}, SQL状态: {e.sqlstate}")
        return []


async def query_mysql(sql: str) -> dict:
    """
    执行SQL查询并返回结果

    Args:
        sql: 要执行的SQL语句（建议只支持SELECT）

    Returns:
        查询结果字典
    """

    logger.info(f"执行SQL: {sql}")
    try:
        conn = get_mysql_connection()
        with conn.cursor(dictionary=True) as cursor:
            logger.debug(f"执行查询: {sql}")
            cursor.execute(sql)

            # 如果是SELECT等返回结果集的查询
            if cursor.description:
                result = cursor.fetchall()
                logger.debug(f"查询结果: {len(result)}行")
                return {"status": "succeed", "data": result}
            # 非SELECT查询（如INSERT, UPDATE, DELETE）
            else:
                conn.commit()
                return {"status": "succeed", "affected_rows": cursor.rowcount}
    except Error as e:
        logger.error(f"MySQL查询出错: {str(e)}")
        logger.error(f"错误代码: {e.errno}, SQL状态: {e.sqlstate}")
        return {"status": "error", "error": str(e)}
    finally:
        if 'conn' in locals() and conn:
            conn.close()


async def list_databases() -> dict:
    """
    查看MySQL服务器上的所有数据库
    Returns:
        数据库列表
    """
    logger.info("列出所有数据库")
    try:
        conn = get_mysql_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SHOW DATABASES")
            result = [row['Database'] for row in cursor.fetchall()]
        conn.close()
        return {"status": "succeed", "databases": result}
    except Error as e:
        logger.error(f"列数据库出错: {str(e)}")
        logger.error(f"错误代码: {e.errno}, SQL状态: {e.sqlstate}")
        return {"status": "error", "error": str(e)}


async def list_tables(database: str) -> dict:
    """
    查看指定数据库的所有表
    Args:
        database: 数据库名
    Returns:
        表名列表
    """
    logger.info(f"列出数据库 {database} 的所有表")
    try:
        conn = get_mysql_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(f"USE `{database}`")
            cursor.execute("SHOW TABLES")
            tables_key = f"Tables_in_{database}"
            result = [row[tables_key] for row in cursor.fetchall()]
        conn.close()
        return {"status": "succeed", "tables": result}
    except Error as e:
        logger.error(f"列表出错: {str(e)}")
        logger.error(f"错误代码: {e.errno}, SQL状态: {e.sqlstate}")
        return {"status": "error", "error": str(e)}


async def describe_table(database: str, table: str) -> dict:
    """
    查看指定表的结构
    Args:
        database: 数据库名
        table: 表名
    Returns:
        表结构信息
    """
    logger.info(f"查看表结构: {database}.{table}")
    try:
        conn = get_mysql_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(f"USE `{database}`")
            cursor.execute(f"DESCRIBE `{table}`")
            result = cursor.fetchall()
        conn.close()
        return {"status": "succeed", "structure": result}
    except Error as e:
        logger.error(f"查表结构出错: {str(e)}")
        logger.error(f"错误代码: {e.errno}, SQL状态: {e.sqlstate}")
        return {"status": "error", "error": str(e)}


async def search_table(database: str, table: str, column: str, keyword: str, limit: int = 20) -> dict:
    """
    在指定表的指定字段中搜索包含关键字的数据
    Args:
        database: 数据库名
        table: 表名
        column: 字段名
        keyword: 关键字
        limit: 返回条数，默认20
    Returns:
        匹配数据列表
    """
    logger.info(f"在 {database}.{table}.{column} 搜索: {keyword}")
    try:
        conn = get_mysql_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(f"USE `{database}`")
            sql = f"SELECT * FROM `{table}` WHERE `{column}` LIKE %s LIMIT %s"
            cursor.execute(sql, (f"%{keyword}%", limit))
            result = cursor.fetchall()
        conn.close()
        return {"status": "succeed", "data": result}
    except Error as e:
        logger.error(f"搜索数据出错: {str(e)}")
        logger.error(f"错误代码: {e.errno}, SQL状态: {e.sqlstate}")
        return {"status": "error", "error": str(e)}


async def main():
    """主入口点，运行MCP服务器"""
    # 导入stdio_server
    from mcp.server.stdio import stdio_server

    try:
        logger.info("启动本地MySQL MCP服务")

        # 测试数据库连接
        try:
            conn = get_mysql_connection()
            logger.info(f"数据库连接测试成功，服务器版本: {conn.get_server_info()}")
            conn.close()
        except Exception as e:
            logger.error(f"数据库连接测试失败: {str(e)}")
            # 继续执行，因为可能是环境变量未设置

        # 打印配置信息到标准错误输出
        config = get_db_config()
        print("Starting MySQL MCP server with config:", file=sys.stderr)
        print(f"Host: {config.get('host')}", file=sys.stderr)
        print(f"Port: {config.get('port')}", file=sys.stderr)
        print(f"User: {config.get('user')}", file=sys.stderr)
        print(f"Database: {config.get('database')}", file=sys.stderr)
        print(f"Charset: {config.get('charset')}", file=sys.stderr)

        logger.info("启动MCP服务...")

        # 打印MCP版本信息
        try:
            import mcp
            logger.info(f"MCP版本: {getattr(mcp, '__version__', '未知')}")
        except Exception as e:
            logger.warning(f"无法获取MCP版本: {str(e)}")

        # 显式设置transport参数并添加详细日志
        logger.info("设置MCP运行参数: transport=stdio")

        # 添加信号处理，确保可以正常退出
        def signal_handler(sig, frame):
            logger.info(f"收到信号 {sig}，准备退出...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        logger.info("注册信号处理器，按Ctrl+C可正常退出")

        # 确保输出缓冲区刷新
        sys.stdout.flush()
        sys.stderr.flush()

        logger.info("MCP服务即将启动并进入监听状态...")

        # 使用与server.py相同的方式启动服务
        async with stdio_server() as (read_stream, write_stream):
            try:
                # 使用Server的run方法
                await app.run(
                    read_stream,
                    write_stream,
                    app.create_initialization_options()
                )
            except Exception as e:
                logger.error(f"服务器错误: {str(e)}", exc_info=True)
                raise

    except Exception as e:
        logger.critical(f"MCP服务启动失败: {str(e)}", exc_info=True)
        raise


if __name__ == '__main__':
    try:
        # 使用asyncio.run启动异步主函数
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("收到键盘中断，程序退出")
    except Exception as e:
        logger.critical(f"MCP服务启动失败: {str(e)}", exc_info=True)
        sys.exit(1)
