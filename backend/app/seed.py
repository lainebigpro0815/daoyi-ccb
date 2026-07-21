from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.template import ProcessTemplate, PhaseDefinition, TaskDefinition


def init_seed_data(db: Session):
    """初始化种子数据，如已存在则跳过"""
    if db.query(Product).first():
        return

    # ============ 产品定义 ============
    products = [
        Product(name="私有化企微 - 统一包", code="wecom_unified", sort_order=1),
        Product(name="私有化企微 - 定制包", code="wecom_custom", sort_order=2),
        Product(name="低代码平台", code="lowcode", sort_order=3),
        Product(name="门户", code="portal", sort_order=4),
        Product(name="纯定制化开发", code="custom_dev", sort_order=5),
        Product(name="运维服务", code="ops", sort_order=6),
    ]
    db.add_all(products)
    db.flush()

    # ============ 流程模板数据 ============
    # 每个产品定义一个模板，模板包含阶段，阶段包含任务

    seed_templates = [
        # --- 统一包企微 ---
        _make_template(db, products[0], "统一包企微部署流程", [
            _phase("项目立项准备", "组建项目团队、明确沟通机制、获取企微授权", [
                _task("1.1", "项目立项 & 组建项目团队", 2,
                      guide="明确双方项目组成员，确定项目经理。输出项目章程。",
                      deliverable="项目章程、组织架构清单", vendor_role="项目经理", customer_role="项目对接人"),
                _task("1.2", "硬件资源评估 & 环境确认", 1,
                      guide="确认企微部署所需硬件资源（服务器配置、网络带宽等）。参考统一包资源清单。",
                      deliverable="资源清单", vendor_role="实施工程师", customer_role="IT部门"),
                _task("1.3", "企微授权证书申请", 3,
                      guide="提交企微授权证书申请，填写相关表单。注意区分正式环境与测试环境。",
                      deliverable="授权证书、License", vendor_role="实施工程师", customer_role="配合盖章"),
            ]),
            _phase("基础环境搭建", "完成企微统一包的环境部署和基本配置", [
                _task("2.1", "企微统一包环境部署", 3,
                      guide="按照企微统一包部署手册进行操作。注意配置参数与客户环境匹配。",
                      deliverable="环境部署验收报告", vendor_role="实施工程师"),
                _task("2.2", "基础配置 & 初始化", 2,
                      guide="组织架构导入、用户账号初始化、基础权限配置。",
                      deliverable="配置确认单", vendor_role="实施工程师", customer_role="配合提供组织架构"),
                _task("2.3", "网络连通性测试", 1,
                      guide="验证企微客户端与服务器网络连通性，包括内外网访问测试。",
                      deliverable="网络测试报告", vendor_role="实施工程师", customer_role="IT部门配合"),
            ]),
            _phase("业务摸底与培训", "调研客户需求，组织基础培训", [
                _task("3.1", "客户业务需求调研", 2,
                      guide="了解客户使用场景，梳理核心需求。注意区分必须需求与期望需求。",
                      deliverable="需求调研记录", vendor_role="项目经理/BA", customer_role="业务部门负责人"),
                _task("3.2", "基础操作培训", 1,
                      guide="为客户管理员和用户提供企微基础操作培训。",
                      deliverable="培训签到表、培训材料", vendor_role="项目经理", customer_role="参训人员"),
            ]),
            _phase("测试与上线", "完成集成测试并正式上线", [
                _task("4.1", "集成测试", 3,
                      guide="全功能测试，包括企微客户端功能、基础应用。记录缺陷并跟踪修复。",
                      deliverable="测试报告、缺陷清单", vendor_role="测试工程师", customer_role="配合测试"),
                _task("4.2", "正式上线", 1,
                      guide="切换正式环境，确认所有功能正常。",
                      deliverable="上线确认单", vendor_role="项目经理", customer_role="客户签字确认"),
            ]),
        ]),

        # --- 定制包企微（参照徽商 Excel 简化版）---
        _make_template(db, products[1], "定制包企微部署流程", [
            _phase("项目立项准备", "项目启动、搭建组织、获取授权", [
                _task("1.1", "项目立项 & 组建项目团队", 2,
                      guide="明确双方项目成员、职责分工。输出项目章程、沟通计划。",
                      deliverable="项目章程、组织架构清单、沟通计划", vendor_role="项目经理", customer_role="项目对接人"),
                _task("1.2", "硬件资源申请 & 架构确认", 3,
                      guide="评估硬件资源需求（建议16k并发以上），确认整体技术架构。注意与客户IT部门充分沟通。",
                      deliverable="硬件资源清单、UAT/正式环境部署方案", vendor_role="实施工程师", customer_role="IT部门"),
                _task("1.3", "企微授权证书申请 & License获取", 5,
                      guide="提交企微授权证书申请，跟进审批流程。注意授权证书有有效期。",
                      deliverable="企微授权证书、License", vendor_role="项目经理", customer_role="配合提供资质文件"),
            ]),
            _phase("基础环境搭建", "搭建UAT/正式环境，完成基础配置", [
                _task("2.1", "UAT环境搭建 & 硬件部署", 2,
                      guide="部署UAT环境，完成服务器初始化。参考部署方案执行。",
                      deliverable="UAT环境验收报告", vendor_role="实施工程师", customer_role="IT部门配合"),
                _task("2.2", "企微UAT环境配置", 3,
                      guide="完成企微定制包UAT配置，包括应用管理、通讯录同步等。",
                      deliverable="环境配置单", vendor_role="实施工程师"),
                _task("2.3", "应用打包 & 上架准备", 2,
                      guide="完成定制应用打包、iOS/Android证书配置。注意上架审核周期。",
                      deliverable="安装包", vendor_role="实施工程师"),
                _task("2.4", "网络连通性与安全测试", 1,
                      guide="全面测试网络连通性，包括VPN、专线等场景。",
                      deliverable="网络测试报告", vendor_role="实施工程师"),
            ]),
            _phase("业务摸底与启动", "业务需求调研、接口规范培训", [
                _task("3.1", "业务应用系统摸底", 3,
                      guide="全面梳理客户现有业务应用系统清单，识别待集成系统。覆盖办公/业务/科技等。",
                      deliverable="应用系统盘点清单V1.0", vendor_role="BA+客户业务部门", customer_role="业务部门接口人"),
                _task("3.2", "接口规范培训 & 开发平台API培训", 2,
                      guide="组织开发平台API培训，输出接口规范手册。",
                      deliverable="培训材料、接口规范手册", vendor_role="技术经理", customer_role="开发人员参加"),
                _task("3.3", "AI需求 & 增值应用需求调研", 2,
                      guide="调研AI应用场景，包括智能客服、文档处理等。输出AI需求清单。",
                      deliverable="AI需求清单", vendor_role="AI产品经理", customer_role="业务部门"),
            ]),
            _phase("系统集成与测试", "完成应用集成、全链路测试", [
                _task("4.1", "统一入口/统一待办/统一信息集成", 5,
                      guide="完成三方应用集成，实现统一门户。注意各系统对接规范。",
                      deliverable="集成API文档", vendor_role="开发工程师", customer_role="配合提供接口文档"),
                _task("4.2", "业务应用接入（信贷/风控/OA等）", 5,
                      guide="接入各业务系统，完成接口联调。",
                      deliverable="接口联调确认单", vendor_role="开发工程师", customer_role="业务系统负责人"),
                _task("4.3", "AI智能助手 & 增值应用开发", 10,
                      guide="开发AI智能客服、智能文档处理等增值应用。聚焦高价值场景。",
                      deliverable="AI模块", vendor_role="AI开发团队", customer_role="提供业务场景样例"),
                _task("4.4", "UAT用户验收测试", 5,
                      guide="组织客户关键用户进行UAT测试，记录问题并跟踪修复。",
                      deliverable="UAT测试报告、缺陷清单", vendor_role="测试工程师", customer_role="关键用户参与"),
            ]),
            _phase("试运行与投产", "试运行验证，正式切换", [
                _task("5.1", "试运行（关键用户小范围）", 5,
                      guide="选取部分关键用户试运行，收集反馈。注意设置反馈渠道。",
                      deliverable="试运行报告", vendor_role="项目经理", customer_role="关键用户使用"),
                _task("5.2", "培训与推广", 3,
                      guide="组织全员培训，输出操作手册和视频教程。",
                      deliverable="操作手册、培训视频", vendor_role="项目经理", customer_role="参训人员"),
                _task("5.3", "正式上线", 1,
                      guide="全量切换，停止旧系统。注意数据迁移和备份。",
                      deliverable="上线确认签字单", vendor_role="项目经理", customer_role="客户签字确认"),
            ]),
        ]),

        # --- 低代码平台 ---
        _make_template(db, products[2], "低代码平台部署流程", [
            _phase("部署准备", "服务器准备、License获取", [
                _task("1.1", "低代码平台License申请", 2,
                      guide="提交License申请，确定授权范围。注意区分正式/测试License。",
                      deliverable="License文件", vendor_role="项目经理"),
                _task("1.2", "服务器环境准备", 2,
                      guide="按低代码平台部署要求准备服务器环境（JDK、数据库等）。",
                      deliverable="环境检查单", vendor_role="实施工程师", customer_role="IT部门配合"),
            ]),
            _phase("平台部署", "安装低代码平台并初始化", [
                _task("2.1", "低代码平台安装", 2,
                      guide="执行安装脚本，完成基础部署。注意初始化参数配置。",
                      deliverable="安装日志", vendor_role="实施工程师"),
                _task("2.2", "平台初始化配置", 2,
                      guide="租户创建、用户导入、基础模块启用。",
                      deliverable="配置确认单", vendor_role="实施工程师", customer_role="提供基础数据"),
                _task("2.3", "功能验证测试", 2,
                      guide="验证平台核心功能正常（表单、流程、报表）。",
                      deliverable="功能测试报告", vendor_role="测试工程师", customer_role="配合测试"),
            ]),
            _phase("培训与移交", "客户管理员培训、移交运维", [
                _task("3.1", "管理员培训", 2,
                      guide="培训客户管理员掌握平台管理、应用发布、用户管理等操作。",
                      deliverable="管理员手册", vendor_role="项目经理", customer_role="管理员参加"),
                _task("3.2", "运维移交", 1,
                      guide="移交运维文档、监控账号、备份策略等。",
                      deliverable="运维移交清单", vendor_role="实施工程师", customer_role="运维团队接收"),
            ]),
        ]),

        # --- 门户 ---
        _make_template(db, products[3], "门户部署流程", [
            _phase("部署准备", "环境检查、资源准备", [
                _task("1.1", "门户部署环境检查", 1,
                      guide="确认服务器配置满足门户部署要求。",
                      deliverable="环境检查单", vendor_role="实施工程师"),
                _task("1.2", "门户License获取", 1,
                      guide="申请门户产品License。",
                      deliverable="License文件", vendor_role="项目经理"),
            ]),
            _phase("门户部署与配置", "安装门户并完成定制配置", [
                _task("2.1", "门户安装部署", 2,
                      guide="安装门户服务，完成基础配置。",
                      deliverable="安装记录", vendor_role="实施工程师"),
                _task("2.2", "门户主题配置", 2,
                      guide="配置门户主题风格、布局、导航等。",
                      deliverable="门户配置确认单", vendor_role="实施工程师", customer_role="确认样式"),
                _task("2.3", "门户集成测试", 2,
                      guide="验证门户与各应用集成正常，页面访问、跳转、SSO正常。",
                      deliverable="集成测试报告", vendor_role="测试工程师"),
            ]),
        ]),

        # --- 纯定制化开发 ---
        _make_template(db, products[4], "纯定制开发流程", [
            _phase("需求阶段", "需求分析、原型设计", [
                _task("1.1", "需求调研与分析", 3,
                      guide="深入了解客户需求，输出需求规格说明书。注意需求变更管理。",
                      deliverable="需求规格说明书", vendor_role="BA/产品经理", customer_role="业务部门确认"),
                _task("1.2", "原型设计 & 客户确认", 3,
                      guide="输出交互原型，与客户确认UI设计和交互流程。",
                      deliverable="原型设计稿", vendor_role="UI设计师", customer_role="客户确认"),
            ]),
            _phase("开发阶段", "技术设计、编码实现", [
                _task("2.1", "技术方案设计", 2,
                      guide="系统架构设计、数据库设计、接口设计。",
                      deliverable="技术设计文档", vendor_role="技术经理"),
                _task("2.2", "编码开发", None,
                      guide="按技术方案进行编码实现，定期代码审查。承诺交付时间视需求复杂度定。",
                      deliverable="代码库", vendor_role="开发工程师"),
                _task("2.3", "单元测试 & 代码审查", 2,
                      guide="开发完成自测，代码审查，修复缺陷。",
                      deliverable="单元测试报告", vendor_role="开发工程师"),
            ]),
            _phase("交付阶段", "测试、部署、验收", [
                _task("3.1", "集成测试", 3,
                      guide="全功能集成测试，输出测试报告。",
                      deliverable="测试报告", vendor_role="测试工程师"),
                _task("3.2", "部署上线", 1,
                      guide="部署到正式环境，完成上线。",
                      deliverable="上线确认单", vendor_role="实施工程师", customer_role="客户确认"),
                _task("3.3", "验收 & 移交", 2,
                      guide="客户验收测试，验收通过后移交源码和运维文档。",
                      deliverable="验收报告、运维文档", vendor_role="项目经理", customer_role="验收签字"),
            ]),
        ]),

        # --- 运维服务 ---
        _make_template(db, products[5], "基础运维服务", [
            _phase("运维初始化", "建立运维体系", [
                _task("1.1", "运维交接", 1,
                      guide="从实施团队接收运维所需的系统信息、账号密码、架构文档。",
                      deliverable="运维交接清单", vendor_role="运维工程师", customer_role="IT部门配合"),
                _task("1.2", "监控体系搭建", 2,
                      guide="配置监控告警（Zabbix/Prometheus等），设置告警阈值。",
                      deliverable="监控配置记录", vendor_role="运维工程师"),
            ]),
            _phase("日常运维", "定期巡检、故障处理", [
                _task("2.1", "定期巡检（周/月）", None,
                      guide="按周期检查系统运行状态，输出巡检报告。注意关注磁盘、内存、CPU使用率。",
                      deliverable="巡检报告", vendor_role="运维工程师"),
                _task("2.2", "故障处理 & 应急响应", None,
                      guide="接收告警和用户报障，按SLA响应处理。",
                      deliverable="故障处理记录", vendor_role="运维工程师"),
                _task("2.3", "版本升级 & 补丁管理", None,
                      guide="按需执行系统升级和补丁更新，注意变更管理流程。",
                      deliverable="变更记录", vendor_role="运维工程师"),
            ]),
        ]),
    ]


