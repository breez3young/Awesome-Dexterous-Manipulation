# 灵巧操作文献导读与标签口径

2026-10-08 · 本次整理覆盖上传的 47 条 BibTeX 记录（去重后 44 篇），另加入 T-Rex 与 Morphometric Imitation。44 篇中有 4 篇已在原目录，因此新增 42 篇，连同保留的 12 篇补充文献，目录共 58 篇。

大多数总结依据所给 BibTeX 摘要与核验后的 arXiv 元数据；两篇新增论文和关键分类疑点进一步核对官方项目页或论文正文。这里是阅读导引，不将摘要整理表述为逐篇全文复现。每条记录的 `summary_basis`、`sources` 和必要的范围说明保存在目录数据中。

## 如何阅读这批文献

- **从示教到机器人动作**：ManipTrans、DexMachina、DexTrack、Dexplore、SPIDER、ConTrack、Morphometric Imitation 都关心人手与机器人之间的差异。阅读时区分：几何重定向、物理可行轨迹生成、参考跟踪策略、最终部署策略。参考轨迹是否含接触信息，与部署时是否需要触觉传感器是两个问题。
- **规模化策略与数据**：UniDex、DexGraspVLA、Dexora、DexHiL、T-Rex 体现预训练、跨本体动作空间与后训练路线。VLA、扩散/流策略和基座策略可以同时出现，标签不是互斥类别。
- **仿真到真实与控制**：Dactyl、DeXtreme、DexCtrl、DROP、SimToolReal 等分别提供随机化、控制器适应、在线规划、物体中心表示等路径。应分开考察是否成功部署、是否只验证特定物体，以及是否依赖特殊状态信息。
- **从单技能到复杂交互**：Bi-DexHands、Dynamic Handover、Sequential Dexterity、Mana、UniCross 覆盖双手协作、投掷接取、技能串联和工具操作。双手不必然意味着长时序；使用工具也不必然意味着操控带关节物体。
- **触觉如何进入控制闭环**：T-Rex 以高频触觉修正较慢的视觉动作规划；KineDex 将触觉示教与力控制结合；触觉手内操作工作则研究接触定位、滑动与旋转。硬件/传感器论文单独打资源标签，不能都视为已经训练好的通用策略。

## 类别命名

研究方向按论文的主要贡献归类。多指机器人控制系统归入两类 Dexterous Manipulation；触觉传感器、仿真和表征归入 **Tactile Sensing & Representation（触觉感知与表征）**。原先笼统的 Related Methods & Datasets 拆为三个具体方向：

| 研究方向 | 关注的问题 | 当前论文 |
| --- | --- | --- |
| Hand–Object Interaction（手物交互） | 人手动作、手物感知与交互建模 | HandX、DexYCB |
| Grasp Synthesis（抓取生成） | 抓取生成、质量评估与选择 | Dex-Net 4.0 |
| Policy Optimization（策略优化） | 通用策略训练目标与优化算法 | CPO |

**Dataset / benchmark** 仍是独立的资源标签，表示论文提供什么，不作为混合研究方向。每篇论文选择一个主要方向，具体方法和资源属性用可叠加的标签表达。例如采用强化学习的灵巧手系统仍属于 Dexterous Manipulation，只有以通用优化算法为主要贡献的工作才归入 Policy Optimization。

**Foundation policy** 专指经广泛预训练、可适配多个任务的基座策略，不再用 Foundations 泛指基础资源。拆分保留原有全部论文；旧分类链接自动选中三个新方向。

## 五组核心标签

| 标签组 | 对应问题 | 标签示例 |
| --- | --- | --- |
| Policy & learning | 控制策略如何得到？ | Reinforcement learning、Imitation learning、Vision-language-action、Foundation policy、Diffusion / flow policy、Model-based planning |
| Data & transfer | 技能数据从哪里来，如何迁移？ | Human motion transfer、Retargeting、Teleoperation、Sim-to-real、Cross-embodiment、Human-in-the-loop |
| Manipulation skills | 手具体完成什么能力？ | Dexterous grasping、In-hand manipulation、Bimanual coordination、Tool use、Long-horizon tasks、Articulated objects |
| Sensing & contact | 控制过程中实际观察什么？ | Tactile feedback、Vision、Proprioception、Force control |
| Research resources | 提供什么基础资源？ | Dataset / benchmark、Hardware / sensor、Survey |

