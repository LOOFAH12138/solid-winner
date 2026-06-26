# -*- coding: utf-8 -*-
"""测试 Agent 工作链式 QA 系统"""
import sys
sys.path.insert(0, '.')

from services.agent_qa import AgentQA

# 测试问题
test_questions = [
    "金银花有什么功效？",
    "人参可以治疗哪些疾病？",
    "黄连的主要化学成分是什么？",
]

for question in test_questions:
    print("\n" + "=" * 80)
    result = AgentQA.chat(question)
    print("\n最终回答:")
    print("-" * 60)
    print(result["answer"])
    print("-" * 60)
    print(f"\n本地结果数: {result['local_results_count']}")
    print(f"图谱结果数: {result['graph_results_count']}")
    print("=" * 80 + "\n")
