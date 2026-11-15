# -*- coding: utf-8 -*-
"""生成参赛技术文档 PDF（<=30 页）。

运行： .venv\\Scripts\\python.exe docs\\build_tech_doc.py
产物： docs/ScholarRAG_技术文档.pdf
"""
from __future__ import annotations

import os
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'ScholarRAG_技术文档.pdf')

FONT_DIR = r'C:\Windows\Fonts'
pdfmetrics.registerFont(TTFont('CN', os.path.join(FONT_DIR, 'simhei.ttf')))
pdfmetrics.registerFont(TTFont('CNB', os.path.join(FONT_DIR, 'msyhbd.ttc'), subfontIndex=0))

ACCENT = colors.HexColor('#1f4e79')
INK = colors.HexColor('#222222')
GREY = colors.HexColor('#666666')
LINE = colors.HexColor('#c8d2dc')

S = {
    'title': ParagraphStyle('title', fontName='CNB', fontSize=25, leading=34,
                            alignment=TA_CENTER, textColor=ACCENT, spaceAfter=8),
    'subtitle': ParagraphStyle('subtitle', fontName='CN', fontSize=12, leading=20,
                               alignment=TA_CENTER, textColor=GREY),
    'cover_sub': ParagraphStyle('cover_sub', fontName='CNB', fontSize=14.5, leading=21,
                                alignment=TA_CENTER, textColor=ACCENT),
    'meta': ParagraphStyle('meta', fontName='CN', fontSize=10.5, leading=18,
                           alignment=TA_CENTER, textColor=INK),
    'h1': ParagraphStyle('h1', fontName='CNB', fontSize=15.5, leading=24, textColor=ACCENT,
                         spaceBefore=12, spaceAfter=7, keepWithNext=1),
    'h2': ParagraphStyle('h2', fontName='CNB', fontSize=12, leading=19, textColor=INK,
                         spaceBefore=8, spaceAfter=3, keepWithNext=1),
    'h3': ParagraphStyle('h3', fontName='CNB', fontSize=10.8, leading=17, textColor=INK,
                         spaceBefore=5, spaceAfter=2, keepWithNext=1),
    'body': ParagraphStyle('body', fontName='CN', fontSize=9.8, leading=15.8, textColor=INK,
                           alignment=TA_LEFT, firstLineIndent=20, spaceAfter=4),
    'ni': ParagraphStyle('ni', fontName='CN', fontSize=9.8, leading=15.8, textColor=INK,
                         alignment=TA_LEFT, spaceAfter=4),
    'bullet': ParagraphStyle('bullet', fontName='CN', fontSize=9.8, leading=15.8, textColor=INK,
                             leftIndent=15, bulletIndent=3, spaceAfter=2),
    'code': ParagraphStyle('code', fontName='CN', fontSize=8.4, leading=13,
                           textColor=colors.HexColor('#243b53'), leftIndent=8,
                           backColor=colors.HexColor('#f4f7fa'), borderPadding=6,
                           spaceBefore=3, spaceAfter=5),
    'cap': ParagraphStyle('cap', fontName='CN', fontSize=8.6, leading=12.5, textColor=GREY,
                          alignment=TA_CENTER, spaceBefore=2, spaceAfter=7),
    'toc': ParagraphStyle('toc', fontName='CN', fontSize=10.5, leading=21, textColor=INK),
}

W = A4[0] - 40 * mm


def P(t, s='body'):
    return Paragraph(t, S[s])


def B(t):
    return Paragraph(t, S['bullet'], bulletText='•')


def H1(t):
    return Paragraph(t, S['h1'])


def H2(t):
    return Paragraph(t, S['h2'])


def H3(t):
    return Paragraph(t, S['h3'])


def CODE(t):
    return Paragraph(t.replace(' ', '&nbsp;').replace('\n', '<br/>'), S['code'])


def cap(t):
    return Paragraph(t, S['cap'])


def TB(rows, widths=None, fs=8.6):
    data = []
    for i, r in enumerate(rows):
        st = ParagraphStyle('c%d' % i, fontName='CNB' if i == 0 else 'CN',
                            fontSize=fs, leading=fs + 4.5, textColor=INK)
        data.append([Paragraph(str(c), st) for c in r])
    t = Table(data, colWidths=widths or [W / len(rows[0])] * len(rows[0]), repeatRows=1)
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.4, LINE),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eaf1f7')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('CN', 8)
    canvas.setFillColor(GREY)
    canvas.drawString(20 * mm, 12 * mm, 'ScholarRAG Agent · 全流程科研助手')
    canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, '第 %d 页' % doc.page)
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.4)
    canvas.line(20 * mm, 15.5 * mm, A4[0] - 20 * mm, 15.5 * mm)
    canvas.restoreState()


s = []

