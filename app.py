# -*- coding: utf-8 -*-
"""Flask 应用入口"""
import os
from flask import Flask, render_template
from database import init_db
from routes.herb_routes import herb_bp
from routes.component_routes import component_bp
from routes.import_routes import import_bp
from routes.qa_routes import qa_bp
from routes.disease_routes import disease_bp


def create_app():
    app = Flask(__name__)

    # 注册蓝图
    app.register_blueprint(herb_bp)
    app.register_blueprint(component_bp)
    app.register_blueprint(import_bp)
    app.register_blueprint(qa_bp)
    app.register_blueprint(disease_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    # 初始化数据库
    init_db()
    app = create_app()
    print("中医药科学大数据管理平台已启动: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
