# 第 5 讲：Agent 智能体与工具调用

Agent（智能体）是能自主规划、调用工具、迭代解决问题的 AI 程序。

## 什么是 Agent
Agent 与普通对话模型的关键区别在于：Agent 可以在多轮中主动决定要不要调用工具，并根据工具返回结果继续推理，直到完成目标。

## ReAct 范式
ReAct（Reasoning + Acting）是 Agent 的经典实现：模型先「思考（Reason）」下一步该做什么，再「行动（Act）」——调用工具或直接回答，循环往复。

## Agent 的工具来源
- 自定义 Python 函数（登录号、计算等）。
- RAG 检索工具（从知识库取内容）。
- MCP 工具（通过标准协议接入的外部能力）。
Agent 通过挂载这些工具获得执行能力，工具列表在运行时决定模型的可用动作集合。

## 常见框架
LangGraph、AutoGen、CrewAI。本课程以 LangGraph 的 ReAct Agent 为主要工具。