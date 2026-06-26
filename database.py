# -*- coding: utf-8 -*-
"""数据库初始化与连接管理 —— 含 Neo4j 知识图谱 & LLM 问答系统扩展"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tcm_data.db")


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """初始化数据库表结构"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        -- ==========================================
        -- 核心表 (从 CSV 导入)
        -- ==========================================
        CREATE TABLE IF NOT EXISTS herb (
            tcmbank_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            latin_name TEXT,
            category TEXT,
            nature TEXT,
            taste TEXT,
            meridian TEXT,
            pinyin_name TEXT,
            tcm_name_en TEXT,
            efficacy TEXT,
            toxicity TEXT,
            dosage TEXT,
            description TEXT,
            use_part TEXT,
            indication TEXT,
            therapeutic_cn_class TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS disease (
            cloud_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            description TEXT,
            tcm_syndrome TEXT,
            mesh_class TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS chemical_component (
            cloud_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            formula TEXT,
            cas_number TEXT,
            bioactivity TEXT,
            herb_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- ==========================================
        -- 新增: 方剂表
        -- ==========================================
        CREATE TABLE IF NOT EXISTS prescription (
            cloud_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            source TEXT,
            efficacy TEXT,
            category TEXT,
            indications TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- ==========================================
        -- 新增: 药理学表
        -- ==========================================
        CREATE TABLE IF NOT EXISTS pharmacology (
            cloud_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- ==========================================
        -- 关系表
        -- ==========================================

        -- Herb-Disease 关系表 (TREATS)
        CREATE TABLE IF NOT EXISTS herb_disease (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            herb_tcmbank_id TEXT NOT NULL,
            disease_cloud_id TEXT NOT NULL,
            relationship_type TEXT DEFAULT 'TREATS',
            indication TEXT,
            FOREIGN KEY (herb_tcmbank_id) REFERENCES herb(tcmbank_id),
            FOREIGN KEY (disease_cloud_id) REFERENCES disease(cloud_id)
        );

        -- Prescription-Herb 关系表 (CONTAINS_HERB)
        CREATE TABLE IF NOT EXISTS prescription_herb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id TEXT NOT NULL,
            herb_id TEXT NOT NULL,
            dosage TEXT,
            FOREIGN KEY (prescription_id) REFERENCES prescription(cloud_id),
            FOREIGN KEY (herb_id) REFERENCES herb(tcmbank_id)
        );

        -- Ingredient-Herb 关系表 (DERIVED_FROM)
        CREATE TABLE IF NOT EXISTS ingredient_herb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_id TEXT NOT NULL,
            herb_id TEXT NOT NULL,
            FOREIGN KEY (ingredient_id) REFERENCES chemical_component(cloud_id),
            FOREIGN KEY (herb_id) REFERENCES herb(tcmbank_id)
        );

        -- Herb-Pharmacology 关系表 (HAS_PHARMACOLOGY)
        CREATE TABLE IF NOT EXISTS herb_pharmacology (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            herb_id TEXT NOT NULL,
            pharmacology_id TEXT NOT NULL,
            FOREIGN KEY (herb_id) REFERENCES herb(tcmbank_id),
            FOREIGN KEY (pharmacology_id) REFERENCES pharmacology(cloud_id)
        );

        -- Ingredient-Pharmacology 关系表 (HAS_PHARMACOLOGY)
        CREATE TABLE IF NOT EXISTS ingredient_pharmacology (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_id TEXT NOT NULL,
            pharmacology_id TEXT NOT NULL,
            FOREIGN KEY (ingredient_id) REFERENCES chemical_component(cloud_id),
            FOREIGN KEY (pharmacology_id) REFERENCES pharmacology(cloud_id)
        );

        -- Prescription-Disease 关系表
        CREATE TABLE IF NOT EXISTS prescription_disease (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id TEXT NOT NULL,
            disease_id TEXT NOT NULL,
            relationship_type TEXT DEFAULT 'TREATS',
            evidence_level TEXT,
            FOREIGN KEY (prescription_id) REFERENCES prescription(cloud_id),
            FOREIGN KEY (disease_id) REFERENCES disease(cloud_id)
        );

        -- ==========================================
        -- LLM 知识库与 RAG 扩展
        -- ==========================================
        CREATE TABLE IF NOT EXISTS knowledge_chunk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            chunk_index INTEGER DEFAULT 0,
            source_type TEXT,
            source_id TEXT,
            entity_type TEXT,
            entity_id TEXT,
            embedding BLOB,
            embedding_model TEXT,
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS qa_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT,
            context_chunks TEXT,
            model_name TEXT,
            rating INTEGER,
            feedback TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- ==========================================
        -- 索引
        -- ==========================================
        CREATE INDEX IF NOT EXISTS idx_herb_name ON herb(name);
        CREATE INDEX IF NOT EXISTS idx_herb_nature ON herb(nature);
        CREATE INDEX IF NOT EXISTS idx_herb_taste ON herb(taste);
        CREATE INDEX IF NOT EXISTS idx_herb_meridian ON herb(meridian);
        CREATE INDEX IF NOT EXISTS idx_disease_name ON disease(name);
        CREATE INDEX IF NOT EXISTS idx_component_name ON chemical_component(name);
        CREATE INDEX IF NOT EXISTS idx_component_herb ON chemical_component(herb_id);
        CREATE INDEX IF NOT EXISTS idx_herb_disease_herb ON herb_disease(herb_tcmbank_id);
        CREATE INDEX IF NOT EXISTS idx_herb_disease_disease ON herb_disease(disease_cloud_id);
        CREATE INDEX IF NOT EXISTS idx_prescription_name ON prescription(name);
        CREATE INDEX IF NOT EXISTS idx_pharmacology_name ON pharmacology(name);
        CREATE INDEX IF NOT EXISTS idx_pres_herb_pres ON prescription_herb(prescription_id);
        CREATE INDEX IF NOT EXISTS idx_pres_herb_herb ON prescription_herb(herb_id);
        CREATE INDEX IF NOT EXISTS idx_ing_herb_ing ON ingredient_herb(ingredient_id);
        CREATE INDEX IF NOT EXISTS idx_ing_herb_herb ON ingredient_herb(herb_id);
        CREATE INDEX IF NOT EXISTS idx_herb_pharm_herb ON herb_pharmacology(herb_id);
        CREATE INDEX IF NOT EXISTS idx_ing_pharm_ing ON ingredient_pharmacology(ingredient_id);
        CREATE INDEX IF NOT EXISTS idx_chunk_entity ON knowledge_chunk(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_chunk_source ON knowledge_chunk(source_type, source_id);
        CREATE INDEX IF NOT EXISTS idx_qa_created ON qa_record(created_at);
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成: " + DB_PATH)
