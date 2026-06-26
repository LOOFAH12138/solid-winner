# -*- coding: utf-8 -*-
"""测试 QA 流程：检查知识块是否被正确构建并传给 AI"""
from services.knowledge_service import KnowledgeService, QAService
import json

query = "金银花"
print(f"查询: {query}\n")

# 1. 检查是否搜索到知识块
chunks = KnowledgeService.search_chunks_extended(query, limit=5)
print(f"搜索到 {len(chunks)} 个知识块:\n")
for i, c in enumerate(chunks):
    print(f"  {i+1}. [{c['entity_type']:20}] {c['title']}")
    print(f"     内容: {c['content'][:150]}...")
    print()

# 2. 模拟 chat 调用，打印发送给 AI 的消息
if chunks:
    knowledge_text = "\n\n---\n\n".join([
        f"【{c['title']}】(类型:{c.get('entity_type','未知')})\n{c['content'][:800]}"
        for c in chunks
    ])
    user_message = f"请严格根据以下【知识库内容】回答问题。\n\n【知识库内容】：\n{knowledge_text}\n\n用户问题：{query}"
    
    print("=" * 80)
    print("发送给 AI 的 user_message（前 2000 字符）:")
    print("=" * 80)
    print(user_message[:2000])
    print(f"\n... (总长度: {len(user_message)} 字符)")
