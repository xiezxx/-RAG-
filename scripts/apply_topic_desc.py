# -*- coding: utf-8 -*-
"""把新增模块 8/9/10 追加到 D:\\毕业设计\\课题描述.docx 的【功能模块】末尾（保留原 1-7 模块不动）"""
import copy
import docx
from docx.oxml.ns import qn

SRC = r"D:\毕业设计\课题描述.docx"

# 只追加的新模块（沿用原文档 1-7 的编号继续）
NEW_MODULES = [
    ('h', '8. 法律知识科普模块'),
    ('b', '8.1 系统提供科普专题文章功能，围绕加班费计算、经济补偿金、试用期、竞业限制、工伤认定、女职工保护等高频主题，由大语言模型基于检索语料按需生成通俗易懂的普法文章，生成结果缓存至数据库，支持在线阅读与重新生成。'),
    ('b', '8.2 系统提供法律名词卡片功能，将知识图谱中的法律概念、权利义务、违法行为、法律责任四类实体以术语卡片形式展示，帮助用户快速理解劳动法律术语。'),
    ('b', '8.3 系统内置高频问答专区，覆盖工资报酬、劳动合同、解除辞退、工伤社保、女职工保护等类别，用户点击问题即可获得带法律依据的解答，回答自动计入问答记录。'),
    ('b', '8.4 系统提供互动式普法功能，包括“打工人小剧场”情景剧（5个剧本、每剧3幕，用户在剧情中选择应对方式，即时获得对错判定与避坑笔记）、普法海报（自动生成普法文案并渲染为可下载图片）和普法短片（自动生成分镜脚本并合成语音旁白），将法律知识转化为可参与、可分享的场景化内容。'),
    ('h', '9. 检索过程可视化与检索模式切换模块'),
    ('b', '9.1 系统对每次问答的检索过程进行完整记录，包括BM25、向量、知识图谱三路通道的命中明细、融合排序结果、策略权重分配、时效过滤情况和各环节耗时。'),
    ('b', '9.2 用户可在回答下方展开“检索过程”面板，查看问题改写结果、时间参考、三路检索通道的命中法条以及最终入选法条的融合排名，直观核对回答依据的形成过程，增强系统的可解释性。'),
    ('b', '9.3 系统支持在问答界面一键切换检索模式，提供完整混合检索以及单一BM25、单一向量、单一图谱、BM25+向量、BM25+向量+图谱、无时效混合等组件组合模式，与消融实验配置一一对应，便于现场演示各检索组件的实际贡献。'),
    ('h', '10. 智能案情诊断模块'),
    ('b', '10.1 用户输入纠纷类型（被辞退、协商解除、拖欠工资、加班纠纷、工伤等11类）、工作年限、月工资、是否签订劳动合同及案情描述等要素，系统提供示例案情一键填充，降低使用门槛。'),
    ('b', '10.2 系统基于案情要素检索相关法条与案例，由大语言模型生成结构化诊断报告，包括按重要性排序并标注风险等级的问题清单、法律依据、风险提示和行动建议。'),
    ('b', '10.3 系统内置赔偿金额估算功能，依据《劳动合同法》第四十七条程序化计算经济补偿金N、代通知金情形N+1及违法解除赔偿金2N，并将计算结果注入大语言模型生成流程，避免模型计算错误。'),
    ('b', '10.4 诊断报告自动保存至系统，用户可随时查看历史诊断记录，并可下载排版完整的HTML格式报告（支持打印或另存为PDF），便于存档与进一步咨询。'),
]


def clone_with_text(template_p, text):
    """克隆模板段落的段落格式与首个非空 run 的字符格式，写入新文本"""
    new_p = copy.deepcopy(template_p._p)
    for r in new_p.findall(qn('w:r')):
        new_p.remove(r)
    rpr = None
    for run in template_p.runs:
        rpr_el = run._r.find(qn('w:rPr'))
        if rpr_el is not None:
            rpr = copy.deepcopy(rpr_el)
            break
    r = new_p.makeelement(qn('w:r'), {})
    if rpr is not None:
        r.append(rpr)
    t = new_p.makeelement(qn('w:t'), {})
    t.set(qn('xml:space'), 'preserve')
    t.text = text
    r.append(t)
    new_p.append(r)
    return new_p


def main():
    doc = docx.Document(SRC)
    paras = doc.paragraphs

    start_idx = end_idx = None
    for i, p in enumerate(paras):
        if p.text.strip() == '【功能模块】':
            start_idx = i
        elif p.text.strip() == '【创新点】' and start_idx is not None:
            end_idx = i
            break
    assert start_idx is not None and end_idx is not None, f'边界定位失败 start={start_idx} end={end_idx}'

    # 校验：旧 7 个模块标题仍在
    old_titles = [paras[i].text.strip() for i in range(start_idx, end_idx)
                  if paras[i].text.strip()[:2] in ('1.', '2.', '3.', '4.', '5.', '6.', '7.')
                  and len(paras[i].text.strip()) < 30]
    print('保留的旧模块标题:', old_titles)
    assert len(old_titles) == 7, f'旧模块数量异常: {len(old_titles)}'

    # 格式模板：模块标题 + 正文
    tpl_h = paras[start_idx + 1]
    tpl_b = paras[start_idx + 2]

    # 只追加：插到【创新点】之前
    anchor = paras[end_idx]._p
    for style, text in NEW_MODULES:
        tpl = tpl_h if style == 'h' else tpl_b
        anchor.addprevious(clone_with_text(tpl, text))

    doc.save(SRC)
    print('已保存（旧7模块保留 + 新增8/9/10）:', SRC)


if __name__ == '__main__':
    main()
