# TODO 列表

## 1. 电量监控已完成
- [x] 在 `read_prompts.sh` 的运行 `genie-t2t-run` 时，两边添加了 batterystats 的代码
  - 使用 `cmd battery unplug` 和 `dumpsys batterystats --reset` 进行虚拟断电和清零
  - 运行后通过 `dumpsys batterystats --charged` 获取 shell UID 2000 的耗电量 (mAh)
  - 运行完成后使用 `cmd battery reset` 恢复电池状态

## 2. 内存监控待实现
- [ ] 需添加 meminfo 计算内存的内容
  - 不需要把 `genie-t2t-run` 放后台
  - 让它前台正常执行，同时并行启动一个"采样器"在后台
  - 使用 `dumpsys meminfo` 或更轻的 `/proc/<pid>/smaps_rollup` 采样 PSS
  - 计算内存峰值 (max PSS total) 和平均值 (avg PSS total)
  - 这样既能测内存峰值/均值，又不改变主进程的前台运行形态
  - 推荐使用 `/proc/<pid>/smaps_rollup` 方案，开销更小，干扰更少

## 3. IRT 分析待实现
- [ ] 需要添加测算子集 IRT 难度和区分度的代码
  - 实现项目反应理论 (Item Response Theory) 分析
  - 计算每个题目的难度参数 (difficulty parameter)
  - 计算每个题目的区分度参数 (discrimination parameter)
  - 分析不同学科子集的 IRT 特性
  - 生成 IRT 分析报告和可视化图表

## 实现优先级
1. **高优先级**: 内存监控功能 (2)
2. **中优先级**: IRT 难度和区分度分析 (3)

## 注意事项
- 内存采样和电量监控可能会相互影响，建议分别测试或使用轻量级的 `smaps_rollup` 方案
- IRT 分析需要足够的题目数量和答题数据才能得到可靠的参数估计
- 所有新增功能都应该与现有的性能统计系统兼容
