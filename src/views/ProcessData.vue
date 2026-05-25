<template>
  <Header></Header>
  <div class="process-data">
    <!-- 面包屑导航 -->
    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置： <router-link to="/">首页</router-link> >
          <span>冶金工艺数据</span>
        </p>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="container main-content">
      <div class="data-aggregation">
        <!-- 左侧导航栏 -->
        <div class="data-aggregation-left">
          <div class="left-sub-nav-box">
            <!-- 工艺概览 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'overview'}"
                @click="switchModule('overview')">
              <dt class="index1">
                <a href="javascript:void(0)">工艺概览</a>
              </dt>
            </dl>

            <!-- 工艺数据库 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'database'}"
                @click="switchModule('database')">
              <dt class="index2">
                <a href="javascript:void(0)">工艺数据库</a>
              </dt>
            </dl>

            <!-- 工艺优化 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'optimization'}"
                @click="switchModule('optimization')">
              <dt class="index3">
                <a href="javascript:void(0)">工艺优化</a>
              </dt>
            </dl>

            <!-- 能效分析 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'energy'}"
                @click="switchModule('energy')">
              <dt class="index4">
                <a href="javascript:void(0)">能效分析</a>
              </dt>
            </dl>

            <!-- 质量分析 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'quality'}"
                @click="switchModule('quality')">
              <dt class="index5">
                <a href="javascript:void(0)">质量分析</a>
              </dt>
            </dl>

            <!-- 工艺报表 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'reports'}"
                @click="switchModule('reports')">
              <dt class="index6">
                <a href="javascript:void(0)">工艺报表</a>
              </dt>
            </dl>
          </div>
          <div class="m-nav-but">点击展开菜单</div>
        </div>

        <!-- 右侧内容展示区 -->
        <div class="data-aggregation-right">

          <!-- ==================== 概览模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'overview'">
            <div class="module-header">
              <h2><i class="fas fa-tachometer-alt"></i> 冶金工艺数据概览</h2>
              <p class="module-desc">冶金生产过程数据采集、分析与优化决策支持系统</p>
            </div>

            <!-- 关键指标 -->
            <div class="echarts-data-num">
              <div class="data-item">
                <dl>
                  <dt>工艺参数记录</dt>
                  <dd>15,200+</dd>
                  <dd class="trend up">实时更新</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-sliders-h fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>工艺路线</dt>
                  <dd>28+</dd>
                  <dd class="trend up">持续完善</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-route fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>能效指标</dt>
                  <dd>45+</dd>
                  <dd class="trend down">优化改善</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-bolt fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>质量控制点</dt>
                  <dd>120+</dd>
                  <dd class="trend up">持续监控</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-clipboard-check fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>设备状态点</dt>
                  <dd>850+</dd>
                  <dd class="trend up">实时监测</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-cogs fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>优化案例</dt>
                  <dd>95+</dd>
                  <dd class="trend up">持续增加</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-chart-line fa-2x"></i>
                </div>
              </div>
            </div>

            <!-- 主要工艺流程 -->
            <div class="application-scenarios mt30">
              <div class="section-header">
                <h3><i class="fas fa-industry"></i> 主要工艺流程</h3>
                <p>冶金生产过程关键工艺环节</p>
              </div>

              <div class="scenarios-grid">
                <div class="scenario-card">
                  <div class="scenario-icon">
                    <i class="fas fa-fire"></i>
                  </div>
                  <div class="scenario-content">
                    <h4>高炉炼铁</h4>
                    <p>高炉冶炼过程参数监控与优化</p>
                    <div class="scenario-tags">
                      <span class="tag">温度控制</span>
                      <span class="tag">配料优化</span>
                    </div>
                  </div>
                </div>

                <div class="scenario-card">
                  <div class="scenario-icon">
                    <i class="fas fa-tint"></i>
                  </div>
                  <div class="scenario-content">
                    <h4>转炉炼钢</h4>
                    <p>转炉吹炼过程控制与终点预测</p>
                    <div class="scenario-tags">
                      <span class="tag">吹炼控制</span>
                      <span class="tag">终点预测</span>
                    </div>
                  </div>
                </div>

                <div class="scenario-card">
                  <div class="scenario-icon">
                    <i class="fas fa-water"></i>
                  </div>
                  <div class="scenario-content">
                    <h4>连铸工艺</h4>
                    <p>连铸过程温度、拉速、冷却控制</p>
                    <div class="scenario-tags">
                      <span class="tag">凝固控制</span>
                      <span class="tag">质量控制</span>
                    </div>
                  </div>
                </div>

                <div class="scenario-card">
                  <div class="scenario-icon">
                    <i class="fas fa-compress-alt"></i>
                  </div>
                  <div class="scenario-content">
                    <h4>轧制工艺</h4>
                    <p>热轧、冷轧工艺参数优化</p>
                    <div class="scenario-tags">
                      <span class="tag">轧制力</span>
                      <span class="tag">温度控制</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 数据库模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'database'">
            <div class="module-header">
              <h2><i class="fas fa-database"></i> 工艺数据库</h2>
              <p class="module-desc">冶金生产过程参数、工艺规程与操作标准</p>
            </div>

            <!-- 数据查询 -->
            <div class="search-section">
              <div class="section-header">
                <h3><i class="fas fa-search"></i> 工艺数据查询</h3>
                <p>选择查询条件，检索冶金工艺数据</p>
              </div>

              <div class="search-form">
                <div class="form-row">
                  <div class="form-group">
                    <label for="process-type"><i class="fas fa-cogs"></i> 工艺类型</label>
                    <select id="process-type" v-model="searchParams.processType">
                      <option value="">选择工艺类型</option>
                      <option value="blast-furnace">高炉炼铁</option>
                      <option value="converter">转炉炼钢</option>
                      <option value="continuous-casting">连铸</option>
                      <option value="rolling">轧制</option>
                      <option value="heat-treatment">热处理</option>
                    </select>
                  </div>

                  <div class="form-group">
                    <label for="parameter-type"><i class="fas fa-sliders-h"></i> 参数类型</label>
                    <select id="parameter-type" v-model="searchParams.parameterType">
                      <option value="">选择参数类型</option>
                      <option value="temperature">温度参数</option>
                      <option value="pressure">压力参数</option>
                      <option value="flow">流量参数</option>
                      <option value="composition">成分参数</option>
                      <option value="time">时间参数</option>
                    </select>
                  </div>

                  <div class="form-group">
                    <label for="date-range"><i class="fas fa-calendar"></i> 时间范围</label>
                    <div class="range-input">
                      <input type="date" v-model="searchParams.dateStart">
                      <span>至</span>
                      <input type="date" v-model="searchParams.dateEnd">
                    </div>
                  </div>
                </div>

                <div class="form-actions">
                  <button class="btn-search" @click="searchProcessData">
                    <i class="fas fa-search"></i> 查询数据
                  </button>
                  <button class="btn-reset" @click="resetSearch">
                    <i class="fas fa-redo"></i> 重置条件
                  </button>
                </div>
              </div>
            </div>

            <!-- 查询结果 -->
            <div class="data-results mt30" v-if="showResults">
              <div class="results-header">
                <h3><i class="fas fa-table"></i> 工艺数据查询结果</h3>
                <div class="results-info">
                  <span>共找到 {{ processResults.length }} 条记录</span>
                  <button class="btn-export" @click="exportData">
                    <i class="fas fa-download"></i> 导出数据
                  </button>
                </div>
              </div>

              <div class="results-table">
                <table>
                  <thead>
                  <tr>
                    <th>工艺类型</th>
                    <th>参数名称</th>
                    <th>参数值</th>
                    <th>单位</th>
                    <th>时间</th>
                    <th>设备编号</th>
                    <th>操作员</th>
                    <th>操作</th>
                  </tr>
                  </thead>
                  <tbody>
                  <tr v-for="(item, index) in paginatedResults" :key="index">
                    <td>{{ item.processType }}</td>
                    <td>{{ item.parameterName }}</td>
                    <td class="value-cell">{{ item.value }}</td>
                    <td>{{ item.unit }}</td>
                    <td>{{ item.timestamp }}</td>
                    <td>{{ item.equipmentId }}</td>
                    <td>{{ item.operator }}</td>
                    <td>
                      <button class="btn-detail" @click="viewProcessDetail(item)">
                        <i class="fas fa-info-circle"></i> 详情
                      </button>
                    </td>
                  </tr>
                  </tbody>
                </table>

                <!-- 分页 -->
                <div class="pagination" v-if="processResults.length > pageSize">
                  <button class="page-btn" :disabled="currentPage === 1" @click="currentPage--">
                    <i class="fas fa-chevron-left"></i> 上一页
                  </button>
                  <span class="page-info">第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
                  <button class="page-btn" :disabled="currentPage === totalPages" @click="currentPage++">
                    下一页 <i class="fas fa-chevron-right"></i>
                  </button>
                </div>
              </div>
            </div>

            <!-- 工艺参数分类 -->
            <div class="fluid-categories mt30">
              <div class="section-header">
                <h3><i class="fas fa-layer-group"></i> 工艺参数分类</h3>
                <p>不同工艺环节的关键参数监控</p>
              </div>

              <div class="categories-grid">
                <div class="category-card" v-for="category in processCategories" :key="category.id">
                  <div class="category-icon" :style="{backgroundColor: category.color}">
                    <i :class="category.icon"></i>
                  </div>
                  <div class="category-content">
                    <h4>{{ category.name }}</h4>
                    <p>{{ category.description }}</p>
                    <div class="category-stats">
                      <div class="stat">
                        <span class="stat-label">监控点</span>
                        <span class="stat-value">{{ category.monitorPoints }}</span>
                      </div>
                      <div class="stat">
                        <span class="stat-label">采样频率</span>
                        <span class="stat-value">{{ category.samplingRate }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 工艺优化模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'optimization'">
            <div class="module-header">
              <h2><i class="fas fa-chart-line"></i> 工艺优化</h2>
              <p class="module-desc">基于数据分析的工艺参数优化与改进建议</p>
            </div>

            <!-- 优化案例 -->
            <div class="simulation-cases">
              <div class="section-header">
                <h3><i class="fas fa-lightbulb"></i> 优化案例</h3>
                <p>工艺参数优化典型成功案例</p>
              </div>

              <div class="cases-grid">
                <div class="case-card" v-for="caseItem in optimizationCases" :key="caseItem.id">
                  <div class="case-visual">
                    <div class="process-visualization" :style="{backgroundColor: caseItem.bgColor}">
                      <!-- 工艺流程图 -->
                      <div class="process-flow">
                        <div class="flow-step" v-for="step in caseItem.steps" :key="step.id">
                          <div class="step-icon">
                            <i :class="step.icon"></i>
                          </div>
                          <div class="step-label">{{ step.label }}</div>
                          <div class="step-value">{{ step.value }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="case-content">
                    <div class="case-header">
                      <h4>{{ caseItem.title }}</h4>
                      <span class="case-tag" :style="{backgroundColor: caseItem.tagColor}">
                        {{ caseItem.type }}
                      </span>
                    </div>
                    <p>{{ caseItem.description }}</p>
                    <div class="case-meta">
                      <div class="meta-item">
                        <i class="fas fa-percentage"></i>
                        <span>改善率：{{ caseItem.improvementRate }}</span>
                      </div>
                      <div class="meta-item">
                        <i class="fas fa-calendar"></i>
                        <span>实施时间：{{ caseItem.implementationDate }}</span>
                      </div>
                    </div>
                    <div class="case-actions">
                      <button class="btn-detail" @click="viewOptimizationDetail(caseItem)">
                        <i class="fas fa-chart-bar"></i> 查看分析
                      </button>
                      <button class="btn-case" @click="applyOptimization(caseItem)">
                        <i class="fas fa-play-circle"></i> 应用优化
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 优化建议 -->
            <div class="simulation-params mt30">
              <div class="section-header">
                <h3><i class="fas fa-bullhorn"></i> 优化建议生成</h3>
                <p>基于当前工艺数据的优化建议</p>
              </div>

              <div class="params-form">
                <div class="params-row">
                  <div class="param-group">
                    <label><i class="fas fa-cogs"></i> 选择工艺</label>
                    <select v-model="optimizationParams.process">
                      <option value="blast-furnace">高炉炼铁</option>
                      <option value="converter">转炉炼钢</option>
                      <option value="casting">连铸</option>
                      <option value="rolling">轧制</option>
                    </select>
                  </div>

                  <div class="param-group">
                    <label><i class="fas fa-crosshairs"></i> 优化目标</label>
                    <select v-model="optimizationParams.target">
                      <option value="energy">能耗降低</option>
                      <option value="quality">质量提升</option>
                      <option value="efficiency">效率提高</option>
                      <option value="cost">成本降低</option>
                    </select>
                  </div>
                </div>

                <div class="params-row">
                  <div class="param-group">
                    <label><i class="fas fa-calendar"></i> 数据周期</label>
                    <select v-model="optimizationParams.period">
                      <option value="week">最近一周</option>
                      <option value="month">最近一月</option>
                      <option value="quarter">最近一季度</option>
                      <option value="year">最近一年</option>
                    </select>
                  </div>

                  <div class="param-group">
                    <label><i class="fas fa-sliders-h"></i> 关键参数</label>
                    <input type="text" v-model="optimizationParams.keyParameters" placeholder="输入关键参数，用逗号分隔">
                  </div>
                </div>

                <div class="params-actions">
                  <button class="btn-run" @click="generateOptimization">
                    <i class="fas fa-magic"></i> 生成优化建议
                  </button>
                  <button class="btn-save" @click="saveOptimizationConfig">
                    <i class="fas fa-save"></i> 保存配置
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 能效分析模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'energy'">
            <div class="module-header">
              <h2><i class="fas fa-bolt"></i> 能效分析</h2>
              <p class="module-desc">冶金生产过程能耗监控与分析</p>
            </div>

            <!-- 能效指标 -->
            <div class="experiment-equipment">
              <div class="section-header">
                <h3><i class="fas fa-tachometer-alt"></i> 能效指标</h3>
                <p>关键能耗指标监控与分析</p>
              </div>

              <div class="equipment-grid">
                <div class="equipment-card" v-for="metric in energyMetrics" :key="metric.id">
                  <div class="equipment-icon">
                    <i :class="metric.icon"></i>
                  </div>
                  <div class="equipment-content">
                    <h4>{{ metric.name }}</h4>
                    <p>{{ metric.description }}</p>
                    <div class="equipment-specs">
                      <div class="spec">
                        <i class="fas fa-ruler"></i>
                        <span>当前值：{{ metric.currentValue }}</span>
                      </div>
                      <div class="spec">
                        <i class="fas fa-chart-line"></i>
                        <span>趋势：{{ metric.trend }}</span>
                      </div>
                    </div>
                    <div class="equipment-tags">
                      <span class="tag" v-for="tag in metric.tags" :key="tag">{{ tag }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 能耗分析 -->
            <div class="experiment-data mt30">
              <div class="section-header">
                <h3><i class="fas fa-chart-pie"></i> 能耗分析</h3>
                <div class="data-controls">
                  <select v-model="energyTimeRange">
                    <option value="day">日统计</option>
                    <option value="week">周统计</option>
                    <option value="month">月统计</option>
                    <option value="year">年统计</option>
                  </select>
                  <select v-model="energyProcessType">
                    <option value="all">全部工艺</option>
                    <option value="ironmaking">炼铁</option>
                    <option value="steelmaking">炼钢</option>
                    <option value="casting">连铸</option>
                    <option value="rolling">轧制</option>
                  </select>
                </div>
              </div>

              <div class="data-grid">
                <div class="data-card" v-for="data in energyAnalysisData" :key="data.id">
                  <div class="data-header">
                    <h4>{{ data.title }}</h4>
                    <span class="data-type" :style="{backgroundColor: data.typeColor}">
                      {{ data.type }}
                    </span>
                  </div>
                  <div class="data-content">
                    <div class="data-meta">
                      <div class="meta-item">
                        <i class="fas fa-calendar"></i>
                        <span>时间：{{ data.timeRange }}</span>
                      </div>
                      <div class="meta-item">
                        <i class="fas fa-bolt"></i>
                        <span>总能耗：{{ data.totalEnergy }}</span>
                      </div>
                    </div>
                    <p>{{ data.description }}</p>
                    <div class="data-stats">
                      <div class="stat">
                        <div class="stat-label">单位能耗</div>
                        <div class="stat-value">{{ data.unitEnergy }}</div>
                      </div>
                      <div class="stat">
                        <div class="stat-label">同比变化</div>
                        <div class="stat-value">{{ data.yearChange }}</div>
                      </div>
                      <div class="stat">
                        <div class="stat-label">环比变化</div>
                        <div class="stat-value">{{ data.monthChange }}</div>
                      </div>
                    </div>
                  </div>
                  <div class="data-footer">
                    <button class="btn-detail" @click="viewEnergyAnalysis(data)">
                      <i class="fas fa-chart-line"></i> 详细分析
                    </button>
                    <button class="btn-download" @click="downloadEnergyReport(data)">
                      <i class="fas fa-download"></i> 下载报告
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 质量分析模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'quality'">
            <div class="module-header">
              <h2><i class="fas fa-clipboard-check"></i> 质量分析</h2>
              <p class="module-desc">冶金产品质量指标监控与分析</p>
            </div>

            <!-- 质量指标 -->
            <div class="experiment-equipment">
              <div class="section-header">
                <h3><i class="fas fa-chart-bar"></i> 质量指标</h3>
                <p>产品质量关键性能指标</p>
              </div>

              <div class="equipment-grid">
                <div class="equipment-card" v-for="metric in qualityMetrics" :key="metric.id">
                  <div class="equipment-icon">
                    <i :class="metric.icon"></i>
                  </div>
                  <div class="equipment-content">
                    <h4>{{ metric.name }}</h4>
                    <p>{{ metric.description }}</p>
                    <div class="equipment-specs">
                      <div class="spec">
                        <i class="fas fa-percentage"></i>
                        <span>合格率：{{ metric.passRate }}</span>
                      </div>
                      <div class="spec">
                        <i class="fas fa-chart-line"></i>
                        <span>趋势：{{ metric.trend }}</span>
                      </div>
                    </div>
                    <div class="equipment-tags">
                      <span class="tag" v-for="tag in metric.tags" :key="tag">{{ tag }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 质量趋势分析 -->
            <div class="experiment-data mt30">
              <div class="section-header">
                <h3><i class="fas fa-trend-up"></i> 质量趋势分析</h3>
                <div class="data-controls">
                  <select v-model="qualityProductType">
                    <option value="all">全部产品</option>
                    <option value="plate">板材</option>
                    <option value="coil">卷材</option>
                    <option value="pipe">管材</option>
                    <option value="bar">棒材</option>
                  </select>
                  <select v-model="qualityTimeRange">
                    <option value="week">最近一周</option>
                    <option value="month">最近一月</option>
                    <option value="quarter">最近一季度</option>
                  </select>
                </div>
              </div>

              <div class="data-grid">
                <div class="data-card" v-for="data in qualityAnalysisData" :key="data.id">
                  <div class="data-header">
                    <h4>{{ data.title }}</h4>
                    <span class="data-type" :style="{backgroundColor: data.typeColor}">
                      {{ data.type }}
                    </span>
                  </div>
                  <div class="data-content">
                    <div class="data-meta">
                      <div class="meta-item">
                        <i class="fas fa-box"></i>
                        <span>产品：{{ data.product }}</span>
                      </div>
                      <div class="meta-item">
                        <i class="fas fa-calendar"></i>
                        <span>批次：{{ data.batch }}</span>
                      </div>
                    </div>
                    <p>{{ data.description }}</p>
                    <div class="data-stats">
                      <div class="stat">
                        <div class="stat-label">合格率</div>
                        <div class="stat-value">{{ data.passRate }}</div>
                      </div>
                      <div class="stat">
                        <div class="stat-label">缺陷率</div>
                        <div class="stat-value">{{ data.defectRate }}</div>
                      </div>
                      <div class="stat">
                        <div class="stat-label">客户投诉</div>
                        <div class="stat-value">{{ data.complaint }}</div>
                      </div>
                    </div>
                  </div>
                  <div class="data-footer">
                    <button class="btn-detail" @click="viewQualityAnalysis(data)">
                      <i class="fas fa-chart-line"></i> 详细分析
                    </button>
                    <button class="btn-download" @click="downloadQualityReport(data)">
                      <i class="fas fa-download"></i> 质量报告
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 工艺报表模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'reports'">
            <div class="module-header">
              <h2><i class="fas fa-file-alt"></i> 工艺报表</h2>
              <p class="module-desc">工艺数据统计报表与生产报告</p>
            </div>

            <!-- 报表分类 -->
            <div class="case-categories">
              <div class="section-header">
                <h3><i class="fas fa-sitemap"></i> 报表分类</h3>
              </div>
              <div class="category-tabs">
                <div class="tab-item"
                     v-for="category in reportCategories"
                     :key="category.id"
                     :class="{active: activeReportCategory === category.id}"
                     @click="switchReportCategory(category.id)">
                  {{ category.name }}
                  <span class="tab-count">{{ category.count }}</span>
                </div>
              </div>
            </div>

            <!-- 报表列表 -->
            <div class="case-studies">
              <div class="case-grid">
                <div class="study-card" v-for="report in filteredReports" :key="report.id">
                  <div class="study-header">
                    <h4>{{ report.title }}</h4>
                    <div class="study-meta">
                      <span class="meta-item">
                        <i class="fas fa-calendar"></i> {{ report.date }}
                      </span>
                      <span class="meta-item">
                        <i class="fas fa-file-pdf"></i> {{ report.format }}
                      </span>
                    </div>
                  </div>
                  <div class="study-content">
                    <p>{{ report.description }}</p>
                    <div class="study-problem">
                      <div class="problem-title">报表内容：</div>
                      <div class="problem-list">
                        <div class="problem-item" v-for="item in report.content" :key="item">
                          <i class="fas fa-check-circle"></i> {{ item }}
                        </div>
                      </div>
                    </div>
                    <div class="study-solution">
                      <div class="solution-title">数据范围：</div>
                      <div class="solution-tags">
                        <span class="solution-tag" v-for="range in report.dataRanges" :key="range">
                          {{ range }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="study-results">
                    <div class="result-item">
                      <div class="result-label">数据量</div>
                      <div class="result-value">{{ report.dataVolume }}</div>
                    </div>
                    <div class="result-item">
                      <div class="result-label">图表数量</div>
                      <div class="result-value">{{ report.chartCount }}</div>
                    </div>
                    <div class="result-item">
                      <div class="result-label">生成时间</div>
                      <div class="result-value">{{ report.generationTime }}</div>
                    </div>
                  </div>
                  <div class="study-footer">
                    <button class="btn-detail" @click="viewReport(report)">
                      <i class="fas fa-eye"></i> 预览报表
                    </button>
                    <button class="btn-report" @click="downloadReport(report)">
                      <i class="fas fa-download"></i> 下载报表
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <Footer></Footer>
</template>

<script>
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

export default {
  name: "ProcessData",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      activeModule: 'overview',
      searchParams: {
        processType: '',
        parameterType: '',
        dateStart: '',
        dateEnd: ''
      },
      showResults: false,
      processResults: [],
      currentPage: 1,
      pageSize: 10,

      // 工艺分类数据
      processCategories: [
        {
          id: 'temperature',
          name: '温度参数',
          icon: 'fas fa-thermometer-half',
          color: '#0046DB',
          description: '各工艺环节温度监控参数',
          monitorPoints: '350+',
          samplingRate: '1秒/次'
        },
        {
          id: 'pressure',
          name: '压力参数',
          icon: 'fas fa-compress-alt',
          color: '#FF6B6B',
          description: '设备压力与流量控制参数',
          monitorPoints: '280+',
          samplingRate: '5秒/次'
        },
        {
          id: 'composition',
          name: '成分参数',
          icon: 'fas fa-flask',
          color: '#4ECDC4',
          description: '原料与产品化学成分',
          monitorPoints: '120+',
          samplingRate: '10分钟/次'
        },
        {
          id: 'equipment',
          name: '设备参数',
          icon: 'fas fa-cogs',
          color: '#96CEB4',
          description: '设备运行状态与工艺参数',
          monitorPoints: '450+',
          samplingRate: '1秒/次'
        }
      ],

      // 优化案例数据 - 更新为工艺流程图
      optimizationCases: [
        {
          id: 1,
          title: '高炉热风温度优化',
          type: '能耗优化',
          bgColor: '#0046DB',
          tagColor: '#0046DB',
          description: '通过优化热风炉操作，提高热风温度稳定性，降低焦炭消耗',
          improvementRate: '8.5%',
          implementationDate: '2024-03',
          steps: [
            { id: 1, icon: 'fas fa-fire', label: '原温度', value: '1180°C' },
            { id: 2, icon: 'fas fa-arrow-right', label: '优化', value: '→' },
            { id: 3, icon: 'fas fa-thermometer-full', label: '新温度', value: '1250°C' },
            { id: 4, icon: 'fas fa-chart-line', label: '改善', value: '+8.5%' }
          ]
        },
        {
          id: 2,
          title: '转炉终点碳控制优化',
          type: '质量提升',
          bgColor: '#FF6B6B',
          tagColor: '#FF6B6B',
          description: '优化吹炼控制模型，提高终点碳命中率，减少补吹次数',
          improvementRate: '12.3%',
          implementationDate: '2024-02',
          steps: [
            { id: 1, icon: 'fas fa-balance-scale', label: '原命中率', value: '85.2%' },
            { id: 2, icon: 'fas fa-arrow-right', label: '优化', value: '→' },
            { id: 3, icon: 'fas fa-bullseye', label: '新命中率', value: '97.5%' },
            { id: 4, icon: 'fas fa-chart-line', label: '提升', value: '+12.3%' }
          ]
        },
        {
          id: 3,
          title: '连铸拉速稳定性优化',
          type: '效率提升',
          bgColor: '#4ECDC4',
          tagColor: '#4ECDC4',
          description: '优化拉速控制系统，提高连铸过程稳定性',
          improvementRate: '6.8%',
          implementationDate: '2024-01',
          steps: [
            { id: 1, icon: 'fas fa-tachometer-alt', label: '原波动', value: '±0.15' },
            { id: 2, icon: 'fas fa-arrow-right', label: '优化', value: '→' },
            { id: 3, icon: 'fas fa-sliders-h', label: '新波动', value: '±0.05' },
            { id: 4, icon: 'fas fa-chart-line', label: '改善', value: '+6.8%' }
          ]
        },
        {
          id: 4,
          title: '轧制力控制优化',
          type: '成本降低',
          bgColor: '#96CEB4',
          tagColor: '#96CEB4',
          description: '优化轧制力控制策略，减少设备磨损和能源消耗',
          improvementRate: '5.2%',
          implementationDate: '2023-12',
          steps: [
            { id: 1, icon: 'fas fa-compress-alt', label: '原能耗', value: '420kWh/t' },
            { id: 2, icon: 'fas fa-arrow-right', label: '优化', value: '→' },
            { id: 3, icon: 'fas fa-bolt', label: '新能耗', value: '398kWh/t' },
            { id: 4, icon: 'fas fa-chart-line', label: '降低', value: '-5.2%' }
          ]
        }
      ],

      optimizationParams: {
        process: 'blast-furnace',
        target: 'energy',
        period: 'month',
        keyParameters: ''
      },

      // 能效指标数据
      energyMetrics: [
        {
          id: 1,
          name: '综合能耗',
          icon: 'fas fa-bolt',
          description: '吨钢综合能耗指标',
          currentValue: '580 kgce/t',
          trend: '下降2.3%',
          tags: ['关键指标', '持续监控', '月度考核']
        },
        {
          id: 2,
          name: '电耗',
          icon: 'fas fa-plug',
          description: '吨钢电耗',
          currentValue: '420 kWh/t',
          trend: '下降1.8%',
          tags: ['主要能耗', '成本控制', '实时监控']
        },
        {
          id: 3,
          name: '燃气消耗',
          icon: 'fas fa-fire',
          description: '吨钢燃气消耗',
          currentValue: '85 Nm³/t',
          trend: '下降3.1%',
          tags: ['燃料成本', '燃烧效率', '优化重点']
        },
        {
          id: 4,
          name: '氧气消耗',
          icon: 'fas fa-wind',
          description: '吨钢氧气消耗',
          currentValue: '62 Nm³/t',
          trend: '稳定',
          tags: ['炼钢关键', '工艺优化', '精细控制']
        }
      ],

      energyTimeRange: 'month',
      energyProcessType: 'all',

      // 质量指标数据
      qualityMetrics: [
        {
          id: 1,
          name: '表面质量',
          icon: 'fas fa-eye',
          description: '产品表面缺陷率',
          passRate: '98.5%',
          trend: '提升0.5%',
          tags: ['外观质量', '客户关注', '在线检测']
        },
        {
          id: 2,
          name: '尺寸精度',
          icon: 'fas fa-ruler',
          description: '产品尺寸合格率',
          passRate: '99.2%',
          trend: '稳定',
          tags: ['精度控制', '工艺保证', '自动测量']
        },
        {
          id: 3,
          name: '力学性能',
          icon: 'fas fa-weight',
          description: '力学性能合格率',
          passRate: '99.6%',
          trend: '提升0.3%',
          tags: ['强度要求', '韧性指标', '客户验收']
        },
        {
          id: 4,
          name: '化学成分',
          icon: 'fas fa-atom',
          description: '化学成分合格率',
          passRate: '99.8%',
          trend: '稳定',
          tags: ['成分控制', '精准冶炼', '标准符合']
        }
      ],

      qualityProductType: 'all',
      qualityTimeRange: 'month',

      // 报表分类
      activeReportCategory: 'all',
      reportCategories: [
        { id: 'all', name: '全部报表', count: 65 },
        { id: 'daily', name: '日报表', count: 30 },
        { id: 'weekly', name: '周报表', count: 15 },
        { id: 'monthly', name: '月报表', count: 12 },
        { id: 'special', name: '专项报告', count: 8 }
      ]
    };
  },
  computed: {
    totalPages() {
      return Math.ceil(this.processResults.length / this.pageSize);
    },
    paginatedResults() {
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return this.processResults.slice(start, end);
    },

    filteredEnergyAnalysisData() {
      // 模拟数据过滤
      return [
        {
          id: 1,
          title: '炼铁工序能耗分析',
          type: '能耗分析',
          typeColor: '#0046DB',
          timeRange: '2024年3月',
          totalEnergy: '12,500 tce',
          description: '高炉炼铁工序能耗详细分析报告，包含焦炭、煤粉、燃气等各项能耗',
          unitEnergy: '380 kgce/t',
          yearChange: '-3.2%',
          monthChange: '-1.5%'
        },
        {
          id: 2,
          title: '炼钢工序能耗分析',
          type: '能耗分析',
          typeColor: '#FF6B6B',
          timeRange: '2024年3月',
          totalEnergy: '8,300 tce',
          description: '转炉炼钢工序能耗分析，重点分析氧气、电力、燃气消耗',
          unitEnergy: '28 kgce/t',
          yearChange: '-2.8%',
          monthChange: '-1.2%'
        },
        {
          id: 3,
          title: '轧制工序能耗分析',
          type: '能耗分析',
          typeColor: '#4ECDC4',
          timeRange: '2024年3月',
          totalEnergy: '5,200 tce',
          description: '热轧、冷轧工序能耗分析，包含电力、燃料、水等消耗',
          unitEnergy: '42 kWh/t',
          yearChange: '-4.1%',
          monthChange: '-2.3%'
        },
        {
          id: 4,
          title: '全厂能源平衡分析',
          type: '综合能耗',
          typeColor: '#96CEB4',
          timeRange: '2024年第一季度',
          totalEnergy: '36,500 tce',
          description: '全厂能源平衡与优化潜力分析报告',
          unitEnergy: '590 kgce/t',
          yearChange: '-2.7%',
          monthChange: '-1.8%'
        }
      ];
    },

    filteredQualityAnalysisData() {
      return [
        {
          id: 1,
          title: '热轧板材质量分析',
          type: '质量分析',
          typeColor: '#0046DB',
          product: 'Q235B板材',
          batch: '2024031501',
          description: '热轧板材表面质量与尺寸精度分析，包含板形、厚度、宽度等指标',
          passRate: '98.7%',
          defectRate: '1.3%',
          complaint: '0.2%'
        },
        {
          id: 2,
          title: '冷轧卷材质量分析',
          type: '质量分析',
          typeColor: '#FF6B6B',
          product: 'SPCC卷材',
          batch: '2024031202',
          description: '冷轧卷材表面质量与力学性能分析，包含表面光洁度、力学性能等',
          passRate: '99.1%',
          defectRate: '0.9%',
          complaint: '0.1%'
        },
        {
          id: 3,
          title: '中厚板质量分析',
          type: '质量分析',
          typeColor: '#4ECDC4',
          product: 'Q345B中板',
          batch: '2024031803',
          description: '中厚板超声波探伤与力学性能综合分析',
          passRate: '99.5%',
          defectRate: '0.5%',
          complaint: '0.05%'
        },
        {
          id: 4,
          title: '型钢质量分析',
          type: '质量分析',
          typeColor: '#96CEB4',
          product: 'H型钢',
          batch: '2024032204',
          description: '型钢尺寸精度与弯曲度质量控制分析',
          passRate: '98.9%',
          defectRate: '1.1%',
          complaint: '0.15%'
        }
      ];
    },

    filteredReports() {
      return [
        {
          id: 1,
          title: '3月份生产运行报告',
          date: '2024-03-31',
          format: 'PDF',
          description: '2024年3月份全厂生产运行综合报告，包含产量、质量、能耗等全方位数据分析',
          content: [
            '生产计划完成情况',
            '设备运行状况分析',
            '质量指标统计分析',
            '能耗综合统计分析',
            '成本控制分析'
          ],
          dataRanges: ['炼铁工序', '炼钢工序', '连铸工序', '轧制工序'],
          dataVolume: '15.2 GB',
          chartCount: 24,
          generationTime: '5分钟'
        },
        {
          id: 2,
          title: '高炉运行周报',
          date: '2024-03-25',
          format: 'Excel',
          description: '高炉运行参数与经济技术指标周报，包含操作参数、技术指标、异常分析',
          content: [
            '高炉运行参数统计',
            '技术经济指标分析',
            '能耗与成本分析',
            '设备故障统计',
            '下周运行建议'
          ],
          dataRanges: ['1#高炉', '2#高炉', '3#高炉'],
          dataVolume: '2.8 GB',
          chartCount: 12,
          generationTime: '2分钟'
        },
        {
          id: 3,
          title: '产品质量月报',
          date: '2024-03-28',
          format: 'PDF',
          description: '月度产品质量综合报告，涵盖各类产品的质量指标和问题分析',
          content: [
            '产品合格率统计',
            '主要质量问题分析',
            '客户投诉处理',
            '质量改进措施',
            '下月质量目标'
          ],
          dataRanges: ['板材', '卷材', '管材', '型材'],
          dataVolume: '8.5 GB',
          chartCount: 18,
          generationTime: '3分钟'
        },
        {
          id: 4,
          title: '能效分析季报',
          date: '2024-03-30',
          format: 'Excel',
          description: '第一季度能效分析报告，包含能耗统计、效率分析、节能潜力评估',
          content: [
            '综合能耗分析',
            '各工序能耗对比',
            '节能项目实施',
            '能效改进建议',
            '下季度能耗目标'
          ],
          dataRanges: ['全厂范围', '各生产单元', '重点耗能设备'],
          dataVolume: '12.3 GB',
          chartCount: 16,
          generationTime: '4分钟'
        }
      ];
    }
  },
  methods: {
    switchModule(module) {
      this.activeModule = module;
      if (module === 'database') {
        this.searchProcessData();
      }
    },

    searchProcessData() {
      this.showResults = true;
      this.currentPage = 1;

      // 模拟数据
      this.processResults = [
        {
          processType: '高炉炼铁',
          parameterName: '热风温度',
          value: '1250',
          unit: '°C',
          timestamp: '2024-03-20 10:30:25',
          equipmentId: 'BF-01',
          operator: '张三'
        },
        {
          processType: '转炉炼钢',
          parameterName: '终点碳含量',
          value: '0.045',
          unit: '%',
          timestamp: '2024-03-20 11:15:42',
          equipmentId: 'BOF-02',
          operator: '李四'
        },
        {
          processType: '连铸',
          parameterName: '拉坯速度',
          value: '1.2',
          unit: 'm/min',
          timestamp: '2024-03-20 12:05:18',
          equipmentId: 'CC-03',
          operator: '王五'
        },
        {
          processType: '轧制',
          parameterName: '轧制力',
          value: '12500',
          unit: 'kN',
          timestamp: '2024-03-20 13:20:35',
          equipmentId: 'RM-04',
          operator: '赵六'
        },
        {
          processType: '高炉炼铁',
          parameterName: '顶压',
          value: '220',
          unit: 'kPa',
          timestamp: '2024-03-20 14:10:18',
          equipmentId: 'BF-01',
          operator: '张三'
        },
        {
          processType: '转炉炼钢',
          parameterName: '终点温度',
          value: '1650',
          unit: '°C',
          timestamp: '2024-03-20 15:45:32',
          equipmentId: 'BOF-02',
          operator: '李四'
        },
        {
          processType: '连铸',
          parameterName: '结晶器水温差',
          value: '5.8',
          unit: '°C',
          timestamp: '2024-03-20 16:30:15',
          equipmentId: 'CC-03',
          operator: '王五'
        },
        {
          processType: '轧制',
          parameterName: '终轧温度',
          value: '860',
          unit: '°C',
          timestamp: '2024-03-20 17:15:28',
          equipmentId: 'RM-04',
          operator: '赵六'
        },
        {
          processType: '热处理',
          parameterName: '退火温度',
          value: '720',
          unit: '°C',
          timestamp: '2024-03-20 18:05:42',
          equipmentId: 'HT-05',
          operator: '孙七'
        },
        {
          processType: '热处理',
          parameterName: '保温时间',
          value: '120',
          unit: 'min',
          timestamp: '2024-03-20 18:50:37',
          equipmentId: 'HT-05',
          operator: '孙七'
        }
      ];
    },

    resetSearch() {
      this.searchParams = {
        processType: '',
        parameterType: '',
        dateStart: '',
        dateEnd: ''
      };
      this.showResults = false;
      this.processResults = [];
      this.currentPage = 1;
    },

    exportData() {
      alert('工艺数据导出功能开发中...');
    },

    viewProcessDetail(item) {
      alert(`工艺数据详情：
      工艺类型：${item.processType}
      参数名称：${item.parameterName}
      参数值：${item.value} ${item.unit}
      时间：${item.timestamp}
      设备编号：${item.equipmentId}
      操作员：${item.operator}`);
    },

    viewOptimizationDetail(caseItem) {
      alert(`查看优化分析：${caseItem.title}
      正在加载详细分析报告...`);
    },

    applyOptimization(caseItem) {
      alert(`应用优化方案：${caseItem.title}
      正在应用优化参数...`);
    },

    generateOptimization() {
      alert(`生成优化建议：
      工艺：${this.optimizationParams.process}
      目标：${this.optimizationParams.target}
      周期：${this.optimizationParams.period}
      关键参数：${this.optimizationParams.keyParameters}
      正在分析数据并生成建议...`);
    },

    saveOptimizationConfig() {
      alert('优化配置已保存');
    },

    viewEnergyAnalysis(data) {
      alert(`查看能效分析：${data.title}
      正在生成详细分析图表...`);
    },

    downloadEnergyReport(data) {
      alert(`下载能效报告：${data.title}
      文件正在下载中...`);
    },

    viewQualityAnalysis(data) {
      alert(`查看质量分析：${data.title}
      正在生成质量分析报告...`);
    },

    downloadQualityReport(data) {
      alert(`下载质量报告：${data.title}
      PDF文件正在生成...`);
    },

    switchReportCategory(category) {
      this.activeReportCategory = category;
    },

    viewReport(report) {
      alert(`预览报表：${report.title}
      正在加载报表预览...`);
    },

    downloadReport(report) {
      alert(`下载报表：${report.title}
      ${report.format}文件正在下载...`);
    }
  },
  mounted() {
    // 移动端菜单切换
    const menuBtn = document.querySelector('.m-nav-but');
    const leftNav = document.querySelector('.data-aggregation-left');

    if (menuBtn && leftNav) {
      menuBtn.addEventListener('click', function() {
        const leftP = getComputedStyle(leftNav).left;
        if (leftP === '0px') {
          leftNav.style.left = '-220px';
          this.textContent = '点击展开菜单';
        } else {
          leftNav.style.left = '0px';
          this.textContent = '点击隐藏菜单';
        }
      });
    }
  }
};
</script>

<style scoped>
/* ==================== 基础样式 ==================== */
.process-data {
  background-color: #f5f7fa;
  min-height: 120vh;
  font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
  display: flex;
  flex-direction: column;
  padding-top: 80px;
}

.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}

.main-content {
  padding: 40px 0 30px;
  flex: 1;
}

/* ==================== 网格布局 ==================== */
.data-aggregation {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 24px;
  align-items: stretch;
}

/* ==================== 左侧导航栏 ==================== */
.data-aggregation-left {
  grid-column: 1;
  position: relative;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: auto;
  min-height: 0;
}

.left-sub-nav-box {
  width: 100%;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  background: #fff;
  min-height: 200px;
}

.data-aggregation-nav {
  width: 100%;
  border-radius: 0;
  overflow: hidden;
  margin-bottom: 0;
  transition: all 0.3s;
  border-bottom: 1px solid #f0f0f0;
}

.data-aggregation-nav:last-child {
  border-bottom: none;
}

.data-aggregation-nav dt {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 56px;
  font-size: 16px;
  color: #333;
  background-color: #fff;
  padding-left: 20px;
  cursor: pointer;
  position: relative;
  transition: all 0.3s;
  border-left: 3px solid transparent;
}

.data-aggregation-nav dt:hover {
  background-color: #f8f9fa;
  color: #0046DB;
}

.data-aggregation-nav dt.active {
  background-color: #f0f7ff;
  color: #0046DB;
  border-left-color: #0046DB;
  font-weight: 600;
}

.data-aggregation-nav dt::before {
  content: '';
  position: absolute;
  left: 20px;
  width: 16px;
  height: 16px;
  background-color: #666;
  mask-size: contain;
  mask-repeat: no-repeat;
  mask-position: center;
  transition: all 0.3s;
}

.data-aggregation-nav dt:hover::before,
.data-aggregation-nav dt.active::before {
  background-color: #0046DB;
}

/* 导航图标 */
.data-aggregation-nav dt.index1::before {
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2L4 5v6.09c0 5.05 3.41 9.76 8 10.91 4.59-1.15 8-5.86 8-10.91V5l-8-3zm0 2l6 1.83-6 1.82-6-1.82L12 4zm0 7c1.65 0 3 1.35 3 3s-1.35 3-3 3-3-1.35-3-3 1.35-3 3-3z'/%3E%3C/svg%3E");
}

.data-aggregation-nav dt.index2::before {
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9 14l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z'/%3E%3C/svg%3E");
}

.data-aggregation-nav dt.index3::before {
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 2.5c1.93 0 3.5 1.57 3.5 3.5s-1.57 3.5-3.5 3.5S8.5 9.93 8.5 8s1.57-3.5 3.5-3.5z'/%3E%3C/svg%3E");
}

.data-aggregation-nav dt.index4::before {
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M11 18h2v-2h-2v2zm1-16C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-2.21 0-4 1.79-4 4h2c0-1.1.9-2 2-2s2 .9 2 2c0 2-3 1.75-3 5h2c0-2.25 3-2.5 3-5 0-2.21-1.79-4-4-4z'/%3E%3C/svg%3E");
}

.data-aggregation-nav dt.index5::before {
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z'/%3E%3C/svg%3E");
}

.data-aggregation-nav dt.index6::before {
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z'/%3E%3C/svg%3E");
}

.data-aggregation-nav dt a {
  color: inherit;
  text-decoration: none;
  flex: 1;
  padding-left: 24px;
  display: flex;
  align-items: center;
  height: 100%;
}

.m-nav-but {
  display: none;
  position: absolute;
  top: 10px;
  right: -40px;
  width: 30px;
  height: 30px;
  background-color: #0046DB;
  color: #fff;
  font-size: 12px;
  text-align: center;
  line-height: 30px;
  cursor: pointer;
  border-radius: 4px;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 70, 219, 0.3);
}

/* ==================== 右侧内容区域 ==================== */
.data-aggregation-right {
  grid-column: 2;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.module-content {
  background: #fff;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  min-height: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid transparent;
  transition: all 0.3s;
}

.module-content:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border-color: #f0f0f0;
}

.module-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e8e8e8;
}

