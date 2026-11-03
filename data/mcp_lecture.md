# 第 8 讲：MCP 模型上下文协议

MCP（Model Context Protocol）是一种开放标准，让 AI 应用以统一方式接入外部数据和工具。

## 核心概念
MCP 采用客户端-服务端架构：
- **MCP Server**：暴露工具（tools）、资源（resources）和提示（prompts）。
- **MCP Client**：AI 应用（如 Agent）通过它发现并调用 Server 的能力。

## 传输方式
MCP 支持 stdio（本地子进程）和 HTTP/SSE（远程）两种传输。本地开发常用 stdio。

## 为什么用 MCP
把工具接口标准化后，Agent 无需为每个外部系统写适配代码；同一个 Server 可以被任意支持 MCP 的客户端复用。

## 本课程项目
我们把「课程表、作业、公告」封装成 MCP 课程 Server，Agent 通过 MCP 客户端挂载这些工具，即可回答『下周三有什么课』『作业截止时间』等结构化问题。