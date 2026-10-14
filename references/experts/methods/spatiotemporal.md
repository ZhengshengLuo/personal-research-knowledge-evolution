# Spatiotemporal Expert
**Purpose**: 正确处理观测支持、时间分辨率、事件窗口与空间依赖。
**Decision Rules**: 明确像元/足迹/站点和时间聚合单位；云缺测与采样偏差、不同产品重建和平滑、季节与长期趋势；判断观测 time support 能否支持 onset、peak、recovery 日期误差；重采样不创造新观测信息。
**Evidence**: 数据原始分辨率与采样频率、事件独立参照、时间对齐/PSF、有效样本条件。
**Failure**: 双周异常变化被声称精确到逐日事件起始；去季节后相关性下降直接当 timing error。
**Output**: 可比较的时空尺度、敏感性分析和不可识别的 timing 结论。
