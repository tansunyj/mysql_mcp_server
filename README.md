![Tests](https://github.com/designcomputer/mysql_mcp_server/actions/workflows/test.yml/badge.svg)
![PyPI - Downloads](https://img.shields.io/pypi/dm/mysql-mcp-server)
[![smithery badge](https://smithery.ai/badge/mysql-mcp-server)](https://smithery.ai/server/mysql-mcp-server)
[![MseeP.ai Security Assessment Badge](https://mseep.net/mseep-audited.png)](https://mseep.ai/app/designcomputer-mysql-mcp-server)
# MySQL MCP 服务

一个基于模型上下文协议(Model Context Protocol, MCP)的MySQL数据库交互服务。该服务允许AI助手安全地查询和操作MySQL数据库，通过结构化的接口进行数据库探索和分析。

## 功能特点

- 列出所有可用的MySQL数据库
- 查看指定数据库中的所有表
- 查看表结构
- 执行SQL查询并返回结果
- 在表中搜索包含特定关键字的数据
- 安全的数据库连接配置
- 详细的日志记录

## 安装

### 通过pip安装

```bash
pip install mysql-mcp-server
```

### 手动安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/mysql-mcp-server.git
cd mysql-mcp-server

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # 或在Windows上使用 venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

## 配置

通过环境变量配置MySQL连接信息：

```bash
MYSQL_HOST=localhost      # 数据库主机地址
MYSQL_PORT=3306          # 数据库端口（可选，默认为3306）
MYSQL_USER=your_username  # 数据库用户名
MYSQL_PASSWORD=your_password  # 数据库密码
MYSQL_DATABASE=your_database  # 要连接的数据库名
MYSQL_CHARSET=utf8mb4    # 字符集（可选，默认为utf8mb4）
MYSQL_COLLATION=utf8mb4_unicode_ci  # 排序规则（可选）
MYSQL_SQL_MODE=TRADITIONAL  # SQL模式（可选）
```

## 使用方法

### 与Claude Desktop集成

在`claude_desktop_config.json`中添加以下配置：

```json
{
  "mcpServers": {
    "mysql": {
      "command": "python",
      "args": ["path/to/mcp_mysql.py"],
      "env": {
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "your_username",
        "MYSQL_PASSWORD": "your_password",
        "MYSQL_DATABASE": "your_database"
      }
    }
  }
}
```

### 与Visual Studio Code集成

在`~/.cursor/mcp.json`中添加以下配置：

```json
{
  "servers": {
    "mysql": {
      "type": "stdio",
      "command": "python",
      "args": ["path/to/mcp_mysql.py"],
      "env": {
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "your_username",
        "MYSQL_PASSWORD": "your_password",
        "MYSQL_DATABASE": "your_database"
      }
    }
  }
}
```

### 直接运行（用于测试）

```bash
# 设置环境变量
export MYSQL_HOST=localhost
export MYSQL_USER=root
export MYSQL_PASSWORD=123456
export MYSQL_DATABASE=ai_content_db

# 运行服务
python mcp_mysql.py
```

## 可用工具

该MCP服务提供以下工具：

1. **query_mysql** - 执行SQL查询并返回结果
   - 参数: `sql` (字符串) - 要执行的SQL语句

2. **list_databases** - 查看MySQL服务器上的所有数据库
   - 无需参数

3. **list_tables** - 查看指定数据库的所有表
   - 参数: `database` (字符串) - 数据库名

4. **describe_table** - 查看指定表的结构
   - 参数: `database` (字符串) - 数据库名
   - 参数: `table` (字符串) - 表名

5. **search_table** - 在指定表的指定字段中搜索包含关键字的数据
   - 参数: `database` (字符串) - 数据库名
   - 参数: `table` (字符串) - 表名
   - 参数: `column` (字符串) - 字段名
   - 参数: `keyword` (字符串) - 关键字
   - 参数: `limit` (整数，可选) - 返回条数，默认20

## 示例查询

以下是一些可以通过AI助手使用的示例查询：

1. "列出所有可用的数据库"
2. "显示数据库 'ai_content_db' 中的所有表"
3. "描述表 'users' 的结构"
4. "在 'products' 表的 'name' 列中搜索包含 'phone' 的数据"
5. "执行SQL查询: SELECT * FROM orders WHERE total > 100 LIMIT 5"

## 安全建议

1. **创建专用数据库用户**：为此服务创建一个具有最小必要权限的专用MySQL用户
2. **避免使用root账户**：永远不要使用root或管理员账户连接数据库
3. **限制数据库访问**：只允许必要的操作权限
4. **启用日志记录**：为了审计目的，确保所有数据库操作都被记录
5. **定期安全审查**：定期检查数据库访问日志和权限设置

## 创建受限MySQL用户示例

```sql
-- 创建新用户
CREATE USER 'mcp_user'@'localhost' IDENTIFIED BY 'secure_password';

-- 只授予SELECT权限（只读访问）
GRANT SELECT ON your_database.* TO 'mcp_user'@'localhost';

-- 如果需要写入权限，可以有选择地授予
-- GRANT SELECT, INSERT, UPDATE ON your_database.* TO 'mcp_user'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;
```

## 开发

```bash
# 克隆仓库
git clone https://github.com/yourusername/mysql-mcp-server.git
cd mysql-mcp-server

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # 或在Windows上使用 venv\Scripts\activate

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest
```

## 许可证

MIT许可证 - 详情请参阅LICENSE文件。

## 贡献

1. Fork本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启一个Pull Request