.module-header h2 {
  font-size: 22px;
  color: #333;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.module-header h2 i {
  color: #0046DB;
  font-size: 20px;
}

.module-desc {
  font-size: 14px;
  color: #666;
  margin: 0;
  line-height: 1.5;
}

/* ==================== 数据卡片 ==================== */
.echarts-data-num {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.data-item {
  display: flex;
  justify-content: space-between;
  padding: 18px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
  border: 1px solid #f0f0f0;
}

.data-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.data-item dl {
  flex: 1;
}

.data-item dt {
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
  font-weight: 500;
}

.data-item dd {
  font-size: 20px;
  font-weight: 700;
  color: #0046DB;
  margin: 0;
  line-height: 1.2;
}

.data-item .trend {
  font-size: 12px;
  font-weight: normal;
  margin-top: 4px;
}

.data-item .trend.up {
  color: #f56c6c;
}

.data-item .trend.down {
  color: #67c23a;
}

.card-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0046DB;
}

/* ==================== 应用场景 ==================== */
.application-scenarios {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.scenarios-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.scenario-card {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 15px;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.scenario-card:hover {
  background: #e6f7ff;
  border-color: #0046DB;
  transform: translateY(-2px);
}

.scenario-icon {
  font-size: 28px;
  color: #0046DB;
  margin-bottom: 10px;
}

.scenario-content h4 {
  font-size: 15px;
  color: #333;
  margin: 0 0 6px 0;
}

.scenario-content p {
  font-size: 13px;
  color: #666;
  margin: 0 0 10px 0;
  line-height: 1.4;
}

.scenario-tags {
  display: flex;
  gap: 5px;
}

.tag {
  font-size: 10px;
  color: #0046DB;
  background: rgba(0, 70, 219, 0.1);
  padding: 2px 6px;
  border-radius: 10px;
}

/* ==================== 搜索区域 ==================== */
.search-section {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
  border: 1px solid #f0f0f0;
}

.section-header {
  margin-bottom: 15px;
}

.section-header h3 {
  font-size: 18px;
  color: #333;
  margin: 0 0 6px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-header h3 i {
  color: #0046DB;
}

.section-header p {
  color: #666;
  font-size: 13px;
  margin: 0;
}

.search-form {
  width: 100%;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 25px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  color: #666;
  margin-bottom: 8px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-group label i {
  color: #0046DB;
}

.form-group select,
.form-group input {
  padding: 12px 15px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  color: #333;
  font-size: 14px;
  transition: all 0.3s;
}

.form-group select:focus,
.form-group input:focus {
  outline: none;
  border-color: #0046DB;
  background: #fff;
}

.range-input {
  display: flex;
  align-items: center;
  gap: 10px;
}

.range-input input {
  flex: 1;
}

.range-input span {
  color: #666;
  font-size: 14px;
}

.form-actions {
  display: flex;
  gap: 15px;
}

.btn-search,
.btn-reset {
  padding: 12px 25px;
  border-radius: 30px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-search {
  background: #0046DB;
  color: #fff;
  border: 1px solid #0046DB;
}

.btn-search:hover {
  background: #003db9;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 70, 219, 0.3);
}

.btn-reset {
  background: transparent;
  color: #666;
  border: 1px solid #dcdfe6;
}

.btn-reset:hover {
  background: #f8f9fa;
  color: #333;
}

/* ==================== 数据结果表格 ==================== */
.data-results {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.results-header h3 {
  font-size: 18px;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.results-header h3 i {
  color: #0046DB;
}

.results-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.results-info span {
  color: #666;
  font-size: 14px;
}

.btn-export {
  padding: 8px 16px;
  background: rgba(0, 70, 219, 0.1);
  border: 1px solid rgba(0, 70, 219, 0.3);
  border-radius: 20px;
  color: #0046DB;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-export:hover {
  background: rgba(0, 70, 219, 0.2);
  color: #003db9;
}

.results-table {
  overflow-x: auto;
}

.results-table table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}

.results-table thead {
  background: #fafafa;
}

.results-table th {
  padding: 14px;
  text-align: left;
  color: #666;
  font-weight: 500;
  font-size: 13px;
  border-bottom: 1px solid #e8e8e8;
}

.results-table td {
  padding: 12px;
  color: #333;
  font-size: 13px;
  border-bottom: 1px solid #e8e8e8;
}

.results-table tbody tr:hover {
  background: #f8f9fa;
}

.value-cell {
  color: #0046DB;
  font-weight: 500;
}

.btn-detail {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 15px;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 5px;
}

.btn-detail:hover {
  background: rgba(0, 70, 219, 0.1);
  color: #0046DB;
  border-color: rgba(0, 70, 219, 0.3);
}

/* ==================== 优化案例 ==================== */
.simulation-cases {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.cases-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.case-card {
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
  border: 1px solid #f0f0f0;
}

.case-card:hover {
  background: #e6f7ff;
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.case-visual {
  width: 100%;
  height: 120px;
  overflow: hidden;
}

.process-visualization {
  width: 100%;
  height: 100%;
  position: relative;
  background: linear-gradient(135deg, rgba(0, 70, 219, 0.9) 0%, rgba(255, 107, 107, 0.9) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.process-flow {
  display: flex;
  align-items: center;
  justify-content: space-around;
  width: 90%;
  height: 80%;
  padding: 15px;
}

.flow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: white;
  text-align: center;
  flex: 1;
}

.step-icon {
  font-size: 20px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.2);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-label {
  font-size: 10px;
  margin-bottom: 3px;
  opacity: 0.9;
}

.step-value {
  font-size: 12px;
  font-weight: bold;
}

.case-content {
  padding: 15px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.case-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.case-header h4 {
  font-size: 16px;
  color: #333;
  margin: 0;
  flex: 1;
}

.case-tag {
  font-size: 10px;
  color: #fff;
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}

.case-card p {
  font-size: 13px;
  color: #666;
  margin: 0 0 12px 0;
  line-height: 1.4;
  flex: 1;
}

.case-meta {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #666;
}

.meta-item i {
  color: #0046DB;
}

.case-actions {
  display: flex;
  gap: 10px;
  margin-top: auto;
}

.btn-case {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 15px;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 5px;
  flex: 1;
  justify-content: center;
}

.btn-case:hover {
  background: rgba(0, 70, 219, 0.1);
  color: #0046DB;
  border-color: rgba(0, 70, 219, 0.3);
}

/* ==================== 优化参数设置 ==================== */
.simulation-params {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.params-form {
  width: 100%;
}

.params-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.param-group {
  display: flex;
  flex-direction: column;
}

.param-group label {
  color: #666;
  margin-bottom: 8px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.param-group label i {
  color: #0046DB;
}

.param-group select,
.param-group input[type="text"] {
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
}

.params-actions {
  display: flex;
  gap: 15px;
}

.btn-run,
.btn-save {
  padding: 12px 25px;
  border-radius: 30px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-run {
  background: #0046DB;
  color: #fff;
  border: 1px solid #0046DB;
}

.btn-run:hover {
  background: #003db9;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 70, 219, 0.3);
}

.btn-save {
  background: transparent;
  color: #666;
  border: 1px solid #dcdfe6;
}

.btn-save:hover {
  background: #f8f9fa;
  color: #333;
}

/* ==================== 流体分类 ==================== */
.fluid-categories {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.category-card {
  background: #fff;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
  border: 1px solid #f0f0f0;
}

.category-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.category-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
  color: white;
  font-size: 24px;
}

.category-content h4 {
  font-size: 16px;
  color: #333;
  margin: 0 0 8px 0;
}

.category-content p {
  font-size: 13px;
  color: #666;
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.category-stats {
  display: flex;
  gap: 15px;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 11px;
  color: #999;
  margin-bottom: 2px;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #0046DB;
}

/* ==================== 实验设备 ==================== */
.experiment-equipment {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.equipment-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.equipment-card {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 15px;
  transition: all 0.3s;
  border: 1px solid #f0f0f0;
}

.equipment-card:hover {
  background: #e6f7ff;
  transform: translateY(-2px);
  border-color: #0046DB;
}

.equipment-icon {
  font-size: 32px;
  color: #0046DB;
  margin-bottom: 10px;
}

.equipment-content h4 {
  font-size: 15px;
  color: #333;
  margin: 0 0 8px 0;
}

.equipment-content p {
  font-size: 13px;
  color: #666;
  margin: 0 0 10px 0;
  line-height: 1.4;
}

.equipment-specs {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.spec {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #666;
}

.spec i {
  color: #0046DB;
}

.equipment-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

/* ==================== 实验数据 ==================== */
.experiment-data {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.data-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.data-controls select {
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  background: #fff;
  cursor: pointer;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-top: 15px;
}

.data-card {
  background: #fff;
  border-radius: 6px;
  padding: 15px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.data-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.data-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.data-header h4 {
  font-size: 15px;
  color: #333;
  margin: 0;
  flex: 1;
}

.data-type {
  font-size: 10px;
  color: #fff;
  padding: 2px 6px;
  border-radius: 10px;
}

.data-meta {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}

.data-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin: 10px 0;
}

.stat-label {
  font-size: 11px;
  color: #999;
  margin-bottom: 2px;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #0046DB;
}

.data-footer {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.btn-download {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 15px;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 5px;
}

.btn-download:hover {
  background: rgba(0, 70, 219, 0.1);
  color: #0046DB;
  border-color: rgba(0, 70, 219, 0.3);
}

/* ==================== 案例分析 ==================== */
.case-categories {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 15px;
  border: 1px solid #f0f0f0;
}

.category-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 5px;
}

.tab-item {
  padding: 8px 15px;
  background: #f8f9fa;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s;
  white-space: nowrap;
}

.tab-item:hover,
.tab-item.active {
  background: #0046DB;
  color: #fff;
}

.tab-count {
  font-size: 11px;
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 5px;
  border-radius: 8px;
}

.case-studies {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.case-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.study-card {
  background: #fff;
  border-radius: 6px;
  padding: 15px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.study-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.study-header {
  margin-bottom: 10px;
}

.study-header h4 {
  font-size: 16px;
  color: #333;
  margin: 0 0 5px 0;
}

.study-meta {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #666;
}

.study-problem,
.study-solution {
  margin: 10px 0;
}

.problem-title,
.solution-title {
  font-size: 13px;
  color: #333;
  font-weight: 500;
  margin-bottom: 5px;
}

.problem-list {
  margin-left: 15px;
}

.problem-item {
  font-size: 12px;
  color: #666;
  margin-bottom: 3px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.problem-item i {
  color: #0046DB;
}

.solution-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.solution-tag {
  font-size: 10px;
  color: #0046DB;
  background: rgba(0, 70, 219, 0.1);
  padding: 2px 6px;
  border-radius: 10px;
}

.study-results {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin: 15px 0;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
}

.result-item {
  text-align: center;
}

.result-label {
  font-size: 11px;
  color: #666;
  margin-bottom: 2px;
}

.result-value {
  font-size: 18px;
  font-weight: 700;
  color: #0046DB;
}

.study-footer {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.btn-report {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 15px;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 5px;
}

.btn-report:hover {
  background: rgba(255, 107, 107, 0.1);
  color: #FF6B6B;
  border-color: rgba(255, 107, 107, 0.3);
}

/* ==================== 分页 ==================== */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e8e8e8;
}

.page-btn {
  padding: 8px 16px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 20px;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 5px;
}

.page-btn:hover:not(:disabled) {
  background: #f8f9fa;
  color: #333;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #666;
  font-size: 14px;
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 1200px) {
  .container {
    max-width: 960px;
  }

  .echarts-data-num {
    grid-template-columns: repeat(2, 1fr);
  }

  .scenarios-grid {
    grid-template-columns: 1fr;
  }

  .categories-grid {
    grid-template-columns: 1fr;
  }

  .data-grid {
    grid-template-columns: 1fr;
  }

  .equipment-grid {
    grid-template-columns: 1fr;
  }

  .cases-grid {
    grid-template-columns: 1fr;
  }

  .case-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 992px) {
  .data-aggregation {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto;
    gap: 15px;
  }

  .data-aggregation-left {
    grid-column: 1;
    grid-row: 1;
    width: 100%;
    height: auto;
    min-height: auto;
  }

  .data-aggregation-right {
    grid-column: 1;
    grid-row: 2;
    width: 100%;
    height: auto;
  }

  .m-nav-but {
    display: block;
  }

  .process-data {
    padding-top: 80px;
  }
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .params-row {
    grid-template-columns: 1fr;
  }

  .study-results {
    grid-template-columns: 1fr;
    gap: 15px;
  }

  .main-content {
    padding: 15px 0 25px;
  }

  .module-content {
    padding: 15px;
  }

  .echarts-data-num {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .module-header h2 {
    font-size: 18px;
  }

  .data-item {
    padding: 15px;
  }

  .data-item dd {
    font-size: 18px;
  }

  .cases-grid {
    grid-template-columns: 1fr;
  }

  .case-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 576px) {
  .container {
    padding: 0 10px;
  }

  .module-header h2 {
    font-size: 16px;
  }

  .data-item {
    padding: 12px;
  }

  .form-actions {
    flex-wrap: wrap;
  }

  .btn-search,
  .btn-reset {
    flex: 1;
    min-width: 120px;
  }

  .results-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .results-info {
    width: 100%;
    justify-content: space-between;
  }

  .case-actions {
    flex-direction: column;
  }

  .btn-case {
    width: 100%;
  }
}

/* 动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.module-content {
  animation: fadeIn 0.3s ease-out;
}

.data-item,
.scenario-card,
.category-card,
.case-card,
.equipment-card,
.data-card,
.study-card {
  animation: fadeIn 0.3s ease-out;
}

/* 工具类 */
.mt30 {
  margin-top: 30px;
}
</style>