# ============================================================ 封面
s += [
    Spacer(1, 48 * mm),
    P('ScholarRAG Agent', 'title'),
    Spacer(1, 3 * mm),
    P('全流程科研助手：抗幻觉文献问答与自主编排系统', 'cover_sub'),
    Spacer(1, 6 * mm),
    P('技术文档', 'subtitle'),
    Spacer(1, 42 * mm),
    P('2026 全国高校 AI 大模型挑战赛（B 组）参赛作品', 'meta'),
    Spacer(1, 3 * mm),
    P('参赛方向：全流程科研助手 Agent（Web 系统）', 'meta'),
    Spacer(1, 3 * mm),
    P('提交日期：2026 年 11 月 18 日', 'meta'),
    Spacer(1, 3 * mm),
    P('代码仓库：github.com/YankeeLio/scholar-rag-agent', 'meta'),
    PageBreak(),
]

# ============================================================ 目录
s += [P('目　录', 'h1'), Spacer(1, 2 * mm)]
for it in [
    '一、项目概述',
    '二、系统总体架构',
    '三、关键模块设计与实现',
    '　　3.1 多模态文档解析：矢量文本层与扫描件重建',
    '　　3.2 章节感知切块与语义索引',
    '　　3.3 稠密 + 稀疏混合检索',
    '　　3.4 证据约束生成：抗幻觉 RAG',
    '　　3.5 Agent 自主编排：Function Calling + SSE',
    '　　3.6 引用图谱与图论基石文献挖掘',
    '　　3.7 版式联动阅读与划词学术翻译',
    '　　3.8 跨版本文档语义去重',
    '四、工程实现与稳定性',
    '五、验证结果与能力对照',
    '六、业务闭环与差异化价值',
    '七、局限与后续规划',
    '附录 A　接口清单',
    '附录 B　部署与复现步骤',
]:
    s.append(Paragraph(it, S['toc']))
s.append(PageBreak())

# ============================================================ 一
s += [
    H1('一、项目概述'),
    H2('1.1 赛题背景与产品定位'),
    P('科研人员的真实工作流不是「问一句、答一句」，而是「导入文献—读懂原文—定位证据—横向对比—找到源头工作—写进自己的稿子」。'
      '通用大模型能聊，但它有三个致命短板：不知道你的文献库里有什么；说得头头是道却给不出页码；'
      '遇到扫描件、长教材、同一论文的多个版本就彻底失效。'),
    P('本项目把这条工作流做成一个可交付的 Web 系统：上传 PDF 即自动完成细粒度解析、结构化切块与语义入库；'
      '提问时先检索、再作答，每条结论强制携带可回溯到「文档—页码—原文行」的证据锚点，证据不足时明确拒答而非编造；'
      '进一步用 Agent 把「查库、列清单、看图谱、比论文、找外部新文献」这些动作串成自主编排的多轮流程；'
      '最后用版式联动阅读把「机翻一段」变成「对照原文逐行读」。'),
    P('一句话定位：<b>一个读得懂扫描件、答得带出处、还会自己决定下一步查什么的科研助手。</b>'),
    H2('1.2 目标用户与典型场景'),
    TB([
        ['用户角色', '真实痛点', '本系统的解法'],
        ['研究生 / 低年级博士', '英文论文读得慢，公式和术语拿不准，不敢整段机翻', '版式联动阅读：原文逐行 + 划词学术翻译，术语一致、公式保留'],
        ['课题组文献管理员', '库里几十上百篇，同一篇论文存了 v1 和 v7，重复占位', '上传即语义去重，相似度 0.8989 触发预警并可一键替换'],
        ['需要写综述的人', '想知道领域里哪些工作是绕不过去的基石，人工顺藤摸瓜太慢', '引用图谱 + PageRank，直接给出基石文献与被引关系'],
        ['跨方向借鉴者', '两篇不同领域的论文，方法能不能迁移说不清', 'Agent 跨论文对比工具，输出结构化共同点与差异维度表'],
    ], widths=[34 * mm, 60 * mm, W - 94 * mm]),
    cap('表 1　目标用户与场景映射'),
    H2('1.3 核心能力一览'),
    TB([
        ['能力域', '已实现能力'],
        ['多模态解析', '矢量 PDF 行级解析（标题树/作者/摘要/表格/参考文献）；无文本层扫描件走 OCR 通道重建文档'],
        ['知识组织', '章节感知切块（1800 字符上限 + 页码锚点）；本地 BGE-M3 向量 + Chroma 持久化；块级语义去重'],
        ['检索与生成', '稠密 0.6 + BM25 0.4 混合召回；证据约束 Prompt；SSE 流式输出与引用溯源面板'],
        ['Agent 编排', 'Function Calling 自主决策，5 个工具、最多 5 轮循环，思考轨迹实时推送'],
        ['图论分析', '入度 / 出度 / PageRank（α=0.85）计算基石文献与边缘文献'],
        ['阅读与翻译', '页面原图渲染 + 行级版面框归一化叠加；扫描页 OCR 兜底；单行划词与整页分批翻译'],
    ], widths=[30 * mm, W - 30 * mm]),
    cap('表 2　系统能力总览'),
    PageBreak(),
]

