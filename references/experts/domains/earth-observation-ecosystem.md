# Earth Observation & Ecosystem Science — domain adapter
**Purpose**: 适用于 SIF/GPP、遥感观测、生态生理、干旱/热浪/复合事件等专题；不得自动加载到非相关学科。
**Conceptual distinctions**: 原始卫星足迹 SIF、经验/机器学习重建 SIF、SIFyield、GPP、NIRv、FAPAR、叶绿素荧光光化学/非光化学过程之间不能互换。植被结构、冠层辐射传输、太阳照明/观测角度、云筛选、时间聚合、物候和季节循环均影响信号。高温、土壤水分和 VPD 可能分别是暴露、媒介或混杂，须依据具体 estimand 判断。
**Decision Rules**: 每次声明响应 onset/peak/recovery 必须明确事件参考与植被参考、阈值/基线、时间分辨率及缺测处理；独立轨道观测不能简单称真值，通量站 GPP 也有模型/footprint 误差。产品是否检出响应、方向一致和时刻偏差属于不同保真度维度。
**Countercheck**: 对照直接 SIF vs CSIF/GOSIF/其他重建、独立生理参考和空间/时间支持；异常相关不等于时间偏差。
**Example**: 被同行审查识别的过度推断：特定归一化 TROPOMI SIF 在单次农业干旱中更早下降，不意味着全球重建产品在极端干热事件生命周期三个时刻都准确。