研究方向标签之间为 OR，多组具体标签之间为 AND。例如 `Human motion transfer + Reinforcement learning` 找人类动作驱动的强化学习方法；`Tactile feedback + Bimanual coordination` 找双手触觉策略。标签数量按当前筛选组合计算，不代表整个领域的论文总数。

`Tactile feedback` 只用于机器人策略运行时实际读取触觉的工作。接触损失、仿真教师的接触状态、人类示教的接触力，都不自动等于这个标签。`Force control` 也与触觉观测分开。未在所读资料中确认的硬件或观测字段留空。

## 两篇补充论文

- **T-Rex: Tactile-Reactive Dexterous Manipulation**（2026-06-15）：将较慢的视觉动作生成与高频触觉修正结合，在共享的专家式架构中融合指尖力与形变信息。属于真实双手触觉灵巧操作。[论文](https://arxiv.org/abs/2606.17055) · [项目](https://tactile-reactive-dexterous.github.io/)
- **Morphometric Imitation**（2026-09-23）：利用形态与接触相关的信息构造跨本体模仿，再将仿真教师蒸馏为可部署学生。部署学生以点云和本体状态为输入，因此不标记为运行时触觉策略。[论文](https://arxiv.org/abs/2609.28660) · [项目](https://morphometricimitation.github.io/)

## 数据校订与统计边界

- 合并三组重复记录：SimToolReal、Object-Centric Dexterous Manipulation from Human Motion Data、ManipTrans。原始 Bib key 仍保留在 `bib_keys` 中，47 条输入都有对应记录。
- 批量核验 43 个不同的 arXiv ID 的首次提交日期；非 arXiv 的 Dex-Net 4.0 使用期刊出版日期。以下年份不再沿用 Bib 中的修订年份。

| 论文 | Bib 年份 | 首次公开年份 |
| --- | --- | --- |
| SPIDER: Scalable Physics-Informed Dexterous Retargeting | 2026 | 2025 |
| In-Hand Manipulation of Articulated Tools with Dexterous Robot Hands with Sim-to-Real Transfer | 2026 | 2025 |
| UniBYD: A Unified Framework for Learning Robotic Manipulation Across Embodiments Beyond Imitation of Human Demonstrations | 2026 | 2025 |
| DeXtreme: Transfer of Agile In-hand Manipulation from Simulation to Reality | 2024 | 2022 |
| Learning Dexterous In-Hand Manipulation | 2019 | 2018 |
| RetrDex: Efficient Object Retrieval in Cluttered Scenes with a Dexterous Hand | 2026 | 2025 |
| DROP: Dexterous Reorientation via Online Planning | 2025 | 2024 |

Dex-Net 4.0 使用平行夹爪/吸盘；DexYCB 是人手物体交互数据集；HandX 以人类双手动作生成为主；CPO 是通用强化学习研究。它们分别归入 Grasp Synthesis、Hand–Object Interaction、Hand–Object Interaction 和 Policy Optimization，保留相邻资源的范围说明。钢琴触觉工作明确标记为仿真研究。Morphometric Imitation、CHORD 未因训练中的接触信息而误标为触觉部署策略。

Stats 只读取正式目录，不包含每日候选。图表按首次公开日期计算；筛选状态会同时作用于统计，URL 可保存这些标签与 Stats 页面。多标签统计的总和可能超过论文数；它反映个人收集结构，不代表全领域增长率或方法优劣。

## 本次 46 篇工作逐条总结

### Dexterous Manipulation

**[Morphometric Imitation: From Morphology and Contact Aware Hand Retargeting to Sim-to-Real Visuomotor Policy](https://arxiv.org/abs/2609.28660)** · 2026-09-23

先通过形态与接触匹配重定向人手动作，再用残差强化学习生成物理可行的示教，最后蒸馏为点云视觉运动策略。方法比较三种手构型，并在 Sharpa Wave 上零样本部署；接触信息用于仿真训练，实机策略读取视觉和本体状态。

范围说明：接触状态是仿真残差强化学习教师的特权信息及奖励依据。部署学生策略仅以当前和前一帧点云、本体感知与上一动作命令为输入，不能归为运行时触觉反馈。三种手用于仿真比较；真实实验为 KUKA iiwa14 搭配 Sharpa Wave 和 RealSense L515。

**[UniCross: Unified Cross-Skill Dexterous Manipulation Synthesis](https://arxiv.org/abs/2607.28198)** · 2026-07-30

把抓取、搬移、手内旋转与手内平移四种技能统一到相同状态、动作空间和目标结构中，再蒸馏为单一跨技能策略。方法旨在解决独立技能难以衔接的问题，展示长时程组合、未知物体泛化、扰动鲁棒性，以及不同机器人手构型间迁移。

范围说明：所提供摘要未指明验证环境为仿真还是实机，因此 evaluation 暂记 Not specified。

**[Towards Human-level Dexterous Teleoperation](https://arxiv.org/abs/2607.11481)** · 2026-07-13

将操作者意图转为手物协同跟踪子目标，再由强化学习控制器执行底层接触动作。稀疏目标与密集跟踪奖励结合，借助动作遮蔽和域随机化迁移至实机；两种灵巧手完成重定向及长时程工具操作，采集的示教还能训练自主策略。

**[Cross-Embodiment Robot Manipulation via a Unified Hand Action Space](https://arxiv.org/abs/2607.03570)** · 2026-07-03

将手部动作表示为标准球面变形，再以级联逆运动学映射到各手型；在共享动作空间训练强化学习策略，实现立方体手内重定向及跨形态迁移。

范围说明：列出的手型涵盖仿真与真机研究对象；MANO 是人手模型，不能视为机器人硬件。

**[Learning Dexterous Manipulation Using Contact Wrench Guidance From Human Demonstration](https://arxiv.org/abs/2607.00033)** · 2026-06-22

以物体中心的接触力与力矩空间对齐人类和机器人动作，用诱导物体运动的相似性引导强化学习。方法覆盖刚体和关节物体的长时程双手操作，建立大规模仿真基准并展示真实迁移；示教中的力旋量指导不等于部署时使用触觉传感器。

范围说明：接触力旋量由人类示教引导强化学习；所提供摘要未确认真实执行阶段采用触觉传感器，不据此标记触觉反馈。

**[Mana: Dexterous Manipulation of Articulated Tools](https://arxiv.org/abs/2606.13677)** · 2026-06-11

借鉴动画制作，把程序生成的抓取关键帧，经运动规划与强化学习转为操作轨迹。每件工具只需少量鼠标操作标注功能可供性，即可较自动地生成数据；在四种不同尺度与关节类型的工具上验证抓取和手内操作的零样本仿真迁移。

**[ConTrack: Constrained Hand Motion Tracking with Adaptive Trade-off Control](https://arxiv.org/abs/2606.03177)** · 2026-06-02

将物体轨迹跟踪作为约束，以在线对偶更新调节任务准确度与手部动作保真度，并复用可达中间状态稳定长序列学习，验证仿真与真机迁移。

**[Dexora: Open-source VLA for High-DoF Bimanual Dexterity](https://arxiv.org/abs/2605.18722)** · 2026-05-18

面向双臂双手高自由度操作，结合外骨骼背包和头显手部追踪采集遥操作数据，并配套仿真数字孪生。训练融合合成轨迹与真实示教，以离线判别器降低低质量片段权重，学习扩散 Transformer 策略，评估灵巧任务及跨构型泛化。

**[Towards Robotic Dexterous Hand Intelligence: A Survey](https://arxiv.org/abs/2605.13925)** · 2026-05-13

从硬件、感知、控制学习、数据与评估四方面梳理机器人灵巧手研究，讨论驱动与传动、力能力、柔顺性和系统集成的取舍。综述将方法演进与构型、传感配置及训练评测条件联系起来，帮助理解不同工作的可比性与未来挑战。

**[DexSynRefine: Synthesizing and Refining Human-Object Interaction Motion for Physically Feasible Dexterous Robot Actions](https://arxiv.org/abs/2605.05925)** · 2026-05-07

先以运动流形流基元生成耦合人手—物体轨迹，再用任务空间残差强化学习落实物理执行，并从本体感知历史推断接触动力学以适应真机。

范围说明：从本体感知历史估计接触动力学，不据此归入使用触觉传感器的工作。

**[BiDexGrasp: Coordinated Bimanual Dexterous Grasps across Object Geometries and Sizes](https://arxiv.org/abs/2604.06589)** · 2026-04-08

用区域初始化与解耦力闭合优化合成双手抓取数据，再以双手协调模块和几何尺寸自适应生成模型预测未见物体的抓取，包含仿真与真机验证。

**[UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://arxiv.org/abs/2603.22264)** · 2026-03-23

将第一视角人类视频重定向为多种灵巧手轨迹，以功能对齐动作空间训练 3D VLA；结合去人手点云及便携 RGB-D 采集支持跨手型工具操作。

**[DexHiL: A Human-in-the-Loop Framework for Vision-Language-Action Model Post-Training in Dexterous Manipulation](https://arxiv.org/abs/2603.09121)** · 2026-03-10

将机械臂与多指手的人类即时纠正统一接入 VLA 后训练，并优先采样纠正片段，提升真实机器人复杂接触任务的执行可靠性。

**[SimToolReal: An Object-Centric Policy for Zero-Shot Dexterous Tool Manipulation](https://arxiv.org/abs/2602.16863)** · 2026-02-18

在程序生成的工具形状上训练统一物体位姿目标策略，减少逐任务奖励及物体建模设计，零样本迁移到真实工具的抓握、手内转动与施力操作。

**[DexImit: Learning Bimanual Dexterous Manipulation from Monocular Human Videos](https://arxiv.org/abs/2602.10105)** · 2026-02-10

从单目人类视频重建手物交互，再进行子任务分解、双手调度、机器人轨迹合成与数据增强，自动生成物理可行的机器人示教。输入可来自互联网或视频生成模型，面向切苹果、制作饮品与叠杯等任务，支持零样本真实部署。

范围说明：摘要描述零样本真实部署的数据生成路线，但未给出明确实机评估结果；evaluation 暂记 Not specified，待进一步核查实验部分。

**[UniBYD: A Unified Framework for Learning Robotic Manipulation Across Embodiments Beyond Imitation of Human Demonstrations](https://arxiv.org/abs/2512.11609)** · 2025-12-12

用统一形态表示连接不同手型，通过退火奖励的 PPO 从人类示范引导过渡到机器人自身探索，并以影子引擎抑制早期状态漂移，配套 UniManip 基准。

范围说明：覆盖两指夹爪及三指、五指手；项目页补充了真实平台迁移结果。

**[SPIDER: Scalable Physics-Informed Dexterous Retargeting](https://arxiv.org/abs/2511.09484)** · 2025-11-12

以人类运动提供任务结构，通过物理采样生成动态可行轨迹，无需逐任务优化策略；支持多种手型与人形机器人，并可扩增负载、接触条件或直接部署。

范围说明：当前 arXiv 修订及项目页已补充真机部署；物理接触约束不等于运行时触觉传感。

**[DexFlyWheel: A Scalable and Self-improving Data Generation Framework for Dexterous Manipulation](https://arxiv.org/abs/2509.23829)** · 2025-09-28

DexFlyWheel 从少量种子示范出发，循环执行模仿学习、残差强化学习、仿真轨迹收集与数据增强，使后续训练覆盖更多场景。该闭环利用已有策略持续生成和改进数据，论文展示了复杂任务泛化，以及借助数字孪生迁移后的真实双臂抬举效果。

**[Dexplore: Scalable Neural Control for Dexterous Manipulation from Reference-Scoped Exploration](https://arxiv.org/abs/2509.09671)** · 2025-09-11

以自适应空间范围把不精确动作捕捉转为软约束，在统一强化学习过程中联合重定向与跟踪，再蒸馏为视觉条件生成控制器用于真实机器人。

**[DexMachina: Functional Retargeting for Bimanual Dexterous Manipulation](https://arxiv.org/abs/2505.24853)** · 2025-05-30

以物体状态而非纯手部姿态为目标，让虚拟物体控制器逐渐减弱、机器人策略逐步接管，学习双手长时程关节物体操作，并用仿真基准比较手型能力。

范围说明：仿真功能重定向与硬件设计比较；接触奖励不代表使用真实触觉传感器。

**[DexCtrl: Towards Sim-to-Real Dexterity with Adaptive Controller Learning](https://arxiv.org/abs/2505.00991)** · 2025-05-02

针对低层控制器动力学不匹配，联合学习动作与控制参数，利用轨迹和控制历史在线自适应调参，改善不同受力条件下的灵巧操作仿真到现实迁移。

范围说明：关注控制参数与受力交互；摘要未明确触觉传感器输入，未标注为触觉策略。

**[ManipTrans: Efficient Dexterous Bimanual Manipulation Transfer via Residual Learning](https://arxiv.org/abs/2503.21860)** · 2025-03-27

先预训练通用轨迹模仿器，再以交互约束微调残差模块，将人类双手演示转成仿真机器人技能，并构建支持笔帽扣合、瓶盖旋拧的 DexManipNet。

范围说明：摘要中的主要验证是仿真技能转移；可支持下游真机部署，不等同于已报告真机策略评测。

**[DexGraspVLA: A Vision-Language-Action Framework Towards General Dexterous Grasping](https://arxiv.org/abs/2502.20900)** · 2025-02-28

DexGraspVLA 将预训练视觉语言规划器与扩散动作控制器结合，通过基础模型把变化的语言和视觉输入转换为较稳定的表示，再用模仿学习训练抓取。系统支持杂乱场景、长指令、失败恢复及非抓取式预调整，在论文未见场景测试中报告超过 90% 的抓取成功率。

**[RetrDex: Efficient Object Retrieval in Cluttered Scenes with a Dexterous Hand](https://arxiv.org/abs/2502.18423)** · 2025-02-25

RetrDex 面向被杂物遮挡的目标检索，将推、拨、搅动等动作与抓取联合学习。策略通过空间关系表示理解遮挡，在并行仿真中训练教师，再从成功轨迹学习用于部署的学生策略。实验覆盖不同杂乱配置，并展示真实手臂系统的零样本迁移。

**[DexTrack: Towards Generalizable Neural Tracking Control for Dexterous Manipulation from Human References](https://arxiv.org/abs/2502.09614)** · 2025-02-13

将强化学习与模仿学习结合训练通用跟踪控制器，再以控制器引导同伦优化解决困难轨迹、扩充成功示范，循环提升人类动作参考的仿真及真机执行。

**[Object-Centric Dexterous Manipulation from Human Motion Data](https://arxiv.org/abs/2411.04005)** · 2024-11-06

将人类手部动作中的结构拆分为高层腕部轨迹与低层手指控制：生成模型根据物体目标状态产生腕部参考，强化学习负责适配机器人形态并实现接触交互。方法在多种日常物体上测试，并迁移至真实双手系统，兼顾人体动作先验与机器人可执行性。

**[DROP: Dexterous Reorientation via Online Planning](https://arxiv.org/abs/2409.14562)** · 2024-09-22

将手内立方体重定向视为在线规划问题，用视觉估计物体位姿，再以采样式预测控制实时搜索接触动作。真实机器人实验分析架构选择和鲁棒性因素，表明这种无需预先训练操作策略的方案可达到与既有强化学习方法相近的表现。

范围说明：采用在线规划进行手内重定向；首次公开于 2024 年，Bib 中的 2025 年对应后续版本。

**[Dynamic Handover: Throw and Catch with Bimanual Hands](https://arxiv.org/abs/2309.05655)** · 2023-09-11

Dynamic Handover 用多智能体强化学习协调两套手臂系统完成抛掷与接取。为降低仿真到现实差距，加入物体轨迹预测模型，使接取端根据飞行趋势实时调整动作。策略在仿真中训练，并迁移到真实机器人，对多种物体展示动态交接能力。

**[Sequential Dexterity: Chaining Dexterous Policies for Long-Horizon Manipulation](https://arxiv.org/abs/2309.00987)** · 2023-09-02

通过转移可行性函数连接多个强化学习子策略，既微调技能间的衔接，也在执行时决定切换与失败恢复。方法提升长时序任务成功率并实现零样本现实迁移。其真实积木演示中最后向下压合由脚本完成，应区分已学习的策略衔接与完整自主装配。

范围说明：真实积木实验最后的下压插入由脚本完成，策略学习结果不应解读为全流程自主装配。

**[AnyTeleop: A General Vision-Based Dexterous Robot Arm-Hand Teleoperation System](https://arxiv.org/abs/2307.04577)** · 2023-07-10

AnyTeleop 用摄像头捕捉人手与手腕动作，通过统一遥操作流程支持不同机械臂、灵巧手、仿真器和相机配置。系统减少对特定硬件组合的依赖，同时在真实遥操作与后续模仿学习实验中保持较好的任务表现，为跨平台采集操作数据提供接口。

**[DexPBT: Scaling up Dexterous Manipulation for Hand-Arm Systems with Population Based Training](https://arxiv.org/abs/2305.12127)** · 2023-05-20

DexPBT 在 GPU 并行仿真中用去中心化种群训练扩大强化学习探索。多个策略协同搜索训练设置，学习单臂与双臂的重抓取、抛掷和物体重定向。重点在于提升高维手臂系统的探索能力与训练效果，论文展示的是仿真实验。

范围说明：论文评估集中于仿真手臂系统；不据此标记已完成真实机器人迁移。

**[Learning a Universal Human Prior for Dexterous Manipulation from Human Preference](https://arxiv.org/abs/2304.04602)** · 2023-04-10

通过人类对机器人动作视频的偏好训练通用奖励模型，再用它约束强化学习策略，使动作更符合人的偏好。方法不需要人工动作示范，而是在多轮策略生成与反馈收集中学习先验，并在二十项仿真双手任务上检验行为改善及未见任务泛化。

范围说明：偏好来自人对视频的比较，非触觉反馈；实验覆盖仿真任务。

**[DeXtreme: Transfer of Agile In-hand Manipulation from Simulation to Reality](https://arxiv.org/abs/2210.13702)** · 2022-10-25

DeXtreme 同时训练灵巧操作策略和视觉物体位姿估计器，通过丰富的仿真条件提升二者的鲁棒性。系统在真实 Allegro Hand 上依靠摄像头执行敏捷的物体重定向，说明可靠感知与训练环境多样性需要共同设计，才能实现有效的仿真到现实迁移。

**[Towards Human-Level Bimanual Dexterous Manipulation with Reinforcement Learning](https://arxiv.org/abs/2206.08686)** · 2022-06-17

Bi-DexHands 提供基于 Isaac Gym 的双手灵巧操作仿真基准，覆盖多种任务与大量物体，并比较单智能体、多智能体、离线、多任务和元强化学习。实验显示单项技能可以有效学习，但技能复用、多任务掌握及少样本适应仍存在明显困难。

范围说明：双手操作仿真基准；文中与儿童年龄的类比不代表机器人具备同等通用智能。

**[Transferring Dexterous Manipulation from GPU Simulation to a Remote Real-World TriFinger](https://arxiv.org/abs/2108.09779)** · 2021-08-22

使用 GPU 仿真训练三指机器人，将立方体移动至指定的位置与姿态。方法以关键点表示物体位姿，同时用于策略观察和奖励，结合域随机化改善训练与迁移效果。策略部署到远程真实 TriFinger 系统，在论文设定的任务中取得 83% 成功率。

**[Solving Rubik's Cube with a Robot Hand](https://arxiv.org/abs/1910.07113)** · 2019-10-16

通过自动域随机化逐步扩大仿真环境难度与多样性，联合增强手部控制和视觉状态估计的现实鲁棒性。带记忆的策略能够在执行中适应环境，配合专门搭建的机械手系统完成魔方翻转与转面等连续操作，展示复杂多阶段操作中的仿真迁移。

**[DexPilot: Vision Based Teleoperation of Dexterous Robotic Hand-Arm System](https://arxiv.org/abs/1910.03135)** · 2019-10-07

DexPilot 从摄像头观察到的裸手动作控制高维机械臂与灵巧手系统，以较低成本完成无需手套的遥操作。不同操作者执行抓取、手内调整和多阶段任务，并可采集后续策略学习所需的状态动作数据。项目明确指出演示依靠视觉，未向操作者回传触觉。

范围说明：遥操作依靠视觉，项目明确未向操作者回传触觉；自主策略学习是其后续数据用途。

**[Learning Dexterous In-Hand Manipulation](https://arxiv.org/abs/1808.00177)** · 2018-08-01

在物理参数与视觉外观随机化的仿真环境中训练强化学习策略，随后直接迁移到真实 Shadow Hand，利用视觉完成物体重定向。训练无需人工示范，手指换步、多指协调以及借助重力等行为自然出现，奠定了大规模仿真学习灵巧操作的重要路线。

### Tactile Dexterous Manipulation

**[T-Rex: Tactile-Reactive Dexterous Manipulation](https://arxiv.org/abs/2606.17055)** · 2026-06-15

以较慢的视觉语言动作规划搭配快速异步触觉修正，通过时序触觉编码和混合 Transformer 处理实时接触变化。结合人类视频预训练与触觉机器人示教，在双 Sharpa Wave 手上利用指尖力及形变信号，完成十二项真实接触敏感任务。

**[Closing the Reality Gap: Zero-Shot Sim-to-Real Deployment for Dexterous Force-Based Grasping and Manipulation](https://arxiv.org/abs/2601.02778)** · 2026-01-06

将密集触觉观测与电流估计的关节力矩结合，用快速触觉仿真、电流力矩标定和非理想执行器建模缩小现实差距。非对称演员—评论家策略完全在仿真中训练，随后无需真机微调即可在五指手上跟踪抓握力指令并完成物体手内重定向。

**[In-Hand Manipulation of Articulated Tools with Dexterous Robot Hands with Sim-to-Real Transfer](https://arxiv.org/abs/2509.23075)** · 2025-09-27

在仿真策略上加入真机示范学习的细化模块，以交叉注意力融合全手触觉、力矩、本体感知与动作意图，适应剪刀、钳子等关节工具并调节接触力。

**[Towards Learning to Play Piano with Dexterous Hands and Touch](https://arxiv.org/abs/2106.02040)** · 2021-06-03

让灵巧手依据机器可读乐谱，在仿真钢琴上从零学习按键、节奏、力度与指法。课程学习和触觉增强奖励帮助探索，论文还比较触觉输入与训练设计的作用；实验使用带模拟 DIGIT 触觉传感器的 Allegro 手，尚属仿真验证。

范围说明：仅仿真验证。全文 III-A 的观测空间明确包括每根手指近期 DIGIT 触觉图及关节、腕部状态，因此触觉不仅用于奖励，也实际输入策略。使用 Allegro 手与 TACTO 模拟触觉传感器。

### Hand–Object Interaction

**[HandX: Scaling Bimanual Motion and Interaction Generation](https://arxiv.org/abs/2603.28766)** · 2026-03-30

整合并新增双手动作捕捉数据，以接触和手指运动特征辅助语言标注，评测扩散与自回归生成模型；属于人类动作资源，未据此声称机器人控制能力。

范围说明：人类双手动作数据、标注及生成基准；不据此认定为已部署的机器人策略。

**[DexYCB: A Benchmark for Capturing Hand Grasping of Objects](https://arxiv.org/abs/2104.04631)** · 2021-04-09

DexYCB 记录人手抓握物体的交互数据，评测目标与关键点检测、物体六维位姿、人手三维姿态，并研究人机交接中的安全抓取生成。它为灵巧操作提供感知基准和人体交互数据，作为相关数据基础收录，不等同于已部署的多指机器人操作策略。

范围说明：相关数据与感知基础：主体是人手交互数据，不应视为多指机器人控制系统。

### Grasp Synthesis

**[Learning ambidextrous robot grasping policies](https://www.science.org/doi/10.1126/scirobotics.aau4984)** · 2019-01-16

Dex-Net 4.0 从大量合成深度图与解析抓取模型中学习，在平行夹爪和吸盘两种末端执行器之间选择合适抓取。域随机化帮助策略迁移至真实机器人，实现可靠的箱内取物。这里的双能抓取指异构夹具选择，因此作为相关基础收录，而非多指灵巧手控制。

范围说明：相关抓取基础：平行夹爪与吸盘的异构选择，并非多指灵巧手控制；日期为期刊发表日。

### Policy Optimization

**[Rethinking Policy Diversity in Ensemble Policy Gradient in Large-Scale Reinforcement Learning](https://arxiv.org/abs/2603.01741)** · 2026-03-02

分析策略集成中多样性对探索效率的影响，通过策略间 KL 约束调节探索范围，避免过度分散破坏训练稳定性。方法在包括灵巧操作的多个任务上提升样本效率与最终表现；其贡献属于通用强化学习方法，作为相关基础工作收录。

范围说明：通用大规模强化学习策略集成方法，灵巧操作是评测任务之一，作为相邻的操作学习基础工作收录。