# ============================================================ 二
s += [
    H1('二、系统总体架构'),
    H2('2.1 分层架构'),
    P('系统采用「单进程后端 + 单页前端」的轻量全栈结构：一个 FastAPI 进程同时承载 REST 接口、SSE 流式接口与前端静态资源，'
      '无需额外部署 Nginx 或前端构建链，便于在最低配云主机上完成公网演示。'),
    CODE('浏览器（apps/web/index.html，原生 HTML + ECharts）\n'
         '        │  HTTP / SSE\n'
         '        ▼\n'
         'FastAPI（apps/api/app/main.py）\n'
         '  ├─ parser.py     行级结构化解析（章节树 / 参考文献 / 表格）\n'
         '  ├─ ocr.py        RapidOCR 扫描件通道 + 单页版面框\n'
         '  ├─ chunker.py    章节感知切块（1800 字符上限，页码锚点）\n'
         '  ├─ embedding.py  本地 BGE-M3（CPU 推理，1024 维）\n'
         '  ├─ indexer.py    Chroma 持久化向量库\n'
         '  ├─ retriever.py  稠密 + BM25 混合检索\n'
         '  ├─ dedup.py      块级语义去重（avg pairwise cosine）\n'
         '  ├─ llm.py        DeepSeek Chat 证据约束 RAG（非流式 + SSE）\n'
         '  ├─ agent.py      Function Calling 编排层（5 工具 / 5 轮 / SSE 事件）\n'
         '  ├─ graph.py      引用图谱 + PageRank 基石挖掘\n'
         '  ├─ reader.py     页面渲染 + 行级版面（bbox 归一化，LRU 24 页）\n'
         '  └─ translate.py  学术翻译契约（术语一致 / 公式保留）'),
    cap('图 1　系统模块结构'),
    H2('2.2 技术选型与理由'),
    TB([
        ['环节', '选型', '选择理由'],
        ['PDF 解析', 'PyMuPDF', '对共享内容流的页面边界处理干净，Unicode 还原优于 pypdf / pdfplumber；并能渲染页面图供联动阅读复用'],
        ['OCR', 'RapidOCR + ONNXRuntime', '纯 CPU 可跑、无需联网下载大模型权重，官方扫描件测试集 15 页约 49 秒'],
        ['Embedding', 'BAAI/bge-m3（本地）', '中英文混合语料表现稳定；本地 CPU 推理避免按 token 计费与外部依赖，离线可复现'],
        ['向量库', 'Chroma（本地持久化）', '零运维、随进程启动即用；配合落盘 embed 缓存避免重复编码'],
        ['生成模型', 'DeepSeek-Chat', 'OpenAI 兼容接口，支持 function calling 与流式；中文长文理解与数学推导质量满足科研问答'],
        ['图算法', 'NetworkX', 'PageRank / 度数统计实现标准，便于对引用图做中心性分析'],
        ['前端', '原生 HTML + ECharts', '无构建链、单文件可托管；ECharts 在 CDN 不可用时降级为列表，保证演示环境可用'],
    ], widths=[23 * mm, 38 * mm, W - 61 * mm]),
    cap('表 3　技术选型'),
    H2('2.3 一次问答的完整数据流'),
    P('<b>入库阶段：</b>PDF 上传 → 判断是否存在文本层 → 有则按行解析并还原章节树，无则逐页 OCR 重建 → 章节感知切块 → '
      '批量编码为 1024 维向量（结果落盘缓存）→ 与既有块做语义去重 → 写入 Chroma 并记录 source / 页码 / 章节元数据。'),
    P('<b>查询阶段：</b>用户提问 → 稠密向量召回 + BM25 稀疏召回 → 加权融合排序 → 取 Top-K 片段拼装证据块 → 证据约束 Prompt → '
      'DeepSeek 生成 → 校验引用编号与页码 → SSE 逐块推送到前端 → 前端渲染正文与证据面板。'),
    P('<b>Agent 阶段：</b>问题进入编排层 → 模型输出 plan 与首个 tool_call → 后端执行工具并把结果回填 → 模型判断信息是否足够 → '
      '不足则进入下一轮（上限 5 轮）→ 足够后输出最终答案；全过程以 SSE 事件流同步到左侧思考轨迹。'),
    PageBreak(),
]

