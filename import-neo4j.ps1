# Neo4j 数据导入脚本 (Windows PowerShell)
# 用途：将 CSV 文件导入到 Neo4j Desktop 数据库

$ImportDir = ".\neo4j_import"
$Neo4jHome = $env:NEO4J_HOME

if (-not $Neo4jHome) {
    Write-Host "未设置 NEO4J_HOME 环境变量，尝试查找默认路径..."
    # 尝试常见的 Neo4j Desktop 路径
    $possiblePaths = @(
        "C:\Users\$env:USERNAME\.Neo4jDesktop2\data\databases",
        "C:\Program Files\Neo4j",
        "C:\Program Files (x86)\Neo4j"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $Neo4jHome = $path
            Write-Host "找到 Neo4j 目录: $Neo4jHome"
            break
        }
    }
}

if (-not $Neo4jHome) {
    Write-Host "错误：无法找到 Neo4j 目录"
    Write-Host "请设置 NEO4J_HOME 环境变量或手动指定路径"
    exit 1
}

# 复制 CSV 文件到 Neo4j import 目录
$Neo4jImportDir = Join-Path $Neo4jHome "import"
if (-not (Test-Path $Neo4jImportDir)) {
    New-Item -ItemType Directory -Path $Neo4jImportDir | Out-Null
    Write-Host "创建 import 目录: $Neo4jImportDir"
}

Write-Host "正在复制 CSV 文件到 $Neo4jImportDir..."
Copy-Item (Join-Path $ImportDir "nodes_Herb.csv") $Neo4jImportDir -Force
Copy-Item (Join-Path $ImportDir "nodes_Ingredient.csv") $Neo4jImportDir -Force
Copy-Item (Join-Path $ImportDir "nodes_Disease.csv") $Neo4jImportDir -Force
Copy-Item (Join-Path $ImportDir "edges_DERIVED_FROM.csv") $Neo4jImportDir -Force
Copy-Item (Join-Path $ImportDir "edges_TREATS.csv") $Neo4jImportDir -Force
Write-Host "文件复制完成"

Write-Host ""
Write-Host "================================================"
Write-Host "数据已复制到: $Neo4jImportDir"
Write-Host "================================================"
Write-Host ""
Write-Host "下一步操作："
Write-Host ""
Write-Host "方法1 - 使用 Neo4j Browser（推荐）："
Write-Host "1. 打开 Neo4j Desktop"
Write-Host "2. 启动您的数据库实例"
Write-Host "3. 点击 Manage -> Browser"
Write-Host "4. 在 Browser 中运行以下 Cypher 查询导入数据："
Write-Host ""
Write-Host "   CREATE CONSTRAINT herb_id IF NOT EXISTS FOR (n:Herb) REQUIRE n.id IS UNIQUE;"
Write-Host "   CREATE CONSTRAINT ingredient_id IF NOT EXISTS FOR (n:Ingredient) REQUIRE n.id IS UNIQUE;"
Write-Host "   CREATE CONSTRAINT disease_id IF NOT EXISTS FOR (n:Disease) REQUIRE n.id IS UNIQUE;"
Write-Host ""
Write-Host "   LOAD CSV WITH HEADERS FROM 'file:///nodes_Herb.csv' AS row MERGE (n:Herb {id: row.id}) SET n.name = row.name, n.latinName = row.latinName, n.category = row.category, n.nature = row.nature, n.flavor = row.flavor, n.meridian = row.meridian, n.pinyin = row.pinyin, n.englishName = row.englishName;"
Write-Host ""
Write-Host "   LOAD CSV WITH HEADERS FROM 'file:///nodes_Ingredient.csv' AS row MERGE (n:Ingredient {id: row.id}) SET n.name = row.name, n.molecularFormula = row.molecularFormula, n.casNumber = row.casNumber, n.bioactivity = row.bioactivity;"
Write-Host ""
Write-Host "   LOAD CSV WITH HEADERS FROM 'file:///nodes_Disease.csv' AS row MERGE (n:Disease {id: row.id}) SET n.name = row.name, n.category = row.category, n.meshClass = row.meshClass, n.tcmSyndrome = row.tcmSyndrome, n.description = row.description;"
Write-Host ""
Write-Host "   LOAD CSV WITH HEADERS FROM 'file:///edges_DERIVED_FROM.csv' AS row MATCH (ing:Ingredient {id: row.':START_ID(Ingredient)'[:19]}), (h:Herb {id: row.':END_ID(Herb)'[:22]}) CREATE (ing)-[:DERIVED_FROM]->(h);"
Write-Host ""
Write-Host "   LOAD CSV WITH HEADERS FROM 'file:///edges_TREATS.csv' AS row MATCH (h:Herb {id: row.':START_ID(Herb)'[:22]}), (d:Disease {id: row.':END_ID(Disease)'[:19]}) CREATE (h)-[:TREATS {indication: row.indication}]->(d);"
Write-Host ""
Write-Host "方法2 - 使用 Python 脚本导入："
Write-Host "运行: python import-csv-to-neo4j.py"
Write-Host ""
Write-Host "提示：如果您的 Neo4j 实例名不同，请修改上面的路径和查询"
