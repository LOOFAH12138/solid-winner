# -*- coding: utf-8 -*-
"""种子数据脚本 —— 运行此脚本向数据库插入示例数据"""
from database import init_db, get_db


def seed():
    init_db()
    conn = get_db()

    # 检查是否已有数据
    existing = conn.execute("SELECT COUNT(*) FROM herb").fetchone()[0]
    if existing > 0:
        print("数据库已有数据，跳过种子数据插入。")
        conn.close()
        return

    # ====== 药材 ======
    herbs = [
        # (name, latin_name, category, nature, taste, meridian, efficacy, toxicity, dosage, description,
        #  tcmbank_id, level1_name_en, pinyin_name, tcm_name_en, use_part, indication,
        #  clinical_manifestations, therapeutic_en_class, therapeutic_cn_class,
        #  tcmid_id, tcm_id_id, symmap_id, tcmsp_id, herb_external_id)
        ("人参", "Panax ginseng C.A.Mey.", "补气药", "温", "甘,微苦", "脾,肺,心",
         "大补元气，复脉固脱，补脾益肺，生津养血", "无毒", "3~9g，另煎兑服",
         "五加科植物人参的干燥根和根茎，主产于吉林、辽宁等地。",
         "HB0001", "Qi-tonifying herbs", "Ren Shen", "Ginseng", "根及根茎",
         "气虚欲脱，脉微欲绝，脾虚食少，肺虚喘咳，津伤口渴，内热消渴，久病虚羸，惊悸失眠",
         "体虚乏力，面色萎黄，气短自汗", "Qi-Tonifying", "补气药",
         "TCMID_001", "TCM_ID_001", "SYMMAP_001", "TCMSP_001", "HERB_001"),
        ("黄芪", "Astragalus membranaceus (Fisch.) Bge.", "补气药", "温", "甘", "脾,肺",
         "补气升阳，固表止汗，利水消肿，生津养血", "无毒", "9~30g",
         "豆科植物蒙古黄芪或膜荚黄芪的干燥根。",
         "HB0002", "Qi-tonifying herbs", "Huang Qi", "Astragalus", "根",
         "脾胃气虚，中气下陷，表虚自汗，气虚水肿，疮疡难溃", "神疲乏力，自汗，少气懒言",
         "Qi-Tonifying", "补气药",
         "TCMID_002", "TCM_ID_002", "SYMMAP_002", "TCMSP_002", "HERB_002"),
        ("当归", "Angelica sinensis (Oliv.) Diels", "补血药", "温", "甘,辛", "肝,心,脾",
         "补血活血，调经止痛，润肠通便", "无毒", "6~12g",
         "伞形科植物当归的干燥根，主产于甘肃岷县。",
         "HB0003", "Blood-tonifying herbs", "Dang Gui", "Chinese Angelica", "根",
         "血虚萎黄，眩晕心悸，月经不调，经闭痛经，虚寒腹痛，肠燥便秘",
         "面色无华，头晕心悸，月经量少色淡", "Blood-Tonifying", "补血药",
         "TCMID_003", "TCM_ID_003", "SYMMAP_003", "TCMSP_003", "HERB_003"),
        ("甘草", "Glycyrrhiza uralensis Fisch.", "补气药", "平", "甘", "心,肺,脾,胃",
         "补脾益气，清热解毒，祛痰止咳，缓急止痛，调和诸药", "无毒", "2~10g",
         "豆科植物甘草的干燥根和根茎，有'国老'之称。",
         "HB0004", "Qi-tonifying herbs", "Gan Cao", "Licorice", "根及根茎",
         "脾胃虚弱，倦怠乏力，心悸气短，咳嗽痰多，脘腹四肢挛急疼痛，痈肿疮毒",
         "倦怠乏力，咳嗽痰多", "Qi-Tonifying; Heat-Clearing", "补气药; 清热解毒药",
         "TCMID_004", "TCM_ID_004", "SYMMAP_004", "TCMSP_004", "HERB_004"),
        ("黄连", "Coptis chinensis Franch.", "清热药", "寒", "苦", "心,脾,胃,肝,胆,大肠",
         "清热燥湿，泻火解毒", "无毒", "2~5g",
         "毛茛科植物黄连的干燥根茎，主产于四川。",
         "HB0005", "Heat-clearing herbs", "Huang Lian", "Coptis", "根茎",
         "湿热痞满，呕吐吞酸，泻痢，黄疸，高热神昏，心火亢盛，心烦不寐",
         "口苦口臭，脘腹痞满，舌苔黄腻", "Heat-Clearing", "清热药",
         "TCMID_005", "TCM_ID_005", "SYMMAP_005", "TCMSP_005", "HERB_005"),
        ("黄芩", "Scutellaria baicalensis Georgi", "清热药", "寒", "苦", "肺,胆,脾,大肠,小肠",
         "清热燥湿，泻火解毒，止血，安胎", "无毒", "3~10g",
         "唇形科植物黄芩的干燥根。",
         "HB0006", "Heat-clearing herbs", "Huang Qin", "Scutellaria", "根",
         "湿温暑湿，胸闷呕恶，湿热痞满，泻痢，黄疸，肺热咳嗽，高热烦渴",
         "发热口渴，咳嗽痰黄，舌红苔黄", "Heat-Clearing", "清热药",
         "TCMID_006", "TCM_ID_006", "SYMMAP_006", "TCMSP_006", "HERB_006"),
        ("半夏", "Pinellia ternata (Thunb.) Breit.", "化痰药", "温", "辛", "脾,胃,肺",
         "燥湿化痰，降逆止呕，消痞散结", "有毒", "3~9g，炮制后使用",
         "天南星科植物半夏的干燥块茎，生品有毒。",
         "HB0007", "Phlegm-resolving herbs", "Ban Xia", "Pinellia", "块茎",
         "痰多咳喘，痰饮眩悸，风痰眩晕，胃气上逆，恶心呕吐，胸脘痞闷",
         "恶心呕吐，咳嗽痰多", "Phlegm-Resolving", "化痰药",
         "TCMID_007", "TCM_ID_007", "SYMMAP_007", "TCMSP_007", "HERB_007"),
        ("茯苓", "Poria cocos (Schw.) Wolf", "利水渗湿药", "平", "甘,淡", "心,肺,脾,肾",
         "利水渗湿，健脾，宁心", "无毒", "10~15g",
         "多孔菌科真菌茯苓的干燥菌核。",
         "HB0008", "Damp-draining herbs", "Fu Ling", "Poria", "菌核",
         "水肿尿少，痰饮眩悸，脾虚食少，便溏泄泻，心神不安，惊悸失眠",
         "水肿，小便不利，脾虚泄泻", "Damp-Draining", "利水渗湿药",
         "TCMID_008", "TCM_ID_008", "SYMMAP_008", "TCMSP_008", "HERB_008"),
        ("桂枝", "Cinnamomum cassia Presl", "解表药", "温", "辛,甘", "心,肺,膀胱",
         "发汗解肌，温通经脉，助阳化气", "无毒", "3~10g",
         "樟科植物肉桂的干燥嫩枝。",
         "HB0009", "Exterior-releasing herbs", "Gui Zhi", "Cinnamon Twig", "嫩枝",
         "风寒感冒，脘腹冷痛，血寒经闭，关节痹痛，水肿，心悸", "恶寒发热，头痛身痛，关节疼痛",
         "Exterior-Releasing", "解表药",
         "TCMID_009", "TCM_ID_009", "SYMMAP_009", "TCMSP_009", "HERB_009"),
        ("陈皮", "Citrus reticulata Blanco", "理气药", "温", "辛,苦", "脾,肺",
         "理气健脾，燥湿化痰", "无毒", "3~10g",
         "芸香科植物橘的干燥成熟果皮，以陈久者为佳。",
         "HB0010", "Qi-regulating herbs", "Chen Pi", "Tangerine Peel", "果皮",
         "脘腹胀满，食少吐泻，咳嗽痰多", "脘腹胀满，嗳气，纳差",
         "Qi-Regulating", "理气药",
         "TCMID_010", "TCM_ID_010", "SYMMAP_010", "TCMSP_010", "HERB_010"),
    ]

    cur = conn.executemany(
        "INSERT INTO herb (name, latin_name, category, nature, taste, meridian, efficacy, toxicity, dosage, description,"
        " tcmbank_id, level1_name_en, pinyin_name, tcm_name_en, use_part, indication,"
        " clinical_manifestations, therapeutic_en_class, therapeutic_cn_class,"
        " tcmid_id, tcm_id_id, symmap_id, tcmsp_id, herb_external_id)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        herbs
    )

    # ====== 方剂 ======
    prescriptions = [
        ("四君子汤", "补气剂", "益气健脾", "脾胃气虚证", "《太平惠民和剂局方》", "治疗脾胃气虚的基础方。"),
        ("四物汤", "补血剂", "补血调血", "营血虚滞证", "《太平惠民和剂局方》", "治疗血虚证的基础方。"),
        ("半夏泻心汤", "和解剂", "寒热平调，消痞散结", "寒热互结之痞证", "《伤寒论》", "辛开苦降法的代表方。"),
        ("桂枝汤", "解表剂", "解肌发表，调和营卫", "外感风寒表虚证", "《伤寒论》", "群方之冠，调和营卫的代表方。"),
        ("黄连解毒汤", "清热剂", "泻火解毒", "三焦火毒证", "《外台秘要》", "清热解毒的代表方。"),
    ]

    for p in prescriptions:
        conn.execute(
            "INSERT INTO prescription (name, category, efficacy, indications, source, description) VALUES (?, ?, ?, ?, ?, ?)",
            p
        )

    # 方剂-药材关联
    pres_herb_links = [
        (1, 1, "9g"), (1, 2, "9g"), (1, 4, "6g"), (1, 8, "9g"),  # 四君子汤: 人参 黄芪 甘草 茯苓
        (2, 3, "12g"), (2, 1, "9g"), (2, 4, "6g"),  # 四物汤简化: 当归 人参 甘草
        (3, 5, "3g"), (3, 7, "9g"), (3, 6, "9g"), (3, 4, "6g"),  # 半夏泻心汤: 黄连 半夏 黄芩 甘草
        (4, 9, "9g"), (4, 4, "6g"),  # 桂枝汤简化: 桂枝 甘草
        (5, 5, "5g"), (5, 6, "10g"), (5, 4, "6g"),  # 黄连解毒汤: 黄连 黄芩 甘草
    ]

    for ph in pres_herb_links:
        conn.execute(
            "INSERT INTO prescription_herb (prescription_id, herb_id, dosage) VALUES (?, ?, ?)",
            ph
        )

    # ====== 化学成分 ======
    components = [
        ("人参皂苷Rb1", "C54H92O23", "41753-43-9", 1, "抗氧化、抗衰老、神经保护"),
        ("人参皂苷Rg1", "C42H72O14", "22427-39-0", 1, "免疫调节、改善记忆"),
        ("黄芪甲苷", "C41H68O14", "83207-58-3", 2, "免疫增强、抗炎"),
        ("阿魏酸", "C10H10O4", "1135-24-6", 3, "抗氧化、抗血栓"),
        ("甘草酸", "C42H62O16", "1405-86-3", 4, "抗炎、保肝、抗病毒"),
        ("小檗碱", "C20H18NO4", "2086-83-1", 5, "抗菌、抗炎、降糖"),
        ("黄芩苷", "C21H18O11", "21967-41-9", 6, "抗炎、抗氧化"),
        ("茯苓多糖", "C6H10O5)n", "", 8, "免疫调节、抗肿瘤"),
        ("桂皮醛", "C9H8O", "104-55-2", 9, "解热镇痛、抗菌"),
        ("橙皮苷", "C28H34O15", "520-26-3", 10, "抗氧化、改善血管功能"),
    ]

    for c in components:
        conn.execute(
            "INSERT INTO chemical_component (name, formula, cas_number, herb_id, bioactivity) VALUES (?, ?, ?, ?, ?)",
            c
        )

    # ====== 药理研究 ======
    studies = [
        ("人参皂苷Rg1对阿尔茨海默病模型小鼠认知功能的影响", 1, 2, "改善认知功能", "通过调节胆碱能系统和减轻氧化应激", "J Ethnopharmacol. 2018;220:147-156", "研究显示人参皂苷Rg1可显著改善AD模型小鼠的学习记忆能力。"),
        ("黄芪甲苷对心肌缺血再灌注损伤的保护作用", 2, 3, "心肌保护", "通过激活PI3K/Akt信号通路抑制细胞凋亡", "Front Pharmacol. 2019;10:1234", "黄芪甲苷预处理可减少心肌梗死面积，减轻炎症反应。"),
        ("小檗碱对2型糖尿病大鼠胰岛素抵抗的改善作用", 5, 6, "降糖", "激活AMPK信号通路，改善胰岛素敏感性", "Metabolism. 2017;69:51-63", "小檗碱显著降低空腹血糖和糖化血红蛋白水平。"),
        ("黄芩苷对脂多糖诱导的急性肺损伤的保护机制", 6, 7, "抗炎", "抑制NF-kB通路和NLRP3炎症小体活化", "Int Immunopharmacol. 2020;80:106194", "黄芩苷可减轻肺组织病理损伤和炎症细胞浸润。"),
        ("茯苓多糖的抗肿瘤免疫调节机制研究", 8, 8, "抗肿瘤、免疫调节", "激活巨噬细胞和NK细胞，促进细胞因子分泌", "Carbohydr Polym. 2018;197:539-547", "茯苓多糖能增强机体免疫功能，抑制肿瘤生长。"),
    ]

    for s in studies:
        conn.execute(
            "INSERT INTO pharma_study (title, herb_id, component_id, effect, mechanism, reference, summary) VALUES (?, ?, ?, ?, ?, ?, ?)",
            s
        )

    # ====== 病症 ======
    diseases = [
        ("消渴", "内科", "以多饮、多食、多尿、消瘦为特征的病证，相当于现代医学的糖尿病", "阴虚燥热"),
        ("胸痹", "内科", "以胸部闷痛为主症的疾病，相当于冠心病", "心脉痹阻"),
        ("不寐", "内科", "以经常不能获得正常睡眠为特征的病证", "心神失养"),
        ("胃脘痛", "内科", "以胃脘部疼痛为主症的病证", "脾胃不和"),
        ("咳嗽", "内科", "肺失宣降，肺气上逆作声的病证", "肺气失宣"),
        ("泄泻", "内科", "以排便次数增多、粪质稀薄为特征的病证", "脾虚湿盛"),
        ("血虚证", "内科", "血液亏虚，脏腑经络失养的证候", "营血亏虚"),
        ("气虚证", "内科", "元气不足，脏腑功能减退的证候", "元气亏虚"),
    ]

    for d in diseases:
        conn.execute(
            "INSERT INTO disease (name, category, description, tcm_syndrome) VALUES (?, ?, ?, ?)",
            d
        )

    # 药材-病症关联
    herb_disease_links = [
        (5, 1, "TREATS", "临床研究"),  # 黄连-消渴
        (5, 4, "TREATS", "临床研究"),  # 黄连-胃脘痛
        (6, 6, "TREATS", "临床研究"),  # 黄芩-泄泻
        (1, 8, "TREATS", "经典"),      # 人参-气虚
        (2, 8, "TREATS", "经典"),      # 黄芪-气虚
        (3, 7, "TREATS", "经典"),      # 当归-血虚
        (4, 8, "TREATS", "经典"),      # 甘草-气虚
        (9, 2, "TREATS", "经典"),      # 桂枝-胸痹
        (8, 8, "TREATS", "经典"),      # 茯苓-气虚
        (1, 7, "TREATS", "经典"),      # 人参-血虚
    ]

    for hd in herb_disease_links:
        conn.execute(
            "INSERT INTO herb_disease (herb_id, disease_id, relationship_type, evidence_level) VALUES (?, ?, ?, ?)",
            hd
        )

    # 方剂-病症关联
    pres_disease_links = [
        (1, 8, "TREATS", "经典"),      # 四君子汤-气虚
        (2, 7, "TREATS", "经典"),      # 四物汤-血虚
        (3, 4, "TREATS", "经典"),      # 半夏泻心汤-胃脘痛
        (4, 5, "TREATS", "经典"),      # 桂枝汤-咳嗽（外感）
        (5, 6, "TREATS", "经典"),      # 黄连解毒汤-泄泻
    ]

    for pd in pres_disease_links:
        conn.execute(
            "INSERT INTO prescription_disease (prescription_id, disease_id, relationship_type, evidence_level) VALUES (?, ?, ?, ?)",
            pd
        )

    conn.commit()
    conn.close()
    print("种子数据插入完成！共插入 {} 味药材、{} 首方剂、{} 个成分、{} 项研究、{} 个病症。".format(
        len(herbs), len(prescriptions), len(components), len(studies), len(diseases)
    ))


if __name__ == "__main__":
    seed()