# ============================================================ 三
s += [
    H1('三、关键模块设计与实现'),
    H2('3.1 多模态文档解析：矢量文本层与扫描件重建'),
    H3('3.1.1 行级解析而非整页文本'),
    P('多数 PDF 工具只能给出一整页文本，标题层级与参考文献全糊在一起。本项目以<b>行</b>为最小单位保存解析结果：'
      '每行记录页码、bbox、字号、字体与文本，再由字号跳变与编号模式（如 12.3、Chapter 4）重建章节树。'
      '章节标题识别经过一次收紧：判定条件由「含字母」改为「必须以字母开头」，避免把 3.1 引言这类纯编号行误判为标题。'),
    H3('3.1.2 扫描件的两条通道'),
    P('官方测试集提供了无文本层的图片型 PDF。系统先探测文本层是否为空，为空则进入 OCR 通道：按页渲染（200 DPI）→ RapidOCR 识别 → '
      '以「每页一个 Section」重建 Document，使后续切块、索引、检索流程无需任何改动即可复用。'
      '扫描识别结果并非只用于检索，还会以带坐标的行级版面条形式供给联动阅读（见 3.7）。'),
    TB([
        ['输入', '处理路径', '实测结果'],
        ['1706.03762v7.pdf（矢量）', '文本层行级解析', '27 块，标题 / 作者 / 摘要 / 参考文献完整'],
        ['1706.03762v1_img.pdf（扫描）', 'OCR 逐页重建', '15 页 / 975 行 / 28 块，约 49 秒'],
        ['Understanding Deep Learning（541 页教材）', '文本层解析 + 章节树', '893 块，含 12 Transformers / 18 Diffusion / 19 RL 章节'],
    ], widths=[56 * mm, 44 * mm, W - 100 * mm]),
    cap('表 4　三类输入的解析结果'),

    H2('3.2 章节感知切块与语义索引'),
    P('朴素定长切块会把一个公式、一张表的上下文劈成两半，检索到的片段缺主语，模型只能猜。本项目按章节边界优先切块，'
      '单块上限 1800 字符，块内保留「文档标题 + 章节路径 + 起始页码」三元组作为元数据；'
      '这使检索命中后能直接回答「在第几页、属于哪一节」。'),
    P('向量侧使用本地 BGE-M3（1024 维，CPU 推理）。为解决 CPU 编码耗时问题，编码结果按内容哈希落盘缓存，同一批文档二次处理直接命中缓存；'
      '当前库内共 921 个块（教材 893 + 扫描件 28），一次全量索引在 CPU 上约 40–70 分钟，命中缓存后为秒级。'),

    H2('3.3 稠密 + 稀疏混合检索'),
    P('纯向量检索对专有术语、公式符号、编号这类精确串不敏感（例如问「式 18.29」时，向量会跑到语义相近但无关的章节）；纯 BM25 又抓不住同义改写。'
      '系统采用加权融合：'),
    CODE('score = 0.6 × cosine(q, d) + 0.4 × BM25(q, d)\n'
         'BM25 分词：中文二元组（bigram）切分 + 英文按词切分，避免中文单字噪音'),
    P('权重经教材问答实测确定：0.6 / 0.4 在「概念解释类」与「精确数值类」问题上同时优于单一通道；'
      '融合后按分数取 Top-K，并把同一章节的相邻块合并，减少证据碎片化。'),

    H2('3.4 证据约束生成：抗幻觉 RAG'),
    P('抗幻觉不是靠「请你不要编造」这种祈祷式提示，而是把它变成可检查的契约。系统在 Prompt 层写入四条硬约束：'),
    B('<b>只依据给定证据回答</b>：证据里没有的内容必须说明「库中无相关记述」，不得用模型自身知识补全。'),
    B('<b>数字必须与证据逐字一致</b>：BLEU、参数量、β1 / β2 等数值只能来自证据，禁止换算或近似。'),
    B('<b>每个结论携带引用编号</b>：形如 [1][2]，前端据此展开到「文档—页码—原文」。'),
    B('<b>使用提问者的语言作答</b>：中文问就中文答，术语首次出现可附英文原词。'),
    P('工程侧还有两道校验：生成完成后检查引用编号是否落在本次召回的片段范围内（越界即提示引用不可信）；'
      '同时把「证据不足」当作正常出口而不是失败——宁可拒答，也不给一个看起来对但查不到出处的答案。'),
    P('实测表现：问「扩散模型训练目标」时，系统自主检索 3 轮后给出 ELBO、式 18.29 与「预测噪声参数化」的推导链，'
      '并主动声明「库中无 DDPM 原始论文」；问「我库里有哪些文献」时不再硬凑答案，而是调用清单工具返回表格。'),

    H2('3.5 Agent 自主编排：Function Calling + SSE'),
    P('单轮 RAG 只能回答「库里有什么」；真实科研问题常常需要先查清单、再检索、再对比、最后还要去外部找新文献。'
      '本项目用 Function Calling 把工具调用权交给模型，后端只做执行与校验：'),
    TB([
        ['工具', '作用', '典型触发'],
        ['search_library', '库内混合检索，返回带页码的证据片段', '任何基于库内内容的问题'],
        ['list_documents', '列出库内文献与块数', '我库里有哪些文献'],
        ['get_citation_graph', '返回引用图、PageRank 排序与基石文献', '哪篇是这块的源头工作'],
        ['compare_docs', '对两篇指定文献做结构化对比（共同点 + 差异维度）', '这两篇方法有什么不同'],
        ['fetch_arxiv', '按主题检索 arXiv 新文献并分类推荐，主动剔除不相关领域', '帮我找几篇最新的综述'],
    ], widths=[31 * mm, 76 * mm, W - 107 * mm]),
    cap('表 5　Agent 工具集'),
    P('编排上限设为 5 轮：实测「自动综述」类任务需要「列清单 → 多次检索 → 对比 → 汇总」约 4 轮；上限过低会导致中途放弃，过高则浪费 token。'
      '全过程通过 SSE 推送五类事件——plan（计划）、tool_call（调用）、tool_result（结果）、delta（正文增量）、done（结束）；'
      '前端左栏呈现思考轨迹、右栏流式呈现答案，让「Agent 在想什么」对用户可见，而不是黑箱等待。'),

    H2('3.6 引用图谱与图论基石文献挖掘'),
    P('把库内文档的参考文献标题与库内其他文档标题做全文归一化包含匹配来建边（避免因大小写、标点、副标题差异漏边），'
      '再用 NetworkX 计算入度、出度与 PageRank（α=0.85，取图分析常用阻尼系数）。'),
    P('这一步的价值在于把「读文献」变成「看结构」：PageRank 高且入度高的节点就是该知识域的<b>基石文献</b>（后续工作普遍建立在它之上），'
      '出度高而入度低的节点往往是<b>综述型或边缘型</b>文献。前端用 ECharts 力导向图渲染，节点大小随 PageRank 变化；'
      'CDN 不可用时自动降级为排序列表，保证答辩现场不空屏。'),

    H2('3.7 版式联动阅读与划词学术翻译'),
    P('这是本系统最像人干活的一环：左边原文、右边译文，点哪行译哪行。技术上有三个关键决策。'),
    H3('（1）bbox 归一化，让版面与渲染解耦'),
    P('版面坐标若按像素保存，换 DPI 或换屏幕就会错位。系统在解析阶段就把 bbox 归一化到 0–1：用行的 x0 / y0 / x1 / y1 除以页面宽高，'
      '前端以百分比绝对定位覆盖在页面图上。这样 96 DPI 的缩略图与 200 DPI 的高清图共用同一份坐标，翻页、缩放、换设备都不会漂移。'),
    H3('（2）扫描页的 OCR 兜底'),
    P('扫描件没有文本层，直接取版面会得到 0 行——界面看起来就像坏了。系统在版面接口上做兜底：文本层为空时，对该页单页渲染并调用 OCR，'
      '返回带归一化坐标的行列表，并标记 ocr=True；OCR 异常只记录到 ocr_error 字段而不抛出，确保 OCR 永远不会拖垮阅读器。'
      '实测扫描件第 1 页返回 55 行，标题与作者行的坐标与页面图逐行对齐。'),
    H3('（3）翻译是与 RAG 分离的独立契约'),
    P('机器翻译用在论文上有两个高频错误：术语前后不一致、公式与引用编号被顺手翻译。系统为翻译单独写了 Prompt 契约：只输出译文；'
      '术语按学科通用译法且全文一致；公式、数学符号、变量名、引用编号保持原样；保留段落编号层级；不确定的译名保留英文不臆造。'
      '温度取 0.1 以保证稳定。由于单次接口限制 4000 字符，整页翻译在前端按 1800 字符分批循环并实时提示进度。'),
    TB([
        ['能力点', '实现要点', '验证结果'],
        ['页面渲染', 'PyMuPDF 按 DPI 渲染 PNG，LRU 缓存 24 页', '第 1 页 120 DPI 输出 61 KB，浏览器实显 1275 px 宽'],
        ['版面文本', 'blocks→lines→spans，bbox 归一化 4 位小数', '教材第 1 页 11 行，首行 bbox [0.2579, 0.1976, 0.6757, 0.2194]'],
        ['扫描兜底', '文本层为空时单页 OCR 补行，异常不抛出', '扫描件第 1 页 55 行，标题行 bbox [0.3431, 0.1255, 0.6543, 0.1457]'],
        ['交互联动', 'overlay 按 bbox 百分比定位，点击即译', '浏览器实测 55 个行框与原文逐行对齐，点击弹出译文卡片'],
    ], widths=[25 * mm, 72 * mm, W - 97 * mm]),
    cap('表 6　联动阅读与翻译实现要点'),

    H2('3.8 跨版本文档语义去重'),
    P('同一篇论文的 arXiv v1 与 v7 常被重复导入。系统在入库前对块向量做两两余弦相似度平均，超过 0.85 判定为同一论文的不同版本并预警，'
      '用户可选择保留新版并替换旧版。实测 v1 与 v7 的整体相似度为 <b>0.8989</b>，稳定触发预警；'
      '阈值取 0.85 是权衡：过低会误杀同主题不同论文，过高则漏判大改版。'),
    PageBreak(),
]