def _phase(name, description, tasks):
    return {"name": name, "description": description, "tasks": tasks}


def _task(task_number, name, estimated_days, guide="", deliverable="",
          vendor_role="", customer_role=""):
    return {
        "task_number": task_number,
        "name": name,
        "estimated_days": estimated_days,
        "guide": guide,
        "deliverable": deliverable,
        "vendor_role": vendor_role,
        "customer_role": customer_role,
    }


def _make_template(db, product, name, phases_data):
    template = ProcessTemplate(
        product_id=product.id,
        name=name,
        version="1.0",
        is_active=True,
    )
    db.add(template)
    db.flush()

    for pi, pd in enumerate(phases_data, 1):
        phase = PhaseDefinition(
            template_id=template.id,
            phase_number=pi,
            name=pd["name"],
            description=pd["description"],
            sort_order=pi,
        )
        db.add(phase)
        db.flush()

        for ti, td in enumerate(pd["tasks"], 1):
            task = TaskDefinition(
                phase_id=phase.id,
                task_number=td["task_number"],
                name=td["name"],
                estimated_days=td["estimated_days"] if td["estimated_days"] else 0,
                guide=td["guide"],
                deliverable=td["deliverable"],
                vendor_role=td["vendor_role"],
                customer_role=td["customer_role"],
                sort_order=ti,
            )
            db.add(task)

    db.commit()
    return template
