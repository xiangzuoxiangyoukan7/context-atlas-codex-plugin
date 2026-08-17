"""定义核心知识库模板必须包含的稳定路径。"""

from pathlib import Path
from typing import Sequence

# context-atlas-rules: [[rules/知识治理规则#RULE-GOV-003|RULE-GOV-003]]


TEMPLATE_MARKERS = frozenset(
    {
        "{{PROJECT_ID}}",
        "{{PROJECT_NAME}}",
        "{{KNOWLEDGE_BASE_NAME}}",
        "{{INITIALIZED_AT}}",
    }
)


def required_template_paths() -> Sequence[Path]:
    """返回初始化产物必须具备的文件路径集合。"""

    return tuple(
        Path(path)
        for path in (
            "README.md",
            "knowledge-base.yaml",
            ".project-kb/README.md",
            "00-项目总览/README.md",
            "00-项目总览/项目目标与成功标准.md",
            "00-项目总览/项目边界.md",
            "00-项目总览/产品能力地图.md",
            "00-项目总览/术语表.md",
            "00-项目总览/技术栈与版本.md",
            "00-项目总览/知识来源.md",
            "01-功能基线/README.md",
            "01-功能基线/TEMPLATE.md",
            "02-架构与契约/README.md",
            "02-架构与契约/系统架构.md",
            "02-架构与契约/模块边界.md",
            "02-架构与契约/接口契约.md",
            "02-架构与契约/数据库/README.md",
            "02-架构与契约/数据资产/README.md",
            "02-架构与契约/数据资产/TEMPLATE.md",
            "02-架构与契约/原型/README.md",
            "02-架构与契约/外部依赖/README.md",
            "03-实施与验收/README.md",
            "03-实施与验收/当前变更.md",
            "03-实施与验收/执行看板.md",
            "03-实施与验收/验收矩阵.md",
            "03-实施与验收/任务包/README.md",
            "03-实施与验收/任务包/TEMPLATE.md",
            "03-实施与验收/验收证据/README.md",
            "03-实施与验收/验收证据/TEMPLATE.md",
            "04-决策记录/README.md",
            "04-决策记录/TEMPLATE.md",
            "05-开发指南/README.md",
            "05-开发指南/AI知识采集协议.md",
            "05-开发指南/本地开发.md",
            "05-开发指南/测试规则.md",
            "90-历史归档/README.md",
        )
    )