# ============================================================ 四
s += [
    H1('四、工程实现与稳定性'),
    H2('4.1 项目结构'),
    CODE('apps/api/app/        后端核心模块（见 2.1）\n'
         'apps/api/requirements.txt\n'
         'apps/web/index.html  前端单页（问答 / Agent / 联动阅读 / 图谱 四个页签）\n'
         'pdf/                 官方测试集\n'
         'docs/                开发日志、技术文档、接口验证产物\n'
         'data/                运行时数据（向量缓存、Chroma 索引、上传副本；不入库）\n'
         '.env.example         环境变量模板（密钥留空）'),
    H2('4.2 资源与性能'),
    TB([
        ['指标', '实测值', '说明'],
        ['推理硬件', '纯 CPU，无 GPU', 'CUDA 不可用的环境下仍可完整运行，降低部署门槛'],
        ['首次冷启动', '75–90 秒', '加载 BGE-M3 权重；之后常驻内存'],
        ['541 页教材索引', '约 40–70 分钟', 'CPU 编码 893 块；命中落盘缓存后秒级'],
        ['扫描件 15 页 OCR', '约 49 秒', 'RapidOCR + ONNXRuntime，CPU'],
        ['单页版面 OCR 兜底', '1–3 秒', '联动阅读翻页时可接受'],
        ['页面图渲染', 'LRU 缓存 24 页', '常用翻页序列基本无重复渲染'],
    ], widths=[34 * mm, 32 * mm, W - 66 * mm]),
    cap('表 7　性能实测'),
    H2('4.3 稳定性：索引损坏事故与工程铁律'),
    P('开发期发生过两次 Chroma HNSW 索引损坏，第二次导致 921 块的原始文本彻底丢失、只能重新上传重建。'
      '根因是 Windows 上 Chroma 的 HNSW 段文件由后台 compactor 异步落盘：进程被强杀或断电时向量本体尚未写盘，'
      '而 sqlite 中的元数据已在，形成「有记录、无向量」的不一致状态。由此固化为五条铁律：'),
    B('<b>等待落盘</b>：写入完成后至少等待 30 秒再重启服务，关机前先优雅停止。'),
    B('<b>禁止并发打开</b>：服务运行期间绝不用独立脚本打开同一 Chroma 目录（只读也不允许），调试只走 HTTP 接口。'),
    B('<b>禁止删除重建</b>：绝不脚本化 rmtree 索引目录后再「恢复」，会连带删掉 sqlite 里的原始块文本。'),
    B('<b>向量落盘缓存</b>：embedding 结果按内容哈希缓存为 npy，崩溃重跑不浪费 CPU 时间。'),
    B('<b>恢复只走服务流程</b>：从原始 PDF 重新上传重建，不写独立恢复脚本。'),
    P('另有一类容易被误判为权限问题的事故：虚拟环境启动器失效。Windows 的 venv 中 python.exe 只是启动器，它按 pyvenv.cfg 里的 home 找基础解释器；'
      '当基础目录被清理后，所有 python 调用都会报找不到可执行文件。定位后通过修正 pyvenv.cfg 的三项路径（home / executable / command）解决，'
      '同 minor 系列版本间 ABI 兼容，无需重装依赖。此类经验已写入开发日志，作为部署文档的一部分交付。'),
    H2('4.4 前端工程'),
    P('四个页签共用一套设计变量：溯源问答、Agent 编排、联动阅读、引用图谱。为兼顾答辩现场的网络不确定性，ECharts 采用 CDN + 本地降级双路径；'
      '所有异步失败都有可读的中文提示（例如模型余额不足会提示「账户余额不足，充值后再使用翻译功能」，而不是抛出原始 JSON 解析错误），'
      '避免现场出现英文堆栈。'),
    PageBreak(),
]

