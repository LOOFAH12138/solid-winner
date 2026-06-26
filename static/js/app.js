/* ===== 主入口：导航与页面切换 ===== */
(function() {
    'use strict';

    // 页面名称到模块的映射
    const pages = {
        dashboard: { load: function() { Dashboard.load(); } },
        herbs: { load: function() { HerbsPage.load(); } },
        prescriptions: { load: function() { PrescriptionsPage.load(); } },
        pharmacology: { load: function() { PharmacologyPage.load(); } },
        components: { load: function() { ComponentsPage.load(); } },
        studies: { load: function() { StudiesPage.load(); } },
        diseases: { load: function() { DiseasesPage.load(); } },
        graph: { load: function() { GraphPage.load(); } },
        qa: { load: function() { QAPage.load(); } },
        import: { load: function() {} }
    };

    function switchPage(pageName) {
        // 导航高亮
        document.querySelectorAll('.nav-item').forEach(function(item) {
            item.classList.toggle('active', item.dataset.page === pageName);
        });
        // 页面切换
        document.querySelectorAll('.page').forEach(function(p) {
            p.classList.toggle('active', p.id === 'page-' + pageName);
        });
        // 加载数据
        if (pages[pageName] && pages[pageName].load) {
            pages[pageName].load();
        }
    }

    // 导航点击事件
    document.querySelectorAll('.nav-item').forEach(function(item) {
        item.addEventListener('click', function() {
            switchPage(this.dataset.page);
        });
    });

    // 初始化
    Modal.init();
    HerbsPage.init();
    PrescriptionsPage.init();
    PharmacologyPage.init();
    ComponentsPage.init();
    StudiesPage.init();
    DiseasesPage.init();
    GraphPage.init();
    QAPage.init();
    ImportPage.init();

    // 默认加载仪表盘
    switchPage('dashboard');
})();