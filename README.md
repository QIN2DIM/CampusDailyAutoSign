# CampusDailyAutoSign

今日校园体温检测自动上报脚本（For:HainanUniversity） 

## :carousel_horse: 服务条款

> 1. 本项目仅为 **海南大学[海甸校区]** 学子提供服务；
> 3. 本项目 **开源免费** ，禁止任何人使用此项目及其分支提供任何形式的收费代理服务；
> 3. 本项目初衷在于帮助大家解决一些生活中的琐碎操作，避免一些客观原因导致的过失误伤。请各位**积极配合国家防疫战略并遵守异常体温上报相关规定**，如若身体异常，请及时联系辅导员/班主任/同学寻求帮助。

客官客官晚上好！不要吝啬手中的**一键三连**yo~:couple_with_heart_woman_woman:

## :kick_scooter: 使用说明

> 20级学子的签到任务不属于本项目的服务范畴，可能原因为：未使用今日校园API；

- 【方案一】使用`quick_register.py`提交表单(Python用户推荐)
- 【方案二】下载信息验证脚本（约10mb）[Download (github.com)](https://github.com/QIN2DIM/CampusDailyAutoSign/raw/main/register.zip)**||** [备用地址](http://t.qinse.top/cpdaily/register.zip)
- 【方案三】今日校园账号验证(测试中)

## :loudspeaker: 更新日志

- #### 2021.01.01 v_1.0.5.beta

    > **重要更新**

    - 根据[《关于启用"网上服务大厅”学生体温上报服务的通知》](https://kdocs.cn/l/sl02ofSPeh7r?f=111
        )本校学子的体温签到任务自2021年1月4日起不再依托今日校园第三方程序，故本项目将无限期停止维护。此外，作者将综合现实情况考虑是否为新需求提供解决方案（本人怀疑管理员同学只是在这里调用了今日校园的API）。
    - 据《科学》杂志2020年12月27日报道，英国科学家发现了一种被称为**B.1.1.7的新冠病毒变种**，变种病毒传播能力要比原始毒株高70%左右，而伦敦最近新冠感染病例超过60％都来自变种病毒。另外，《科学》杂志称，该变种病毒可能已经在全球各地广泛传播。

- #### **2020.12.10 v_1.0.4.beta**

    项目除虫~

- #### **2020.12.08 v_1.0.4.beta**

    > **功能迭代**

    任务分发，解决因多用户并发而操作过热导致的IP封禁问题

- #### **2020.12.08 v_1.0.3.beta**

    > **功能迭代**

    1. 解决原方案在获取`MOD_AUTH_CAS`时`session`状态码`405`的问题

    2. 修复消息通知功能异常的问题

- #### **2020.11.11 v_1.0.2.11162350.11**

  > **重要更新**

  1. 统一接口，部署`TrojanGoCDN`，集群解耦；
  2. 改用 `GoroutineEngine` +` ConfigPath` 单机架构驱动业务核心；
  3. 使用`Flask `+`Panel`接收验证数据；

  > **性能调优**

  1. 将`API`打包成`ActionBase`，引入`T-SC ESS`并行伸缩技术驱动`ActionGeneral`弹性业务；
  2. 编写`GeventSchedule`轻量化部署脚本（支持数据吞吐、弹性协程）；

## :world_map: 开源计划

- [ ] ~~植入太极~~
- [x] 用户管理
- [x] 弹性伸缩
- [x] 数据加密
- [x] 信息通知

## :e-mail: 联系我们

> 本项目由海南大学机器人与人工智能协会数据挖掘小组 **(A-RAI.DM)** 提供维护

- [Email](mailto:RmAlkaid@outlook.com?subject=CampusDailyAutoSign-ISSUE) **||** [Home](https://a-rai.github.io/)