# ============================================================ 五
s += [
    H1('五、验证结果与能力对照'),
    H2('5.1 功能验证数据'),
    TB([
        ['验证项', '输入 / 操作', '结果'],
        ['教材入库', '541 页 PDF 上传', '893 块，章节树完整（12 Transformers / 18 Diffusion / 19 RL）'],
        ['扫描件 OCR', 'v1_img 共 15 页', '28 块，标题作者正文引用号均可识别'],
        ['语义去重', 'v1 与 v7 同库', '相似度 0.8989，触发预警并提供替换'],
        ['精确数值问答', 'Transformer 用了多少 GPU', '答案与证据一致（8 卡 P100），携带页码锚点'],
        ['抗幻觉边界', '库中无 DDPM 原文时问训练目标', '给出 ELBO 与式 18.29 推导，并主动声明库中无原始论文'],
        ['Agent 清单', '我库里有哪些文献', '调用 list_documents 返回表格，不臆造'],
        ['Agent 对比', '指定两篇论文', '输出 4 项共同点 + 6 维度差异表'],
        ['Agent 外部推荐', '某方向最新综述', '调用 fetch_arxiv 分类推荐，主动剔除无关材料学文献'],
        ['Agent 自动综述', '整库发展脉络', '输出发展脉络 / 6 核心方法 / 5 未来方向 / 参考文献，并声明局限'],
        ['联动阅读', '教材第 1 页', '11 行版面框，首行坐标与原文对齐'],
        ['联动阅读（扫描）', '扫描件第 1 页', '55 行 OCR 版面框，标题与作者行对齐'],
        ['健康检查', 'GET /health', 'index_count=921，llm_configured=true'],
    ], widths=[30 * mm, 50 * mm, W - 80 * mm]),
    cap('表 8　功能验证结果'),
    H2('5.2 与评分维度的能力对照'),
    TB([
        ['评分维度', '本系统对应实现'],
        ['Agent 编排（9%）', 'Function Calling 自主决策，5 工具、5 轮循环，SSE 五类事件，思考轨迹可视化'],
        ['RAG 溯源（8%）', '混合检索 + 证据约束 Prompt + 引用编号校验 + 页码级证据面板 + 不足即拒答'],
        ['多模态解析（7%）', '矢量行级解析与扫描件 OCR 重建双通道；单页 OCR 版面框'],
        ['Function Calling（6%）', '工具 schema 明确、返回结构化、工具结果回填后再决策'],
        ['Prompt / Guardrails（5%）', 'RAG 四条硬约束 + 翻译五条契约 + 引用越界校验'],
        ['图论基石挖掘（10%）', '引用图 + PageRank 识别基石 / 边缘文献，前端力导向可视化'],
        ['RAG 创新（8%）', '章节感知切块 + 混合权重 + 语义去重 + 证据锚点'],
        ['联动阅读（7%）', 'bbox 归一化解耦渲染、扫描页 OCR 兜底、划词翻译与术语一致'],
        ['全栈工程（10%）', '单进程托管前后端、失败降级、稳定性铁律、可复现部署'],
    ], widths=[42 * mm, W - 42 * mm]),
    cap('表 9　评分维度对照'),
    H2('5.3 已知局限'),
    B('扫描件的检索质量受 OCR 识别率约束，公式与上下标容易识别偏差；当前以「每页一个 Section」重建，未做版面区块聚类。'),
    B('引用图谱依赖参考文献标题匹配，遇到标题改写严重（如缩写、译名）时可能漏边。'),
    B('翻译与问答均依赖外部模型服务的可用性；服务不可用时系统会给出明确的中文错误提示，但无法离线作答。'),
    B('Agent 编排上限 5 轮，超长综述任务可能需要人工追加一轮指令。'),
    PageBreak(),
]

