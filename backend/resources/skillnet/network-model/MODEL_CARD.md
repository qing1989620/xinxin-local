# SkillNet / S1 路由研究候选

模型：`network-b9e7622390ddc716`。状态：**研究对照，未获准自动更新正式排序**。

这是冻结 E5 编码器上的低秩匹配适配器，负责问题与技能的相关度排序；不是通用语言模型，不输出执行成功概率。选中版本为文本适配 / seed 29 / 微调 epoch 7。架构含 110,596 个可训练参数，选中文本版本不启用图消息分支。

## 随克隆直接提供

- `model.npz`：纯数值权重，SHA-256 `b9e7622390ddc71633586f71bce15960940801808693eea2189d2835c267f3f5`。
- `manifest.json`：模型结构、固定编码器版本、数据协议指纹。
- `catalog.npz`：已公开的产品技能目录表示与邻居特征；目录正文发生变化时预览跳过过期版本。
- `catalog.json`：技能名称、正文指纹和表示文件指纹。
- `assets/network-research/v1/`：四组预训练与验证集选出的微调检查点、训练曲线、原始冻结协议、数据切分检查及研究门禁证据。

NumPy 推理无需 PyTorch。训练复现使用可选的 `requirements-training.txt`。交付清单验证以上文件，`/api/personal` 报告候选状态。

## 证据与限制

在冻结 Gym 测试上 Recall@5 为 35.94% → 59.53%；另一来源的缩减候选池为 55.93% → 50.16%，存在负迁移。研究审计 7/12，能力奖励 0。图消息版本没有优于文本适配。原始协议没有冻结奖励政策指纹，不能事后追补；它已原样保留。

不用于宣称因果技能贡献、执行成功率或完整 80K SkillRouter 复现。详细实验与准入边界见 [研究报告](../../docs/learned-network-research.md)。

## 来源与第三方材料

- 编码器：[Xenova/multilingual-e5-small](https://huggingface.co/Xenova/multilingual-e5-small)，固定 revision `761b726dd34fb83930e26aab4e9ac3899aa1fa78`。原模型为 [intfloat/multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small)，模型卡标注 MIT；原编码器通过既有独立模型包交付，不混入本适配权重。
- 训练任务：[SkillNet-Gym](https://github.com/zjunlp/SkillNet-Gym)，固定 commit `54d0081041bf341496b76c50475342d69af306d5`，仓库许可为 Apache-2.0。使用其公开任务的文本及参考包标签；未在本数值包中重新分发原任务、脚本和参考正文。
- 产品技能：使用仓库既有的来源与许可登记，见 `seed/community/`。其许可不因被编码或参与训练而重新指定。
- 外部评估：[SkillRouter-Eval-Core](https://huggingface.co/datasets/pipizhao/SkillRouter-Eval-Core)，固定 revision `20a03920e7f08d76b67af367350d25ef4468198e`，只用于首轮外部评估，未进入该候选梯度。

公开数值研究产物不等于对所有上游材料商业使用范围的统一授权。来源许可应分别遵守；个人用户历史、身份、密钥和临时下载凭证不在交付中。
