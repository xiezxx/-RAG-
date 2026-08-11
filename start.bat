@echo off
REM 劳动法 RAG 智能咨询系统 — 一键启动脚本（RAG 检索引擎）
chcp 65001 >nul

echo.
echo ╔══════════════════════════════════════════╗
echo ║   ⚖️  劳动法 RAG 智能咨询系统           ║
echo ╚══════════════════════════════════════════╝
echo.

REM 1. 检查 Neo4j 是否在运行
echo [1/3] 检查 Neo4j 连接 ...
curl -s http://localhost:7474 >nul 2>&1
if %errorlevel% neq 0 (
    echo   ⚠️  Neo4j 未运行！请先启动 Neo4j:
    echo      打开新的 cmd 窗口执行:
    echo      set JAVA_HOME=D:\jdk21
    echo      cd /d "D:\My wordl four\neo4j-community-2026.06.0"
    echo      bin\neo4j console
    echo.
    echo   启动成功后，再运行本脚本。
    pause
    exit /b 1
)
echo   ✅ Neo4j 已连接

REM 2. 激活虚拟环境
echo [2/3] 激活虚拟环境 ...
call .venv\Scripts\activate.bat

REM 2.5 设置 Python 路径
set PYTHONPATH=%~dp0

REM 3. 启动 RAG 检索引擎（FastAPI，端口 8001）
echo [3/3] 启动 RAG 检索引擎（端口 8001）...
echo.
echo   启动成功后，请另开窗口启动:
echo     · Spring Boot 后端  →  mvn spring-boot:run （目录 spring-boot-backend）
echo     · Vue 前端          →  npm run serve    （目录 vue-frontend）
echo.
python src\rag_service.py

pause