# ============================================================ 六
s += [
    H1('六、业务闭环与差异化价值'),
    H2('6.1 完整业务闭环'),
    P('本系统覆盖「文献导入 → 结构化 → 检索 → 问答 → 对比 → 溯源 → 阅读 → 翻译」的完整链路，每一环都能独立使用，'
      '又共同服务于「把一篇论文读明白并写进自己的稿子」这一终点。用户不需要在五六个工具之间搬运 PDF：'
      '上传一次，后面所有环节共用同一份解析结果和同一套页码锚点。'),
    H2('6.2 与常见方案的差异'),
    TB([
        ['对比维度', '通用对话式大模型', '纯向量检索问答', '本系统'],
        ['定位到原文页码', '不能', '仅片段', '页码 + 章节路径 + 原文行'],
        ['扫描件 / 图片型 PDF', '无法解析', '通常不支持', 'OCR 重建 + 版面框兜底'],
        ['证据不足时', '倾向编造', '仍可能拼接片段', '明确拒答并说明库中无记述'],
        ['多步任务', '靠用户手动追问', '单轮检索', 'Function Calling 自主编排 5 轮'],
        ['领域结构洞察', '无', '无', '引用图 + PageRank 给基石文献'],
        ['英文阅读成本', '整段机翻、术语漂移', '无', '逐行对照 + 术语一致的学术翻译'],
    ], widths=[28 * mm, 40 * mm, 38 * mm, W - 106 * mm]),
    cap('表 10　差异化对比'),
    H2('6.3 可复用性'),
    P('所有模块都不绑定特定学科：换一个领域的 PDF 库，解析、切块、检索、编排、图论、阅读链路无需改动即可工作。'
      '对课题组而言，它可以作为「私有文献库 + 可信问答」的底座；对个人而言，它替代了「PDF 阅读器 + 翻译插件 + 文献管理 + 手动检索」四件套。'),
    PageBreak(),
]

