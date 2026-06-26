# -*- coding: utf-8 -*-
from services.knowledge_service import KnowledgeService

chunks = KnowledgeService.search_chunks_extended('金银花', limit=5)
for i, c in enumerate(chunks):
    print(f"{i+1}. [{c['entity_type']:20}] {c['title']}")
    print(f"   完整内容({len(c['content'])}字):")
    print(c['content'])
    print()