# ============================================================ 七
s += [
    H1('七、局限与后续规划'),
    TB([
        ['优先级', '规划项', '预期收益'],
        ['高', '公式与表格的版面级还原（LaTeX 化），并在联动阅读中渲染公式块', '解决多模态解析中最难的一环，直接提升科研可用性'],
        ['高', '引用图反向扩展：用外部文献接口补全参考文献节点，形成跨库图谱', '让基石文献从库内推演升级为领域级推演'],
        ['中', '写作 Copilot：把证据片段组织成综述段落并保留引用角标', '打通从读到写的最后一公里'],
        ['中', '增量索引与后台任务队列，避免长文档上传阻塞交互', '提升多用户并发体验'],
        ['低', '多语言双向互译与自定义术语库', '适配非英语母语团队'],
    ], widths=[16 * mm, 80 * mm, W - 96 * mm]),
    cap('表 11　后续规划'),
    P('当前功能范围按「先保证核心链路可信，再扩展锦上添花」的原则确定：抗幻觉、可溯源、能处理扫描件决定系统是否可用；'
      'Agent 编排与图论决定它是否好用；联动阅读与翻译决定它是否愿意被天天打开。三者已全部落地，后续在此基础上做纵深。'),
    PageBreak(),
]

# ============================================================ 附录
s += [
    H1('附录 A　接口清单'),
    TB([
        ['方法', '路径', '说明'],
        ['GET', '/health', '健康检查（模型状态 / 索引块数 / LLM 配置）'],
        ['GET', '/api/documents', '文献清单（doc_id / 标题 / 块数）'],
        ['POST', '/api/documents/upload', '上传 PDF：解析 → 切块 → 去重 → 入库'],
        ['POST', '/api/qa', '证据约束问答（非流式）'],
        ['POST', '/api/qa/stream', '证据约束问答（SSE 流式）'],
        ['POST', '/api/agent/chat', 'Agent 自主编排（SSE：plan / tool_call / tool_result / delta / done）'],
        ['GET', '/api/graph', '引用图谱 + PageRank 排序 + 基石文献'],
        ['GET', '/api/documents/{doc_id}/page/{page_no}/image', '页面原图渲染（?dpi=，默认 144）'],
        ['GET', '/api/documents/{doc_id}/page/{page_no}/layout', '行级版面文本（bbox 归一化，扫描页自动 OCR 兜底）'],
        ['POST', '/api/translate', '学术翻译（text / target_lang / context，上限 4000 字符）'],
    ], widths=[14 * mm, 64 * mm, W - 78 * mm]),
    cap('表 12　HTTP 接口'),
    H1('附录 B　部署与复现步骤'),
    P('环境：Python 3.13；无 GPU 要求（CPU 即可）。依赖见 apps/api/requirements.txt，主要包含 fastapi、uvicorn、pymupdf、chromadb、'
      'sentence-transformers 与 torch、rapidocr-onnxruntime、networkx、openai。', 'ni'),
    CODE('# 1. 安装依赖\n'
         'cd apps/api\n'
         'python -m venv .venv\n'
         '.venv\\Scripts\\Activate.ps1\n'
         'pip install -r requirements.txt\n\n'
         '# 2. 配置密钥（从模板复制后填入）\n'
         'Copy-Item .env.example .env\n'
         '#   DEEPSEEK_API_KEY=...\n'
         '#   DEEPSEEK_BASE_URL=https://api.deepseek.com\n'
         '#   DEEPSEEK_MODEL=deepseek-chat\n\n'
         '# 3. 启动（首次会下载 BGE-M3 权重，约 2.2GB）\n'
         'uvicorn app.main:app --host 0.0.0.0 --port 8010\n\n'
         '# 4. 打开\n'
         '#   界面      http://127.0.0.1:8010\n'
         '#   接口文档  http://127.0.0.1:8010/docs\n'
         '#   健康检查  http://127.0.0.1:8010/health'),
    P('复现验证路径：上传 pdf/ 下的官方测试文件 → 观察解析块数与章节树 → 询问「Transformer 用了多少 GPU 训练」（验证溯源与数值一致性）→ '
      '询问「扩散模型训练目标」（验证多轮编排与拒答声明）→ 切换到联动阅读页签，在扫描件上点击任意行（验证 OCR 版面兜底与划词翻译）。', 'ni'),
    Spacer(1, 10 * mm),
    P('文档结束。代码与开发日志见仓库 github.com/YankeeLio/scholar-rag-agent。', 'cap'),
]

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                     topMargin=18 * mm, bottomMargin=20 * mm,
                     title='ScholarRAG Agent 技术文档', author='YankeeLio')
doc.addPageTemplates([PageTemplate(id='main',
                                   frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='n')],
                                   onPage=footer)])
doc.build(s)
print('PDF written:', OUT, os.path.getsize(OUT), 'bytes')
